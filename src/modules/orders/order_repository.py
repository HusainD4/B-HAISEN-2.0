from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.orders.order_model import CartItem, Order, OrderItem
from src.modules.products.product_model import ProductVariant, Product


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================================
    # Cart Operations (DB Stored)
    # ==========================================

    async def get_user_cart(self, user_id: str) -> List[CartItem]:
        stmt = (
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_cart_item_by_variant(self, user_id: str, variant_id: str) -> Optional[CartItem]:
        stmt = select(CartItem).where(and_(CartItem.user_id == user_id, CartItem.variant_id == variant_id))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_cart_item_by_id(self, item_id: str, user_id: str) -> Optional[CartItem]:
        stmt = select(CartItem).where(and_(CartItem.id == item_id, CartItem.user_id == user_id))
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def add_to_cart(self, user_id: str, product_id: str, variant_id: str, quantity: int = 1) -> CartItem:
        existing = await self.get_cart_item_by_variant(user_id, variant_id)
        if existing:
            existing.quantity += quantity
            await self.db.flush()
            return existing

        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_cart_quantity(self, item_id: str, user_id: str, quantity: int) -> Optional[CartItem]:
        stmt = (
            update(CartItem)
            .where(and_(CartItem.id == item_id, CartItem.user_id == user_id))
            .values(quantity=quantity, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        return await self.get_cart_item_by_id(item_id, user_id)

    async def remove_from_cart(self, item_id: str, user_id: str) -> bool:
        stmt = delete(CartItem).where(and_(CartItem.id == item_id, CartItem.user_id == user_id))
        res = await self.db.execute(stmt)
        return res.rowcount > 0

    async def clear_user_cart(self, user_id: str) -> None:
        stmt = delete(CartItem).where(CartItem.user_id == user_id)
        await self.db.execute(stmt)

    # ==========================================
    # Order Operations
    # ==========================================

    async def create_order(self, order_data: dict, items_data: List[dict]) -> Order:
        order = Order(**order_data)
        self.db.add(order)
        await self.db.flush()

        for item_d in items_data:
            order_item = OrderItem(order_id=order.id, **item_d)
            self.db.add(order_item)

        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        stmt = select(Order).where(Order.order_number == order_number.strip())
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_user_orders(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Order], int]:
        filters = [Order.user_id == user_id]

        count_stmt = select(func.count(Order.id)).where(and_(*filters))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        offset = (page - 1) * limit
        stmt = (
            select(Order)
            .where(and_(*filters))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def get_all_orders_paginated(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        filters = []

        if status:
            filters.append(Order.status == status.lower().strip())

        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Order.order_number.ilike(pattern),
                    Order.customer_name.ilike(pattern),
                    Order.customer_email.ilike(pattern),
                )
            )

        count_stmt = select(func.count(Order.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        offset = (page - 1) * limit
        stmt = select(Order)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)

        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        paid_at: Optional[datetime] = None,
    ) -> Optional[Order]:
        update_data: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        if paid_at:
            update_data["paid_at"] = paid_at

        stmt = update(Order).where(Order.id == order_id).values(**update_data)
        await self.db.execute(stmt)
        return await self.get_order_by_id(order_id)
