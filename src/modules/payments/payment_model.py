from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database_base import Base, IDMixin, TimestampMixin


class PaymentTransaction(Base, IDMixin, TimestampMixin):
    """
    Tabel data pembayaran Midtrans Core API (Direct QRIS & Direct Bank Virtual Account).
    Menyimpan instruksi pembayaran langsung untuk ditampilkan di halaman frontend tanpa popup.
    """
    __tablename__ = "payment_transactions"

    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    midtrans_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    payment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # qris, bank_transfer, echannel, permata
    gross_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    fraud_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 1. Data Khusus Direct QRIS
    qr_string: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Payload string QRIS dinamis
    qr_code_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL gambar QR code dari Midtrans

    # 2. Data Khusus Direct Bank Virtual Account
    bank: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # bca, bni, bri, permata, mandiri
    va_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Nomor Virtual Account
    bill_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Kode tagihan Mandiri
    biller_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Kode perusahaan Mandiri

    expiry_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    order = relationship("src.modules.orders.order_model.Order", back_populates="payment")


class PaymentWebhookLog(Base, IDMixin, TimestampMixin):
    """Log audit webhook Midtrans untuk rekonsiliasi dan investigasi transaksi."""
    __tablename__ = "payment_webhook_logs"

    order_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    transaction_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
