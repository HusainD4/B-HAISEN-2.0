import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database_base import Base, IDMixin, TimestampMixin


class CartItem(Base, IDMixin, TimestampMixin):
    """Tabel keranjang belanja tersimpan di database (sinkron di seluruh perangkat user)."""
    __tablename__ = "cart_items"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relasi
    user = relationship("src.modules.auth.auth_model.User", lazy="selectin")
    product = relationship("src.modules.products.product_model.Product", lazy="selectin")
    variant = relationship("src.modules.products.product_model.ProductVariant", lazy="selectin")


class Order(Base, IDMixin, TimestampMixin):
    """Tabel data transaksi pesanan pelanggan."""
    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)

    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Total pembayaran IDR (produk + ongkir)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True, nullable=False)  # pending, paid, expired, cancelled, refunded
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # qris, bca_va, bni_va, bri_va, mandiri
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Catatan pesanan
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Data Pengiriman Khusus Indonesia (Kalkulasi RajaOngkir)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Nama jalan, RT/RW, Patokan/Detail rumah
    shipping_province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Provinsi
    shipping_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Kabupaten/Kota
    shipping_district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Kecamatan
    shipping_postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Kode Pos
    shipping_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Ongkir
    courier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # JNE, POS, TIKI, SiCepat
    courier_service: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Layanan kurir

    # Relasi
    user = relationship("src.modules.auth.auth_model.User", lazy="selectin")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    payment = relationship("src.modules.payments.payment_model.PaymentTransaction", back_populates="order", uselist=False, lazy="selectin")


class OrderItem(Base, IDMixin):
    """Tabel rincian item produk digital dalam pesanan."""
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    variant_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)

    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variant_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot lisensi & file key saat pembelian agar link unduhan permanen bagi pembeli
    license_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    digital_file_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
