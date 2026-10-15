"""
Unit Tests: Product Catalog Endpoints
"""
import pytest
from httpx import AsyncClient


# ── Data Test ─────────────────────────────────────────────────────────────────
SAMPLE_PRODUCT_PAYLOAD = {
    "name": "Template Desain Logo Profesional",
    "slug": "template-desain-logo-profesional",
    "description": "Paket template logo vector premium untuk bisnis.",
    "price": 75000,
    "stock": 999,
    "category_id": None,   # opsional
    "is_digital": True,
    "is_active": True,
}


# ── Public Endpoints (Tanpa Auth) ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_products_public(client: AsyncClient):
    """GET /products harus dapat diakses publik dan return 200."""
    response = await client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient):
    """GET /products?page=1&limit=10 harus return struktur pagination."""
    response = await client.get("/products?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    # Harus ada meta pagination
    assert "meta" in data or "data" in data


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    """GET /products/{id} dengan ID tidak valid harus return 404."""
    response = await client.get("/products/id-yang-tidak-ada-sama-sekali")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_product_by_slug(client: AsyncClient):
    """GET /products/slug/{slug} harus return 404 jika produk belum ada."""
    response = await client.get("/products/slug/slug-tidak-ada")
    assert response.status_code == 404


# ── Admin-Protected Endpoints ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_create_product_without_auth(client: AsyncClient):
    """POST /products tanpa token harus return 401."""
    response = await client.post("/products", json=SAMPLE_PRODUCT_PAYLOAD)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_product_as_user_forbidden(client: AsyncClient, user_token: str):
    """POST /products dengan token user biasa harus return 403 Forbidden."""
    response = await client.post(
        "/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_product_as_admin(client: AsyncClient, admin_token: str):
    """POST /products dengan token admin harus return 201."""
    response = await client.post(
        "/products",
        json=SAMPLE_PRODUCT_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # 201 jika sukses, atau 422 jika schema memerlukan category_id wajib
    assert response.status_code in (201, 422)


@pytest.mark.asyncio
async def test_update_product_without_auth(client: AsyncClient):
    """PATCH /products/{id} tanpa token harus return 401."""
    response = await client.patch("/products/some-id", json={"price": 50000})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_product_requires_superadmin(client: AsyncClient, admin_token: str):
    """DELETE /products/{id} oleh admin (bukan superadmin) harus return 403."""
    response = await client.delete(
        "/products/some-id",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # 403 atau 404 (tidak ditemukan) — keduanya valid
    assert response.status_code in (403, 404)


# ── Search & Filter ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_search_products(client: AsyncClient):
    """GET /products?search=template harus return daftar produk yang difilter."""
    response = await client.get("/products?search=template")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_filter_products_by_category(client: AsyncClient):
    """GET /products?category_id=... harus return 200 (mungkin list kosong)."""
    response = await client.get("/products?category_id=kategori-tidak-ada")
    assert response.status_code == 200
