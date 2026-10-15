from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from src.modules.users.user_schema import PaginationMeta


# ==========================================
# Category Schemas
# ==========================================

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    icon_url: Optional[str] = None
    is_active: bool = True


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: Optional[bool] = None


# ==========================================
# Variant Schemas
# ==========================================

class VariantResponse(BaseModel):
    id: str
    product_id: str
    name: str
    sku: str
    variant_image_url: Optional[str] = None  # Gambar khusus varian
    price: int
    discount_price: Optional[int] = None
    stock: Optional[int] = None
    license_type: Optional[str] = None
    digital_file_name: Optional[str] = None
    digital_file_size: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class VariantCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nama varian (contoh: Commercial Extended)")
    sku: str = Field(..., min_length=2, max_length=50, description="SKU unik varian")
    variant_image_url: Optional[str] = Field(None, description="URL gambar varian dari bucket")
    price: int = Field(..., ge=0, description="Harga jual varian dalam IDR")
    discount_price: Optional[int] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0, description="None = Unlimited digital stock")
    license_type: Optional[str] = Field("standard", description="Tipe lisensi (personal/commercial/developer)")
    digital_file_key: Optional[str] = Field(None, description="S3 Key file aset terproteksi di bucket")
    digital_file_name: Optional[str] = None
    digital_file_size: Optional[int] = None
    is_active: bool = True


class VariantUpdateRequest(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    variant_image_url: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    discount_price: Optional[int] = Field(None, ge=0)
    stock: Optional[int] = None
    license_type: Optional[str] = None
    digital_file_key: Optional[str] = None
    digital_file_name: Optional[str] = None
    digital_file_size: Optional[int] = None
    is_active: Optional[bool] = None


# ==========================================
# Product Schemas
# ==========================================

class ProductListItemResponse(BaseModel):
    id: str
    category: Optional[CategoryResponse] = None
    name: str
    slug: str
    short_description: Optional[str] = None
    banner_image_url: Optional[str] = None  # Gambar banner produk
    thumbnail_url: Optional[str] = None     # Gambar utama produk
    base_price: int
    discount_price: Optional[int] = None
    product_type: str = "digital"  # 'digital' | 'service' | 'physical'
    is_featured: bool
    is_active: bool
    variants_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(BaseModel):
    id: str
    category: Optional[CategoryResponse] = None
    name: str
    slug: str
    short_description: Optional[str] = None
    description: str
    banner_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    gallery_images: List[str] = []
    base_price: int
    discount_price: Optional[int] = None
    product_type: str = "digital"  # 'digital' | 'service' | 'physical'
    is_featured: bool
    is_active: bool
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    variants: List[VariantResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCreateRequest(BaseModel):
    category_id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=160)
    short_description: Optional[str] = Field(None, max_length=300)
    description: str = Field(..., min_length=10)
    banner_image_url: Optional[str] = Field(None, description="URL banner dari upload bucket")
    thumbnail_url: Optional[str] = Field(None, description="URL thumbnail dari upload bucket")
    gallery_images: List[str] = Field(default_factory=list, description="Array URL galeri gambar produk")
    base_price: int = Field(0, ge=0)
    discount_price: Optional[int] = Field(None, ge=0)
    product_type: str = Field("digital", description="Tipe produk: 'digital' (file/lisensi), 'service' (jasa), 'physical' (barang fisik kurir)")
    is_featured: bool = False
    is_active: bool = True
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    variants: List[VariantCreateRequest] = Field(default_factory=list, description="Daftar varian beserta gambar & aset")


class ProductUpdateRequest(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    banner_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    base_price: Optional[int] = Field(None, ge=0)
    discount_price: Optional[int] = Field(None, ge=0)
    product_type: Optional[str] = Field(None, description="Tipe produk: 'digital' | 'service' | 'physical'")
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


# ==========================================
# Upload & Storage Responses
# ==========================================

class ImageUploadResponse(BaseModel):
    file_key: str
    url: str
    message: str = "Gambar berhasil diunggah ke Object Storage (Bucket)."


class DigitalAssetUploadResponse(BaseModel):
    file_key: str
    file_name: str
    file_size: int
    message: str = "File digital terproteksi berhasil diunggah ke Bucket."


class PresignedDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_seconds: int = 3600
    file_name: Optional[str] = None


class PaginatedProductsResponse(BaseModel):
    items: List[ProductListItemResponse]
    meta: PaginationMeta
