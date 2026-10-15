import secrets
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_service import BaseService
from src.core.exceptions import (
    NotFoundException,
    BadRequestException,
)
from src.modules.orders.order_repository import OrderRepository
from src.modules.products.product_repository import ProductRepository
from src.modules.payments.payment_service import PaymentService
from src.modules.orders.order_schema import (
    CartItemResponse,
    CartResponse,
    CartItemAddRequest,
    CartItemUpdateRequest,
    CheckoutRequest,
    DirectBuyRequest,
    OrderDetailResponse,
    OrderSummaryResponse,
    OrderItemResponse,
    PaymentInstructionResponse,
    PaginatedOrdersResponse,
)
from src.modules.users.user_schema import PaginationMeta


class OrderService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.payment_service = PaymentService(db)

    @staticmethod
    def _generate_order_number() -> str:
        """Format nomor order: HSN-YYYYMMDD-XXXX (unik & terstruktur)."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_str = secrets.token_hex(3).upper()
        return f"HSN-{date_str}-{rand_str}"

    # ==========================================
    # 1. Cart Service (Database Stored)
    # ==========================================

    async def get_user_cart(self, user_id: str) -> CartResponse:
        cart_items = await self.repo.get_user_cart(user_id)

        items_resp: List[CartItemResponse] = []
        total_amount = 0
        total_items = 0

        for item in cart_items:
            variant = item.variant
            product = item.product

            if not variant or not product or not product.is_active or not variant.is_active:
                continue

            current_price = variant.discount_price if variant.discount_price else variant.price
            subtotal = current_price * item.quantity
            total_amount += subtotal
            total_items += item.quantity

            items_resp.append(
                CartItemResponse(
                    id=item.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    product_name=product.name,
                    product_slug=product.slug,
                    variant_name=variant.name,
                    variant_image_url=variant.variant_image_url or product.thumbnail_url,
                    price=current_price,
                    quantity=item.quantity,
                    subtotal=subtotal,
                    is_available=True,
                )
            )

        return CartResponse(
            items=items_resp,
            total_items=total_items,
            total_amount=total_amount,
        )

    async def add_to_cart(self, user_id: str, payload: CartItemAddRequest) -> CartResponse:
        variant = await self.product_repo.get_variant_by_id(payload.variant_id)
        if not variant or not variant.is_active:
            raise NotFoundException("Varian produk tidak ditemukan atau sedang tidak aktif.")

        await self.repo.add_to_cart(
            user_id=user_id,
            product_id=variant.product_id,
            variant_id=variant.id,
            quantity=payload.quantity,
        )
        await self.commit()
        return await self.get_user_cart(user_id)

    async def update_cart_quantity(self, user_id: str, item_id: str, payload: CartItemUpdateRequest) -> CartResponse:
        item = await self.repo.get_cart_item_by_id(item_id, user_id)
        if not item:
            raise NotFoundException("Item keranjang tidak ditemukan.")

        await self.repo.update_cart_quantity(item_id, user_id, payload.quantity)
        await self.commit()
        return await self.get_user_cart(user_id)

    async def remove_from_cart(self, user_id: str, item_id: str) -> CartResponse:
        item = await self.repo.get_cart_item_by_id(item_id, user_id)
        if not item:
            raise NotFoundException("Item keranjang tidak ditemukan.")

        await self.repo.remove_from_cart(item_id, user_id)
        await self.commit()
        return await self.get_user_cart(user_id)

    async def clear_cart(self, user_id: str) -> CartResponse:
        await self.repo.clear_user_cart(user_id)
        await self.commit()
        return CartResponse(items=[], total_items=0, total_amount=0)

    # ==========================================
    # 2. Checkout & Order Service
    # ==========================================

    async def checkout_from_cart(
        self,
        user_id: str,
        user_email: str,
        user_name: str,
        payload: CheckoutRequest,
    ) -> OrderDetailResponse:
        """
        Checkout produk dari keranjang belanja user.
        Menghitung harga riil dari database (Anti-Tampering) dan membuat tagihan pembayaran langsung.
        """
        cart = await self.get_user_cart(user_id)
        if not cart.items:
            raise BadRequestException("Keranjang belanja Anda kosong.")

        order_number = self._generate_order_number()
        customer_name = payload.customer_name or user_name
        customer_email = payload.customer_email or user_email

        # Susun item pesanan
        order_items_data = []
        for c in cart.items:
            variant = await self.product_repo.get_variant_by_id(c.variant_id)
            order_items_data.append({
                "product_id": c.product_id,
                "variant_id": c.variant_id,
                "product_name": c.product_name,
                "variant_name": c.variant_name,
                "variant_image_url": c.variant_image_url,
                "price": c.price,
                "quantity": c.quantity,
                "subtotal": c.subtotal,
                "license_type": variant.license_type if variant else "standard",
                "digital_file_key": variant.digital_file_key if variant else None,
            })

        total_amount = cart.total_amount + payload.shipping_cost

        order_data = {
            "order_number": order_number,
            "user_id": user_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": payload.customer_phone,
            "total_amount": total_amount,
            "status": "pending",
            "payment_method": f"{payload.payment_method}_{payload.bank}" if payload.bank else payload.payment_method,
            "notes": payload.notes,
            "shipping_address": payload.shipping_address,
            "shipping_province": payload.shipping_province,
            "shipping_city": payload.shipping_city,
            "shipping_district": payload.shipping_district,
            "shipping_postal_code": payload.shipping_postal_code,
            "shipping_cost": payload.shipping_cost,
            "courier": payload.courier,
            "courier_service": payload.courier_service,
        }

        # Simpan pesanan ke database
        order = await self.repo.create_order(order_data, order_items_data)

        # Kosongkan keranjang belanja
        await self.repo.clear_user_cart(user_id)

        # Proses Charge langsung ke Midtrans Core API (Non-Snap)
        await self.payment_service.initiate_direct_charge(
            order=order,
            payment_method=payload.payment_method,
            bank=payload.bank,
        )

        await self.commit()
        return await self.get_order_detail_by_id(order.id)

    async def direct_buy(
        self,
        user_id: Optional[str],
        user_email: Optional[str],
        user_name: Optional[str],
        payload: DirectBuyRequest,
    ) -> OrderDetailResponse:
        """
        Beli langsung (Instant Checkout) untuk satu produk/varian tanpa melalui keranjang.
        """
        variant = await self.product_repo.get_variant_by_id(payload.variant_id)
        if not variant or not variant.is_active or not variant.product or not variant.product.is_active:
            raise NotFoundException("Varian produk tidak ditemukan atau tidak tersedia.")

        customer_name = payload.customer_name or user_name or "Pelanggan"
        customer_email = payload.customer_email or user_email
        if not customer_email:
            raise BadRequestException("Email pembeli wajib diisi untuk pengiriman lisensi/file digital.")

        price = variant.discount_price if variant.discount_price else variant.price
        subtotal = price * payload.quantity
        order_number = self._generate_order_number()

        order_items_data = [{
            "product_id": variant.product_id,
            "variant_id": variant.id,
            "product_name": variant.product.name,
            "variant_name": variant.name,
            "variant_image_url": variant.variant_image_url or variant.product.thumbnail_url,
            "price": price,
            "quantity": payload.quantity,
            "subtotal": subtotal,
            "license_type": variant.license_type,
            "digital_file_key": variant.digital_file_key,
        }]

        total_amount = subtotal + payload.shipping_cost

        order_data = {
            "order_number": order_number,
            "user_id": user_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": payload.customer_phone,
            "total_amount": total_amount,
            "status": "pending",
            "payment_method": f"{payload.payment_method}_{payload.bank}" if payload.bank else payload.payment_method,
            "notes": payload.notes,
            "shipping_address": payload.shipping_address,
            "shipping_province": payload.shipping_province,
            "shipping_city": payload.shipping_city,
            "shipping_district": payload.shipping_district,
            "shipping_postal_code": payload.shipping_postal_code,
            "shipping_cost": payload.shipping_cost,
            "courier": payload.courier,
            "courier_service": payload.courier_service,
        }

        order = await self.repo.create_order(order_data, order_items_data)

        # Proses Charge langsung ke Midtrans Core API (Non-Snap)
        await self.payment_service.initiate_direct_charge(
            order=order,
            payment_method=payload.payment_method,
            bank=payload.bank,
        )

        await self.commit()
        return await self.get_order_detail_by_id(order.id)

    async def get_order_detail_by_id(self, order_id: str) -> OrderDetailResponse:
        order = await self.repo.get_order_by_id(order_id)
        if not order:
            raise NotFoundException("Pesanan tidak ditemukan.")

        items_resp = []
        for it in order.items:
            items_resp.append(
                OrderItemResponse(
                    id=it.id,
                    product_id=it.product_id,
                    variant_id=it.variant_id,
                    product_name=it.product_name,
                    variant_name=it.variant_name,
                    variant_image_url=it.variant_image_url,
                    price=it.price,
                    quantity=it.quantity,
                    subtotal=it.subtotal,
                    license_type=it.license_type,
                    has_digital_file=bool(it.digital_file_key),
                )
            )

        payment_resp = None
        if order.payment:
            payment_resp = PaymentInstructionResponse(
                payment_type=order.payment.payment_type,
                status=order.payment.transaction_status,
                gross_amount=order.payment.gross_amount,
                qr_string=order.payment.qr_string,
                qr_code_url=order.payment.qr_code_url,
                bank=order.payment.bank,
                va_number=order.payment.va_number,
                bill_key=order.payment.bill_key,
                biller_code=order.payment.biller_code,
                expiry_time=order.payment.expiry_time,
            )

        return OrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            total_amount=order.total_amount,
            status=order.status,
            payment_method=order.payment_method,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            notes=order.notes,
            paid_at=order.paid_at,
            items=items_resp,
            payment=payment_resp,
            created_at=order.created_at,
        )

    async def get_order_detail_by_number(self, order_number: str) -> OrderDetailResponse:
        order = await self.repo.get_order_by_number(order_number)
        if not order:
            raise NotFoundException("Pesanan tidak ditemukan.")
        return await self.get_order_detail_by_id(order.id)

    async def get_user_orders(self, user_id: str, page: int = 1, limit: int = 10) -> PaginatedOrdersResponse:
        items, total = await self.repo.get_user_orders(user_id=user_id, page=page, limit=limit)
        summaries = [
            OrderSummaryResponse(
                id=o.id,
                order_number=o.order_number,
                total_amount=o.total_amount,
                status=o.status,
                payment_method=o.payment_method,
                customer_name=o.customer_name,
                items_count=len(o.items) if o.items else 0,
                paid_at=o.paid_at,
                created_at=o.created_at,
            )
            for o in items
        ]
        pagination = self.paginate(items=items, total=total, page=page, limit=limit)
        return PaginatedOrdersResponse(items=summaries, meta=PaginationMeta(**pagination["meta"]))

    async def get_all_orders_admin(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedOrdersResponse:
        items, total = await self.repo.get_all_orders_paginated(
            page=page,
            limit=limit,
            status=status,
            search=search,
        )
        summaries = [
            OrderSummaryResponse(
                id=o.id,
                order_number=o.order_number,
                total_amount=o.total_amount,
                status=o.status,
                payment_method=o.payment_method,
                customer_name=o.customer_name,
                items_count=len(o.items) if o.items else 0,
                paid_at=o.paid_at,
                created_at=o.created_at,
            )
            for o in items
        ]
        pagination = self.paginate(items=items, total=total, page=page, limit=limit)
        return PaginatedOrdersResponse(items=summaries, meta=PaginationMeta(**pagination["meta"]))
