"""
Test fixtures dan konfigurasi global untuk semua test.
Menggunakan SQLite async in-memory agar tidak memerlukan database PostgreSQL nyata.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.database_base import Base
from src.config.database import get_db
from src.main import app


# ── Test Database (SQLite async in-memory) ────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Event loop scope ──────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    """Gunakan satu event loop untuk seluruh sesi test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ── Setup & Teardown Database ─────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Buat semua tabel sebelum sesi test, hapus setelah selesai."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    """Fixture session database dengan rollback otomatis setelah setiap test."""
    async with TestSessionFactory() as session:
        yield session
        await session.rollback()


# ── Override FastAPI DB dependency ────────────────────────────────────────────
@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:
    """
    HTTP test client async (HTTPX) dengan DB di-override ke SQLite in-memory.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Utility Fixtures ──────────────────────────────────────────────────────────
@pytest.fixture()
def superadmin_token(client) -> str:
    """
    Placeholder: return test JWT token untuk role superadmin.
    Ganti dengan proses login nyata ke endpoint /auth/login.
    """
    from src.core.security import create_access_token
    return create_access_token(subject="test-superadmin-id", role="superadmin")


@pytest.fixture()
def admin_token() -> str:
    from src.core.security import create_access_token
    return create_access_token(subject="test-admin-id", role="admin")


@pytest.fixture()
def user_token() -> str:
    from src.core.security import create_access_token
    return create_access_token(subject="test-user-id", role="user")
