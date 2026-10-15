from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class MidtransWebhookPayload(BaseModel):
    """Payload data notifikasi otomatis webhook dari Midtrans."""
    order_id: str
    status_code: str
    gross_amount: str
    signature_key: str
    transaction_status: str
    fraud_status: Optional[str] = None
    payment_type: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_time: Optional[str] = None
    settlement_time: Optional[str] = None
    bank: Optional[str] = None
    va_numbers: Optional[list] = None
    bill_key: Optional[str] = None
    biller_code: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    order_number: str
    transaction_status: str
    payment_type: str
    gross_amount: int
    is_paid: bool
    paid_at: Optional[datetime] = None


class WebhookSuccessResponse(BaseModel):
    success: bool = True
    message: str = "Webhook notifikasi Midtrans berhasil diverifikasi dan diproses."
