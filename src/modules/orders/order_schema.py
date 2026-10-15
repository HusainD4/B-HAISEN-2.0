from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.modules.users.user_schema import PaginationMeta


# ==========================================
# 1. Cart Schemas (DB Stored)
# ==========================================

class CartItemAddRequest(BaseModel):
    variant_id: str = Field(..., description="ID varian produk digital yang ingin ditambahkan ke keranjang")
    quantity: int = Field(1, ge=1, le=100, description="Kuantitas (default 1)")


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=100, description="Kuantitas baru")


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    variant_id: str
    product_name: str
    product_slug: str
    variant_name: str
    variant_image_url: Optional[str] = None
    price: int
    quantity: int
    subtotal: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_amount: int


# ==========================================
# 2. Checkout & Order Schemas
# ==========================================

class CheckoutRequest(BaseModel):
    payment_method: str = Field("qris", description="Metode: 'qris' atau 'bank_transfer'")
    bank: Optional[str] = Field(None, description="Pilihan bank jika bank_transfer: bca, bni, bri, permata, mandiri")
    customer_name: Optional[str] = Field(None, min_length=2, max_length=100)
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = Field(None, max_length=25)
    
    # Data Pengiriman Indonesia (RajaOngkir & Kurir)
    shipping_address: Optional[str] = Field(None, description="Nama jalan, RT/RW, Patokan/Detail rumah (kawasan Indonesia)")
    shipping_province: Optional[str] = Field(None, description="Provinsi tujuan pengiriman")
    shipping_city: Optional[str] = Field(None, description="Kabupaten / Kota (untuk kalkulasi ongkir)")
    shipping_district: Optional[str] = Field(None, description="Kecamatan (untuk kalkulasi ongkir)")
    shipping_postal_code: Optional[str] = Field(None, max_length=10, description="Kode Pos validasi kurir")
    courier: Optional[str] = Field(None, description="Kurir: jne, pos, tiki, sicepat, dll.")
    courier_service: Optional[str] = Field(None, description="Paket layanan kurir (REG, YES, OKE)")
    shipping_cost: int = Field(0, ge=0, description="Ongkos kirim (IDR)")
    notes: Optional[str] = Field(None, max_length=500, description="Catatan pesanan")


class DirectBuyRequest(BaseModel):
    variant_id: str = Field(..., description="ID Varian produk untuk beli langsung (instan tanpa keranjang)")
    quantity: int = Field(1, ge=1, le=100)
    payment_method: str = Field("qris", description="'qris' atau 'bank_transfer'")
    bank: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    
    # Data Pengiriman Indonesia (RajaOngkir & Kurir)
    shipping_address: Optional[str] = Field(None, description="Nama jalan, RT/RW, Patokan/Detail rumah")
    shipping_province: Optional[str] = Field(None, description="Provinsi tujuan pengiriman")
    shipping_city: Optional[str] = Field(None, description="Kabupaten / Kota")
    shipping_district: Optional[str] = Field(None, description="Kecamatan")
    shipping_postal_code: Optional[str] = Field(None, max_length=10, description="Kode Pos")
    courier: Optional[str] = None
    courier_service: Optional[str] = None
    shipping_cost: int = Field(0, ge=0, description="Ongkos kirim (IDR)")
    notes: Optional[str] = Field(None, max_length=500, description="Catatan pesanan")


class OrderItemResponse(BaseModel):
    id: str
    product_id: Optional[str]
    variant_id: Optional[str]
    product_name: str
    variant_name: str
    variant_image_url: Optional[str] = None
    price: int
    quantity: int
    subtotal: int
    license_type: Optional[str] = None
    has_digital_file: bool = False

    model_config = ConfigDict(from_attributes=True)


class PaymentInstructionResponse(BaseModel):
    payment_type: str
    status: str
    gross_amount: int
    # QRIS info
    qr_string: Optional[str] = None
    qr_code_url: Optional[str] = None
    # Virtual Account info
    bank: Optional[str] = None
    va_number: Optional[str] = None
    bill_key: Optional[str] = None
    biller_code: Optional[str] = None
    expiry_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderDetailResponse(BaseModel):
    id: str
    order_number: str
    total_amount: int
    status: str
    payment_method: Optional[str] = None
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None

    # Pengiriman Indonesia
    shipping_address: Optional[str] = None
    shipping_province: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_district: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_cost: int = 0
    courier: Optional[str] = None
    courier_service: Optional[str] = None

    items: List[OrderItemResponse] = []
    payment: Optional[PaymentInstructionResponse] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderSummaryResponse(BaseModel):
    id: str
    order_number: str
    total_amount: int
    status: str
    payment_method: Optional[str] = None
    customer_name: str
    items_count: int
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedOrdersResponse(BaseModel):
    items: List[OrderSummaryResponse]
    meta: PaginationMeta
