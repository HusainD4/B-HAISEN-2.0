from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.dependencies import (
    get_current_user,
    CurrentUser,
    require_permissions,
    require_roles,
)
from src.modules.products.product_service import ProductService
from src.modules.products.product_schema import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductListItemResponse,
    ProductDetailResponse,
    PaginatedProductsResponse,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    VariantCreateRequest,
    VariantUpdateRequest,
    VariantResponse,
    ImageUploadResponse,
    DigitalAssetUploadResponse,
    PresignedDownloadUrlResponse,
)
from src.modules.auth.auth_schema import MessageResponse

router = APIRouter(prefix="/api/v1/products", tags=["Product Catalog & Digital Assets"])


# ==========================================
# 1. Bucket Storage Upload Endpoints (Admin / Staff)
# ==========================================

@router.post(
    "/upload/banner",
    response_model=ImageUploadResponse,
    summary="Upload Gambar Banner Produk ke Object Storage Bucket",
    dependencies=[Depends(require_permissions("product:create"))],
)
async def upload_banner(
    file: UploadFile = File(..., description="File gambar banner (JPG, PNG, WebP)"),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.upload_banner_image(file)


@router.post(
    "/upload/thumbnail",
    response_model=ImageUploadResponse,
    summary="Upload Gambar Utama Produk ke Object Storage Bucket",
    dependencies=[Depends(require_permissions("product:create"))],
)
async def upload_thumbnail(
    file: UploadFile = File(..., description="File gambar utama produk"),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.upload_product_thumbnail(file)


@router.post(
    "/upload/variant-image",
    response_model=ImageUploadResponse,
    summary="Upload Gambar Khusus Varian Produk ke Object Storage Bucket",
    dependencies=[Depends(require_permissions("product:create"))],
)
async def upload_variant_image(
    file: UploadFile = File(..., description="File gambar varian produk"),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.upload_variant_image(file)


@router.post(
    "/upload/digital-file",
    response_model=DigitalAssetUploadResponse,
    summary="Upload File Aset Digital Terproteksi (ZIP/PDF/Software) ke Private Bucket",
    dependencies=[Depends(require_permissions("product:create"))],
)
async def upload_digital_file(
    file: UploadFile = File(..., description="File digital yang akan didistribusikan kepada pembeli"),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.upload_digital_asset(file)


# ==========================================
# 2. Public Catalog Endpoints (Publik / Pembeli)
# ==========================================

@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="Daftar Kategori Produk Aktif (Publik)",
)
async def get_active_categories(
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.list_categories(active_only=True)


@router.get(
    "",
    response_model=PaginatedProductsResponse,
    summary="Katalog Daftar Produk (Publik - Paginasi, Filter & Sorting)",
)
async def list_products(
    page: int = Query(1, ge=1, description="Halaman"),
    limit: int = Query(12, ge=1, le=50, description="Item per halaman"),
    search: Optional[str] = Query(None, description="Pencarian kata kunci"),
    category: Optional[str] = Query(None, description="Slug kategori produk"),
    featured: Optional[bool] = Query(None, description="Hanya produk unggulan/featured"),
    sort: str = Query("newest", description="Sorting: newest | price_asc | price_desc"),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.get_products_list(
        page=page,
        limit=limit,
        search=search,
        category_slug=category,
        is_featured=featured,
        is_active=True,
        sort_by=sort,
    )


@router.get(
    "/detail/{slug}",
    response_model=ProductDetailResponse,
    summary="Detail Lengkap Produk Berdasarkan Slug (Publik)",
)
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.get_product_by_slug(slug)


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Detail Produk Berdasarkan ID",
)
async def get_product_by_id(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.get_product_by_id(product_id)


# ==========================================
# 3. Product CRUD (Admin / Superadmin)
# ==========================================

@router.post(
    "",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Produk Baru Lengkap Dengan Varian & Gambar",
    dependencies=[Depends(require_permissions("product:create"))],
)
async def create_product(
    payload: ProductCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.create_product(payload)


@router.put(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Perbarui Informasi Produk",
    dependencies=[Depends(require_permissions("product:update"))],
)
async def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.update_product(product_id, payload)


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Hapus Produk (Soft-Delete)",
    dependencies=[Depends(require_permissions("product:delete"))],
)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    await service.delete_product(product_id)
    return MessageResponse(message="Produk berhasil dihapus.")


# ==========================================
# 4. Variant Operations
# ==========================================

@router.post(
    "/{product_id}/variants",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Varian Baru ke Suatu Produk",
    dependencies=[Depends(require_permissions("product:update"))],
)
async def add_product_variant(
    product_id: str,
    payload: VariantCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.add_variant(product_id, payload)


@router.put(
    "/variants/{variant_id}",
    response_model=VariantResponse,
    summary="Perbarui Varian Produk (Harga/Gambar/Aset)",
    dependencies=[Depends(require_permissions("product:update"))],
)
async def update_product_variant(
    variant_id: str,
    payload: VariantUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.update_variant(variant_id, payload)


@router.delete(
    "/variants/{variant_id}",
    response_model=MessageResponse,
    summary="Hapus Varian Produk",
    dependencies=[Depends(require_permissions("product:update"))],
)
async def delete_product_variant(
    variant_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    await service.delete_variant(variant_id)
    return MessageResponse(message="Varian produk berhasil dihapus.")


@router.get(
    "/variants/{variant_id}/download-url",
    response_model=PresignedDownloadUrlResponse,
    summary="Dapatkan Tautan Unduh Presigned Berbatas Waktu untuk File Digital Varian",
    dependencies=[Depends(get_current_user)],
)
async def get_presigned_download_url(
    variant_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.get_variant_presigned_download(variant_id)


# ==========================================
# 5. Category Management (Admin / Superadmin)
# ==========================================

@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat Kategori Produk Baru",
    dependencies=[Depends(require_permissions("product:create"))],
)
async def create_category(
    payload: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.create_category(payload)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Perbarui Kategori Produk",
    dependencies=[Depends(require_permissions("product:update"))],
)
async def update_category(
    category_id: str,
    payload: CategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    return await service.update_category(category_id, payload)


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    summary="Hapus Kategori Produk",
    dependencies=[Depends(require_permissions("product:delete"))],
)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    await service.delete_category(category_id)
    return MessageResponse(message="Kategori produk berhasil dihapus.")
