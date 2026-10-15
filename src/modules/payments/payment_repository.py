from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.payments.payment_model import PaymentTransaction, PaymentWebhookLog


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_order_id(self, order_id: str) -> Optional[PaymentTransaction]:
        stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def create_payment_transaction(
        self,
        order_id: str,
        payment_type: str,
        gross_amount: int,
        midtrans_response: Dict[str, Any],
        bank: Optional[str] = None,
    ) -> PaymentTransaction:
        # Ekstrak data spesifik Direct QRIS atau Direct VA dari respon Midtrans Core API
        qr_string = midtrans_response.get("qr_string")
        qr_code_url = None
        if "actions" in midtrans_response:
            for act in midtrans_response["actions"]:
                if act.get("name") == "generate-qr-code":
                    qr_code_url = act.get("url")
                    break

        va_number = None
        if "va_numbers" in midtrans_response and midtrans_response["va_numbers"]:
            va_number = midtrans_response["va_numbers"][0].get("va_number")
            if not bank:
                bank = midtrans_response["va_numbers"][0].get("bank")

        bill_key = midtrans_response.get("bill_key")
        biller_code = midtrans_response.get("biller_code")

        expiry_time = None
        if "expiry_time" in midtrans_response:
            try:
                expiry_time = datetime.fromisoformat(midtrans_response["expiry_time"].replace(" ", "T"))
            except Exception:
                pass

        payment = PaymentTransaction(
            order_id=order_id,
            midtrans_transaction_id=midtrans_response.get("transaction_id"),
            payment_type=payment_type,
            gross_amount=gross_amount,
            transaction_status=midtrans_response.get("transaction_status", "pending"),
            fraud_status=midtrans_response.get("fraud_status"),
            qr_string=qr_string,
            qr_code_url=qr_code_url,
            bank=bank,
            va_number=va_number,
            bill_key=bill_key,
            biller_code=biller_code,
            expiry_time=expiry_time,
            raw_response=midtrans_response,
        )
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def update_payment_status(
        self,
        order_id: str,
        transaction_status: str,
        fraud_status: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        update_data = {
            "transaction_status": transaction_status,
            "updated_at": datetime.now(timezone.utc),
        }
        if fraud_status:
            update_data["fraud_status"] = fraud_status

        stmt = (
            update(PaymentTransaction)
            .where(PaymentTransaction.order_id == order_id)
            .values(**update_data)
        )
        await self.db.execute(stmt)
        return await self.get_by_order_id(order_id)

    async def log_webhook(
        self,
        order_id: Optional[str],
        status: Optional[str],
        signature_valid: bool,
        payload: Dict[str, Any],
    ) -> None:
        log = PaymentWebhookLog(
            order_id=order_id,
            transaction_status=status,
            signature_valid=signature_valid,
            payload=payload,
        )
        self.db.add(log)
        await self.db.flush()
