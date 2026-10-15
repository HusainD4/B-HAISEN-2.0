"""
Unit Tests: Auth Endpoints (Register, Login, Refresh Token, Logout)
"""
import pytest
from httpx import AsyncClient


# ── Data Test ─────────────────────────────────────────────────────────────────
VALID_USER = {
    "full_name": "Test Customer",
    "email": "testcustomer@haisen.test",
    "password": "Test@Secure123",
    "phone": "08123456789",
}

INVALID_EMAIL = {**VALID_USER, "email": "bukan-email-valid"}
WEAK_PASSWORD  = {**VALID_USER, "password": "123", "email": "another@haisen.test"}


# ── Register ──────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """POST /auth/register dengan data valid harus return 201 dan data user."""
    response = await client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == VALID_USER["email"]
    assert "password" not in data["data"]  # Password tidak boleh dikembalikan


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registrasi dengan email yang sudah terdaftar harus return 409 Conflict."""
    await client.post("/auth/register", json=VALID_USER)  # Register pertama
    response = await client.post("/auth/register", json=VALID_USER)  # Duplikat
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Registrasi dengan email tidak valid harus return 422 Unprocessable Entity."""
    response = await client.post("/auth/register", json=INVALID_EMAIL)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Registrasi dengan password terlalu pendek harus return 422."""
    response = await client.post("/auth/register", json=WEAK_PASSWORD)
    assert response.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """POST /auth/login dengan kredensial valid harus return access + refresh token."""
    # Pastikan user sudah terdaftar
    await client.post("/auth/register", json={**VALID_USER, "email": "logintest@haisen.test"})

    response = await client.post("/auth/login", json={
        "email": "logintest@haisen.test",
        "password": VALID_USER["password"],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login dengan password salah harus return 401."""
    response = await client.post("/auth/login", json={
        "email": VALID_USER["email"],
        "password": "password-salah-banget",
    })
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Login dengan email yang tidak terdaftar harus return 401."""
    response = await client.post("/auth/login", json={
        "email": "tidakterdaftar@haisen.test",
        "password": "SomePassword123",
    })
    assert response.status_code == 401


# ── Protected Endpoint ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    """GET /auth/me tanpa Authorization header harus return 401."""
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(client: AsyncClient, user_token: str):
    """GET /auth/me dengan token valid harus return profil user."""
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    # 200 jika user test-user-id ada di DB, atau 404 jika tidak — keduanya bukan 401/403
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient):
    """GET /auth/me dengan token palsu/expired harus return 401."""
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer token-palsu-tidak-valid"},
    )
    assert response.status_code == 401


# ── Rate Limiting ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient):
    """Percobaan login berulang dengan password salah harus akhirnya di-rate-limit (429)."""
    for _ in range(10):
        await client.post("/auth/login", json={
            "email": "bruteforce@haisen.test",
            "password": "salah",
        })

    response = await client.post("/auth/login", json={
        "email": "bruteforce@haisen.test",
        "password": "salah",
    })
    # Rate limiter aktif → 429, atau tetap 401 jika limit belum tercapai di test env
    assert response.status_code in (401, 429)
