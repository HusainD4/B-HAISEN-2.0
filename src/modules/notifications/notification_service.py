"""
Modul: Notification Service
Layanan terpusat untuk pengiriman Email (SMTP) dan WhatsApp (WA Gateway).
Dipanggil dari service lain (orders, payments) — tidak langsung dari controller.
"""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
import httpx

from src.config.settings import settings
from src.modules.notifications.notification_templates import (
    email_digital_product_delivery,
    email_order_receipt,
    email_order_status_update,
    email_payment_success,
    wa_download_link_customer,
    wa_order_created_admin,
    wa_order_status_customer,
    wa_payment_success_admin,
)

logger = logging.getLogger(__name__)


# ============================================================
# EMAIL SERVICE
# ============================================================

async def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Kirim email HTML via SMTP async (aiosmtplib)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=False,
        ) as smtp:
            await smtp.starttls()
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            await smtp.send_message(msg)

        logger.info("Email terkirim ke %s | Subject: %s", to_email, subject)
        return True
    except Exception as exc:
        logger.error("Gagal kirim email ke %s: %s", to_email, exc)
        return False


# ============================================================
# WHATSAPP SERVICE
# ============================================================

async def _send_whatsapp(phone: str, message: str) -> bool:
    """
    Kirim pesan WhatsApp via self-hosted WA gateway (misal: waha/whatsapp-web.js).
    Format nomor: 628xxxxxxxxxx (tanpa +, tanpa 0 di depan).
    """
    if not settings.WA_GATEWAY_URL or not settings.WA_API_KEY:
        logger.warning("WA Gateway tidak dikonfigurasi, lewati pengiriman WA.")
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.WA_GATEWAY_URL}/api/sendText",
                headers={"X-Api-Key": settings.WA_API_KEY},
                json={"chatId": f"{phone}@c.us", "text": message, "session": "default"},
            )
            resp.raise_for_status()
        logger.info("WA terkirim ke %s", phone)
        return True
    except Exception as exc:
        logger.error("Gagal kirim WA ke %s: %s", phone, exc)
        return False


async def _blast_wa_admins(message: str) -> None:
    """Kirim WA blast ke semua nomor admin yang dikonfigurasi."""
    if not settings.WA_ADMIN_NUMBERS:
        return
    for number in settings.WA_ADMIN_NUMBERS.split(","):
        await _send_whatsapp(number.strip(), message)


# ============================================================
# HIGH-LEVEL NOTIFICATION ACTIONS
# ============================================================

class NotificationService:
    """
    Service publik dipanggil dari modul orders/payments.
    Setiap method menggabungkan pengiriman email + WA sesuai skenario.
    """

    @staticmethod
    async def notify_order_created(
        customer_email: str,
        customer_name: str,
        customer_phone: Optional[str],
        order_code: str,
        items: list[dict],
        total_amount: int,
        payment_method: str,
        order_date: str,
    ) -> None:
        """Notifikasi saat pesanan baru dibuat (ke customer + admin)."""
        # Email ke customer
        template = email_order_receipt(
            customer_name, order_code, items,
            total_amount, payment_method, order_date,
        )
        await _send_email(customer_email, template["subject"], template["html"])

        # WA ke admin
        items_summary = ", ".join(f"{i['name']} x{i['qty']}" for i in items)
        await _blast_wa_admins(
            wa_order_created_admin(order_code, customer_name, total_amount, items_summary)
        )

    @staticmethod
    async def notify_payment_success(
        customer_email: str,
        customer_name: str,
        customer_phone: Optional[str],
        order_code: str,
        total_amount: int,
        payment_method: str,
        paid_at: str,
    ) -> None:
        """Notifikasi saat pembayaran berhasil dikonfirmasi."""
        template = email_payment_success(customer_name, order_code, total_amount, paid_at)
        await _send_email(customer_email, template["subject"], template["html"])

        await _blast_wa_admins(
            wa_payment_success_admin(order_code, customer_name, total_amount, payment_method)
        )

    @staticmethod
    async def notify_digital_delivery(
        customer_email: str,
        customer_name: str,
        customer_phone: Optional[str],
        order_code: str,
        product_name: str,
        download_url: str,
        expires_at: str,
    ) -> None:
        """Notifikasi pengiriman produk digital (link download)."""
        template = email_digital_product_delivery(
            customer_name, order_code, product_name, download_url, expires_at
        )
        await _send_email(customer_email, template["subject"], template["html"])

        if customer_phone:
            await _send_whatsapp(
                customer_phone,
                wa_download_link_customer(customer_name, product_name, download_url, expires_at),
            )

    @staticmethod
    async def notify_order_status_update(
        customer_email: str,
        customer_name: str,
        customer_phone: Optional[str],
        order_code: str,
        new_status: str,
        note: str = "",
    ) -> None:
        """Notifikasi perubahan status pesanan ke customer."""
        template = email_order_status_update(customer_name, order_code, new_status, note)
        await _send_email(customer_email, template["subject"], template["html"])

        if customer_phone:
            status_label = template["subject"].split("–")[-1].strip() if "–" in template["subject"] else new_status
            await _send_whatsapp(
                customer_phone,
                wa_order_status_customer(customer_name, order_code, status_label, note),
            )
