from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.dependencies import require_permissions
from src.modules.payments.payment_service import PaymentService
from src.modules.payments.payment_schema import (
    MidtransWebhookPayload,
    PaymentStatusResponse,
    WebhookSuccessResponse,
)

router = APIRouter(prefix="/api/v1/payments", tags=["Payments & Midtrans Core API"])


@router.post(
    "/webhook",
    response_model=WebhookSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Webhook Listener Notifikasi Otomatis Pembayaran dari Midtrans (Non-Snap)",
)
async def midtrans_webhook_listener(
    payload: MidtransWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint HTTP Webhook yang menerima notifikasi real-time dari Midtrans.
    Otomatis memverifikasi signature hash SHA-512, mengupdate status order menjadi PAID,
    dan mengirim notifikasi email + WhatsApp staf.
    """
    service = PaymentService(db)
    return await service.process_webhook_notification(payload)


@router.get(
    "/status/{order_number}",
    response_model=PaymentStatusResponse,
    summary="Polling Status Pembayaran Pesanan (Untuk Frontend Check Status)",
)
async def check_payment_status(
    order_number: str,
    db: AsyncSession = Depends(get_db),
):
    service = PaymentService(db)
    return await service.get_status_by_order_number(order_number)


@router.post(
    "/sync-midtrans/{order_number}",
    response_model=PaymentStatusResponse,
    summary="Sinkronisasi Manual Status Transaksi Langsung ke Server Midtrans (Finance / Admin)",
    dependencies=[Depends(require_permissions("payment:manage"))],
)
async def sync_with_midtrans_server(
    order_number: str,
    db: AsyncSession = Depends(get_db),
):
    from src.config.midtrans import midtrans_client
    service = PaymentService(db)

    # Ambil status langsung dari Midtrans API
    midtrans_status = await midtrans_client.get_transaction_status(order_number)

    # Simulasikan webhook payload untuk auto-update
    mock_payload = MidtransWebhookPayload(
        order_id=order_number,
        status_code=midtrans_status.get("status_code", "200"),
        gross_amount=str(midtrans_status.get("gross_amount", "0")),
        signature_key=midtrans_status.get("signature_key", ""),
        transaction_status=midtrans_status.get("transaction_status", "pending"),
        fraud_status=midtrans_status.get("fraud_status"),
        payment_type=midtrans_status.get("payment_type"),
        transaction_id=midtrans_status.get("transaction_id"),
    )
    # Update status transaksi
    order = await service.order_repo.get_order_by_number(order_number)
    if order:
        tx_status = midtrans_status.get("transaction_status", "").lower()
        new_status = "paid" if tx_status in ["settlement", "capture"] else tx_status
        await service.order_repo.update_order_status(order.id, status=new_status)
        await service.repo.update_payment_status(order.id, transaction_status=tx_status)
        await service.commit()

    return await service.get_status_by_order_number(order_number)
