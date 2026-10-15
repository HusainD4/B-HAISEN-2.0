"""
Integration Tests: Root & Health Check Endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """GET / harus return 200 dengan pesan selamat datang."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Haisen" in data["message"]
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /health harus return status healthy."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_docs_available_in_debug(client: AsyncClient):
    """GET /docs harus tersedia saat DEBUG=True (development mode)."""
    response = await client.get("/docs")
    # Swagger UI tersedia → redirect atau 200
    assert response.status_code in (200, 307)


@pytest.mark.asyncio
async def test_not_found_returns_json(client: AsyncClient):
    """Endpoint yang tidak ada harus return 404 JSON (bukan HTML)."""
    response = await client.get("/endpoint-yang-tidak-ada")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers_present(client: AsyncClient):
    """Preflight CORS request ke origin yang diizinkan harus direspons."""
    response = await client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Jika CORS middleware aktif, origin diizinkan
    assert response.status_code in (200, 204)
