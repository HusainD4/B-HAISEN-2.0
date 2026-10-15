from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database_base import Base, IDMixin, TimestampMixin, SoftDeleteMixin


class ProductCategory(Base, IDMixin, TimestampMixin):
    """Tabel kategori produk digital (Template Web, Script/Source Code, UI Kit, Layanan Jasa, dll)."""
    __tablename__ = "product_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="category", lazy="selectin")


class Product(Base, IDMixin, TimestampMixin, SoftDeleteMixin):
    """Tabel katalog produk digital & layanan."""
    __tablename__ = "products"

    category_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # 1. Gambar Banner & Gambar Utama Produk
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gallery_images: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    base_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Harga dasar IDR
    discount_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Tipe Produk: 'digital' (source code/aset), 'service' (jasa), 'physical' (barang fisik/pengiriman kurir)
    product_type: Mapped[str] = mapped_column(String(20), default="digital", nullable=False)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # SEO Metadata
    meta_title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    category: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory", back_populates="products", lazy="selectin")
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProductVariant(Base, IDMixin, TimestampMixin):
    """
    Tabel varian produk:
    Setiap varian memiliki harga, gambar varian khusus, lisensi, dan file unduhan digital terproteksi sendiri.
    """
    __tablename__ = "product_variants"

    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Misal: "Personal License", "Commercial Extended"
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # 2. Gambar Khusus Varian Produk
    variant_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Harga spesifik varian
    discount_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = Unlimited digital stock

    # 3. File Aset Digital Terproteksi di S3/R2 Bucket
    license_type: Mapped[Optional[str]] = mapped_column(String(50), default="standard", nullable=True)
    digital_file_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # S3 Object Key
    digital_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    digital_file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Bytes

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")
