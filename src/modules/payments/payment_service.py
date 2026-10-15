from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_service import BaseService
from src.core.exceptions import BadRequestException, NotFoundException
from src.config.midtrans import midtrans_client
from src.config.mailer import mailer
from src.config.whatsapp import whatsapp_client
from src.config.settings import settings
from src.modules.payments.payment_repository import PaymentRepository
from src.modules.orders.order_repository import OrderRepository
from src.modules.payments.payment_model import PaymentTransaction
from src.modules.payments.payment_schema import (
    MidtransWebhookPayload,
    PaymentStatusResponse,
    WebhookSuccessResponse,
)


class PaymentService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)

    async def initiate_direct_charge(
        self,
        order,
        payment_method: str = "qris",
        bank: Optional[str] = None,
    ) -> PaymentTransaction:
        """
        Memproses pembayaran langsung via Midtrans Core API (tanpa Snap).
        Menghasilkan QRIS string/URL atau Bank Virtual Account number.
        """
        customer_details = {
            "first_name": order.customer_name,
            "email": order.customer_email,
            "phone": order.customer_phone or "",
        }

        item_details = [
            {
                "id": str(item.variant_id or item.id),
                "price": item.price,
                "quantity": item.quantity,
                "name": f"{item.product_name} - {item.variant_name}"[:50],
            }
            for item in order.items
        ]

        payment_method_lower = payment_method.lower().strip()

        if payment_method_lower == "qris":
            midtrans_res = await midtrans_client.charge_qris(
                order_id=order.order_number,
                gross_amount=order.total_amount,
                customer_details=customer_details,
                item_details=item_details,
            )
            payment_type = "qris"
            bank_val = None
        else:
            # Bank Virtual Account
            bank_choice = (bank or "bca").lower().strip()
            midtrans_res = await midtrans_client.charge_bank_transfer(
                order_id=order.order_number,
                gross_amount=order.total_amount,
                bank=bank_choice,
                customer_details=customer_details,
                item_details=item_details,
            )
            payment_type = "bank_transfer"
            bank_val = bank_choice

        # Simpan transaksi pembayaran ke database
        payment = await self.repo.create_payment_transaction(
            order_id=order.id,
            payment_type=payment_type,
            gross_amount=order.total_amount,
            midtrans_response=midtrans_res,
            bank=bank_val,
        )
        return payment

    async def process_webhook_notification(self, payload: MidtransWebhookPayload) -> WebhookSuccessResponse:
        """
        Memproses notifikasi webhook resmi dari Midtrans.
        Verifikasi SHA-512 signature, update status pesanan, kirim email receipt & alert WhatsApp ke staf.
        """
        # 1. Verifikasi Signature Key
        is_valid = midtrans_client.verify_webhook_signature(
            order_id=payload.order_id,
            status_code=payload.status_code,
            gross_amount=payload.gross_amount,
            signature_key=payload.signature_key,
        )

        # Log webhook audit
        await self.repo.log_webhook(
            order_id=payload.order_id,
            status=payload.transaction_status,
            signature_valid=is_valid,
            payload=payload.model_dump(),
        )

        if not is_valid:
            await self.commit()
            raise BadRequestException("Signature webhook Midtrans tidak valid.")

        # 2. Ambil data pesanan
        order = await self.order_repo.get_order_by_number(payload.order_id)
        if not order:
            await self.commit()
            raise NotFoundException(f"Order #{payload.order_id} tidak ditemukan.")

        tx_status = payload.transaction_status.lower()
        fraud_status = payload.fraud_status.lower() if payload.fraud_status else None

        # 3. Penentuan Status Pembayaran
        new_order_status = order.status
        paid_at = None

        if tx_status == "settlement" or (tx_status == "capture" and fraud_status == "accept"):
            new_order_status = "paid"
            paid_at = datetime.now(timezone.utc)
        elif tx_status in ["cancel", "deny"]:
            new_order_status = "cancelled"
        elif tx_status == "expire":
            new_order_status = "expired"
        elif tx_status == "pending":
            new_order_status = "pending"

        # Update status di database
        await self.order_repo.update_order_status(order.id, status=new_order_status, paid_at=paid_at)
        await self.repo.update_payment_status(order.id, transaction_status=tx_status, fraud_status=fraud_status)
        await self.commit()

        # 4. Trigger Notifikasi Otomatis Jika Pembayaran Lunas
        if new_order_status == "paid":
            # A. Kirim Email Tanda Terima & Link Unduhan ke Pelanggan
            download_url = f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/downloads"
            
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
                <h2 style="color: #16a34a;">Pembayaran Berhasil!</h2>
                <p>Halo <strong>{order.customer_name}</strong>,</p>
                <p>Terima kasih! Pembayaran untuk pesanan <strong>#{order.order_number}</strong> sebesar <strong>Rp {order.total_amount:,}</strong> telah kami terima.</p>
                <p>Aset produk digital Anda sekarang sudah aktif dan siap diunduh.</p>
                <p style="margin: 25px 0;">
                    <a href="{download_url}" style="background-color: #2563eb; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Unduh Produk Digital Anda
                    </a>
                </p>
                <p style="color: #666; font-size: 13px;">Salam hangat,<br>Tim {settings.APP_NAME}</p>
            </div>
            """
            await mailer.send_email(
                to_email=order.customer_email,
                subject=f"Pembayaran Berhasil #{order.order_number} - {settings.APP_NAME}",
                html_content=email_html,
            )

            # B. Kirim WhatsApp Alert Khusus ke Superadmin, Admin, dan Staff
            wa_alert = (
                f"🚨 *NOTIFIKASI PESANAN MASUK (LUNAS)* 🚨\n\n"
                f"• No. Order: #{order.order_number}\n"
                f"• Pembeli: {order.customer_name} ({order.customer_email})\n"
                f"• Total: Rp {order.total_amount:,}\n"
                f"• Metode: {payload.payment_type or order.payment_method}\n"
                f"• Waktu: {datetime.now(timezone.utc).strftime('%d-%m-%Y %H:%M UTC')}\n\n"
                f"Status pesanan telah otomatis diperbarui menjadi *PAID*."
            )
            await whatsapp_client.notify_admins(wa_alert)

        return WebhookSuccessResponse()

    async def get_status_by_order_number(self, order_number: str) -> PaymentStatusResponse:
        order = await self.order_repo.get_order_by_number(order_number)
        if not order:
            raise NotFoundException("Pesanan tidak ditemukan.")

        payment = await self.repo.get_by_order_id(order.id)
        return PaymentStatusResponse(
            order_number=order.order_number,
            transaction_status=payment.transaction_status if payment else order.status,
            payment_type=payment.payment_type if payment else (order.payment_method or "unknown"),
            gross_amount=order.total_amount,
            is_paid=(order.status == "paid"),
            paid_at=order.paid_at,
        )
