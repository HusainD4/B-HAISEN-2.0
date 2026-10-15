from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.dependencies import (
    get_current_user,
    CurrentUser,
    require_permissions,
    require_roles,
    oauth2_scheme,
)
from src.modules.orders.order_service import OrderService
from src.modules.orders.order_schema import (
    CartResponse,
    CartItemAddRequest,
    CartItemUpdateRequest,
    CheckoutRequest,
    DirectBuyRequest,
    OrderDetailResponse,
    PaginatedOrdersResponse,
)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders & Cart Management"])


# ==========================================
# 1. Keranjang Belanja (Database Stored)
# ==========================================

@router.get(
    "/cart",
    response_model=CartResponse,
    summary="Ambil Isi Keranjang Belanja Pengguna",
)
async def get_my_cart(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.get_user_cart(current_user.id)


@router.post(
    "/cart",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah Varian Produk ke Keranjang Belanja",
)
async def add_item_to_cart(
    payload: CartItemAddRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.add_to_cart(current_user.id, payload)


@router.put(
    "/cart/{item_id}",
    response_model=CartResponse,
    summary="Ubah Jumlah/Kuantitas Item di Keranjang",
)
async def update_cart_item(
    item_id: str,
    payload: CartItemUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.update_cart_quantity(current_user.id, item_id, payload)


@router.delete(
    "/cart/{item_id}",
    response_model=CartResponse,
    summary="Hapus Item dari Keranjang Belanja",
)
async def remove_cart_item(
    item_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.remove_from_cart(current_user.id, item_id)


@router.delete(
    "/cart",
    response_model=CartResponse,
    summary="Kosongkan Seluruh Keranjang Belanja",
)
async def clear_cart(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.clear_cart(current_user.id)


# ==========================================
# 2. Checkout & Pemesanan (Direct Core API)
# ==========================================

@router.post(
    "/checkout",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout dari Keranjang Belanja (Instruksi QRIS / VA Langsung Non-Snap)",
)
async def checkout(
    payload: CheckoutRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.checkout_from_cart(
        user_id=current_user.id,
        user_email=current_user.email or "",
        user_name=current_user.email.split("@")[0] if current_user.email else "Pelanggan",
        payload=payload,
    )


@router.post(
    "/direct-buy",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Beli Langsung 1 Varian Produk (Instan Tanpa Keranjang)",
)
async def direct_buy(
    payload: DirectBuyRequest,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # Support checkout baik user terautentikasi maupun guest (asalkan email diisi)
    user_id = None
    user_email = None
    user_name = None

    if token:
        try:
            from src.core.security import decode_token
            decoded = decode_token(token)
            user_id = decoded.get("sub")
            user_email = decoded.get("email")
            user_name = decoded.get("name")
        except Exception:
            pass

    service = OrderService(db)
    return await service.direct_buy(
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
        payload=payload,
    )


@router.get(
    "/my-orders",
    response_model=PaginatedOrdersResponse,
    summary="Daftar Riwayat Pesanan Saya",
)
async def get_my_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.get_user_orders(user_id=current_user.id, page=page, limit=limit)


@router.get(
    "/{order_number}",
    response_model=OrderDetailResponse,
    summary="Ambil Detail Pesanan Beserta Instruksi Pembayaran QRIS / VA",
)
async def get_order_detail(
    order_number: str,
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.get_order_detail_by_number(order_number)


# ==========================================
# 3. Admin / Staff Order Management
# ==========================================

@router.get(
    "/admin/all",
    response_model=PaginatedOrdersResponse,
    summary="Daftar Seluruh Pesanan Toko (Admin / Finance / Staff)",
    dependencies=[Depends(require_permissions("order:read_all"))],
)
async def list_all_orders_for_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: pending, paid, expired, cancelled"),
    search: Optional[str] = Query(None, description="Cari No. Order, Nama, atau Email"),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.get_all_orders_admin(
        page=page,
        limit=limit,
        status=status,
        search=search,
    )
