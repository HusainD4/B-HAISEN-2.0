from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.base_service import BaseService
from src.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
)
from src.config.storage import storage_client
from src.modules.products.product_repository import ProductRepository
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
from src.modules.users.user_schema import PaginationMeta


class ProductService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = ProductRepository(db)

    # ==========================================
    # 1. Bucket Upload Handlers (Supabase Storage Bucket)
    # ==========================================

    async def upload_banner_image(self, file: UploadFile) -> ImageUploadResponse:
        """Upload gambar banner produk ke folder 'banners' di bucket."""
        key, public_url = await storage_client.upload_file(file, folder_prefix="banners")
        return ImageUploadResponse(file_key=key, url=public_url, message="Gambar banner berhasil diunggah ke bucket.")

    async def upload_product_thumbnail(self, file: UploadFile) -> ImageUploadResponse:
        """Upload gambar utama/thumbnail produk ke folder 'products' di bucket."""
        key, public_url = await storage_client.upload_file(file, folder_prefix="products")
        return ImageUploadResponse(file_key=key, url=public_url, message="Gambar produk berhasil diunggah ke bucket.")

    async def upload_variant_image(self, file: UploadFile) -> ImageUploadResponse:
        """Upload gambar khusus varian produk ke folder 'variants' di bucket."""
        key, public_url = await storage_client.upload_file(file, folder_prefix="variants")
        return ImageUploadResponse(file_key=key, url=public_url, message="Gambar varian berhasil diunggah ke bucket.")

    async def upload_digital_asset(self, file: UploadFile) -> DigitalAssetUploadResponse:
        """Upload file digital terproteksi (ZIP/PDF/Software) ke folder 'protected-assets' di bucket."""
        key, size = await storage_client.upload_protected_digital_file(file, folder_prefix="protected-assets")
        return DigitalAssetUploadResponse(
            file_key=key,
            file_name=file.filename or "asset.zip",
            file_size=size,
            message="File aset digital berhasil diunggah secara aman ke bucket.",
        )

    async def get_variant_presigned_download(self, variant_id: str) -> PresignedDownloadUrlResponse:
        """Generate presigned download URL berbatas waktu 1 jam untuk aset varian."""
        variant = await self.repo.get_variant_by_id(variant_id)
        if not variant:
            raise NotFoundException("Varian produk tidak ditemukan.")

        if not variant.digital_file_key:
            raise BadRequestException("Varian ini tidak memiliki file digital unduhan.")

        url = storage_client.generate_presigned_download_url(
            file_key=variant.digital_file_key,
            expires_in_seconds=3600,
        )
        return PresignedDownloadUrlResponse(
            download_url=url,
            expires_in_seconds=3600,
            file_name=variant.digital_file_name,
        )

    # ==========================================
    # 2. Category Service
    # ==========================================

    async def list_categories(self, active_only: bool = True) -> List[CategoryResponse]:
        categories = await self.repo.get_categories(active_only=active_only)
        return [CategoryResponse.model_validate(c) for c in categories]

    async def create_category(self, payload: CategoryCreateRequest) -> CategoryResponse:
        existing = await self.repo.get_category_by_slug(payload.slug)
        if existing:
            raise ConflictException(f"Kategori dengan slug '{payload.slug}' sudah ada.")

        cat = await self.repo.create_category(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            icon_url=payload.icon_url,
        )
        await self.commit()
        return CategoryResponse.model_validate(cat)

    async def update_category(self, category_id: str, payload: CategoryUpdateRequest) -> CategoryResponse:
        cat = await self.repo.get_category_by_id(category_id)
        if not cat:
            raise NotFoundException("Kategori tidak ditemukan.")

        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()

        updated = await self.repo.update_category(category_id, **update_data)
        await self.commit()
        return CategoryResponse.model_validate(updated)

    async def delete_category(self, category_id: str) -> None:
        cat = await self.repo.get_category_by_id(category_id)
        if not cat:
            raise NotFoundException("Kategori tidak ditemukan.")
        await self.repo.delete_category(category_id)
        await self.commit()

    # ==========================================
    # 3. Product Service
    # ==========================================

    async def get_products_list(
        self,
        page: int = 1,
        limit: int = 12,
        search: Optional[str] = None,
        category_slug: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_active: Optional[bool] = True,
        sort_by: str = "newest",
    ) -> PaginatedProductsResponse:
        items, total = await self.repo.get_products_paginated(
            page=page,
            limit=limit,
            search=search,
            category_slug=category_slug,
            is_featured=is_featured,
            is_active=is_active,
            sort_by=sort_by,
        )

        item_responses = []
        for p in items:
            cat_resp = CategoryResponse.model_validate(p.category) if p.category else None
            item_responses.append(
                ProductListItemResponse(
                    id=p.id,
                    category=cat_resp,
                    name=p.name,
                    slug=p.slug,
                    short_description=p.short_description,
                    banner_image_url=p.banner_image_url,
                    thumbnail_url=p.thumbnail_url,
                    base_price=p.base_price,
                    discount_price=p.discount_price,
                    is_featured=p.is_featured,
                    is_active=p.is_active,
                    variants_count=len(p.variants) if p.variants else 0,
                    created_at=p.created_at,
                )
            )

        pagination = self.paginate(items=items, total=total, page=page, limit=limit)
        return PaginatedProductsResponse(
            items=item_responses,
            meta=PaginationMeta(**pagination["meta"]),
        )

    async def get_product_by_slug(self, slug: str) -> ProductDetailResponse:
        product = await self.repo.get_product_by_slug(slug)
        if not product:
            raise NotFoundException("Produk tidak ditemukan.")
        return ProductDetailResponse.model_validate(product)

    async def get_product_by_id(self, product_id: str) -> ProductDetailResponse:
        product = await self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException("Produk tidak ditemukan.")
        return ProductDetailResponse.model_validate(product)

    async def create_product(self, payload: ProductCreateRequest) -> ProductDetailResponse:
        existing = await self.repo.get_product_by_slug(payload.slug)
        if existing:
            raise ConflictException(f"Produk dengan slug '{payload.slug}' sudah ada.")

        if payload.category_id:
            cat = await self.repo.get_category_by_id(payload.category_id)
            if not cat:
                raise NotFoundException("Kategori yang dipilih tidak valid.")

        # Cek SKU unik untuk setiap varian
        for v in payload.variants:
            existing_sku = await self.repo.get_variant_by_sku(v.sku)
            if existing_sku:
                raise ConflictException(f"SKU varian '{v.sku}' sudah digunakan pada produk lain.")

        product_data = {
            "category_id": payload.category_id,
            "name": payload.name.strip(),
            "slug": payload.slug.lower().strip(),
            "short_description": payload.short_description.strip() if payload.short_description else None,
            "description": payload.description.strip(),
            "banner_image_url": payload.banner_image_url,
            "thumbnail_url": payload.thumbnail_url,
            "gallery_images": payload.gallery_images,
            "base_price": payload.base_price,
            "discount_price": payload.discount_price,
            "is_featured": payload.is_featured,
            "is_active": payload.is_active,
            "meta_title": payload.meta_title,
            "meta_description": payload.meta_description,
        }

        variants_data = [v.model_dump() for v in payload.variants]
        product = await self.repo.create_product(product_data, variants_data)
        await self.commit()
        return await self.get_product_by_id(product.id)

    async def update_product(self, product_id: str, payload: ProductUpdateRequest) -> ProductDetailResponse:
        product = await self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException("Produk tidak ditemukan.")

        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
        if "slug" in update_data:
            update_data["slug"] = update_data["slug"].lower().strip()
            existing = await self.repo.get_product_by_slug(update_data["slug"])
            if existing and existing.id != product_id:
                raise ConflictException("Slug tersebut sudah digunakan oleh produk lain.")

        updated = await self.repo.update_product(product_id, **update_data)
        await self.commit()
        return await self.get_product_by_id(updated.id)

    async def delete_product(self, product_id: str) -> None:
        product = await self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException("Produk tidak ditemukan.")

        await self.repo.soft_delete_product(product_id)
        await self.commit()

    # ==========================================
    # 4. Variant Service
    # ==========================================

    async def add_variant(self, product_id: str, payload: VariantCreateRequest) -> VariantResponse:
        product = await self.repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException("Produk induk tidak ditemukan.")

        existing_sku = await self.repo.get_variant_by_sku(payload.sku)
        if existing_sku:
            raise ConflictException(f"SKU '{payload.sku}' sudah digunakan.")

        variant = await self.repo.create_variant(product_id, payload.model_dump())
        await self.commit()
        return VariantResponse.model_validate(variant)

    async def update_variant(self, variant_id: str, payload: VariantUpdateRequest) -> VariantResponse:
        variant = await self.repo.get_variant_by_id(variant_id)
        if not variant:
            raise NotFoundException("Varian tidak ditemukan.")

        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "sku" in update_data:
            update_data["sku"] = update_data["sku"].upper().strip()
            existing_sku = await self.repo.get_variant_by_sku(update_data["sku"])
            if existing_sku and existing_sku.id != variant_id:
                raise ConflictException(f"SKU '{update_data['sku']}' sudah dipakai varian lain.")

        updated = await self.repo.update_variant(variant_id, **update_data)
        await self.commit()
        return VariantResponse.model_validate(updated)

    async def delete_variant(self, variant_id: str) -> None:
        variant = await self.repo.get_variant_by_id(variant_id)
        if not variant:
            raise NotFoundException("Varian tidak ditemukan.")

        await self.repo.delete_variant(variant_id)
        await self.commit()
