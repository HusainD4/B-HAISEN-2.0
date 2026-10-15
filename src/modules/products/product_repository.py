from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.products.product_model import Product, ProductCategory, ProductVariant


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================================
    # Category Operations
    # ==========================================

    async def get_categories(self, active_only: bool = True) -> List[ProductCategory]:
        stmt = select(ProductCategory)
        if active_only:
            stmt = stmt.where(ProductCategory.is_active == True)
        stmt = stmt.order_by(ProductCategory.name.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_category_by_id(self, category_id: str) -> Optional[ProductCategory]:
        stmt = select(ProductCategory).where(ProductCategory.id == category_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_category_by_slug(self, slug: str) -> Optional[ProductCategory]:
        stmt = select(ProductCategory).where(ProductCategory.slug == slug.lower())
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def create_category(self, name: str, slug: str, description: Optional[str] = None, icon_url: Optional[str] = None) -> ProductCategory:
        cat = ProductCategory(
            name=name.strip(),
            slug=slug.lower().strip(),
            description=description.strip() if description else None,
            icon_url=icon_url,
            is_active=True,
        )
        self.db.add(cat)
        await self.db.flush()
        return cat

    async def update_category(self, category_id: str, **kwargs) -> Optional[ProductCategory]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = update(ProductCategory).where(ProductCategory.id == category_id).values(**kwargs)
        await self.db.execute(stmt)
        return await self.get_category_by_id(category_id)

    async def delete_category(self, category_id: str) -> bool:
        stmt = delete(ProductCategory).where(ProductCategory.id == category_id)
        res = await self.db.execute(stmt)
        return res.rowcount > 0

    # ==========================================
    # Product Operations
    # ==========================================

    async def get_products_paginated(
        self,
        page: int = 1,
        limit: int = 12,
        search: Optional[str] = None,
        category_slug: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_active: Optional[bool] = True,
        sort_by: str = "newest",
    ) -> Tuple[List[Product], int]:
        filters = [Product.is_deleted == False]

        if is_active is not None:
            filters.append(Product.is_active == is_active)

        if is_featured is not None:
            filters.append(Product.is_featured == is_featured)

        if category_slug:
            filters.append(Product.category.has(ProductCategory.slug == category_slug.lower()))

        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Product.name.ilike(pattern),
                    Product.short_description.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )

        # Count statement
        count_stmt = select(func.count(Product.id)).where(and_(*filters))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        # Query items
        offset = (page - 1) * limit
        stmt = select(Product).where(and_(*filters))

        if sort_by == "price_asc":
            stmt = stmt.order_by(Product.base_price.asc())
        elif sort_by == "price_desc":
            stmt = stmt.order_by(Product.base_price.desc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())

        stmt = stmt.offset(offset).limit(limit)
        items_res = await self.db.execute(stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def get_product_by_id(self, product_id: str) -> Optional[Product]:
        stmt = select(Product).where(and_(Product.id == product_id, Product.is_deleted == False))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_product_by_slug(self, slug: str) -> Optional[Product]:
        stmt = select(Product).where(and_(Product.slug == slug.lower(), Product.is_deleted == False))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def create_product(self, product_data: dict, variants_data: List[dict] = []) -> Product:
        product = Product(**product_data)
        self.db.add(product)
        await self.db.flush()

        for v_data in variants_data:
            variant = ProductVariant(product_id=product.id, **v_data)
            self.db.add(variant)

        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update_product(self, product_id: str, **kwargs) -> Optional[Product]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = update(Product).where(and_(Product.id == product_id, Product.is_deleted == False)).values(**kwargs)
        await self.db.execute(stmt)
        return await self.get_product_by_id(product_id)

    async def soft_delete_product(self, product_id: str) -> bool:
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        res = await self.db.execute(stmt)
        return res.rowcount > 0

    # ==========================================
    # Variant Operations
    # ==========================================

    async def get_variant_by_id(self, variant_id: str) -> Optional[ProductVariant]:
        stmt = select(ProductVariant).where(ProductVariant.id == variant_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_variant_by_sku(self, sku: str) -> Optional[ProductVariant]:
        stmt = select(ProductVariant).where(ProductVariant.sku == sku.upper().strip())
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def create_variant(self, product_id: str, variant_data: dict) -> ProductVariant:
        variant = ProductVariant(product_id=product_id, **variant_data)
        self.db.add(variant)
        await self.db.flush()
        return variant

    async def update_variant(self, variant_id: str, **kwargs) -> Optional[ProductVariant]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = update(ProductVariant).where(ProductVariant.id == variant_id).values(**kwargs)
        await self.db.execute(stmt)
        return await self.get_variant_by_id(variant_id)

    async def delete_variant(self, variant_id: str) -> bool:
        stmt = delete(ProductVariant).where(ProductVariant.id == variant_id)
        res = await self.db.execute(stmt)
        return res.rowcount > 0
