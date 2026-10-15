"""
Alembic Environment Configuration
Menggunakan SQLAlchemy async engine agar kompatibel dengan asyncpg + SQLAlchemy 2.0.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# ── Import semua model agar Alembic bisa detect skema ─────────────────────────
# Pastikan semua model diimport sebelum Base.metadata dipakai.
from src.core.database_base import Base  # noqa: F401 — Base metadata
from src.config.settings import settings

# Import semua modul ORM agar tabel terdaftar ke Base.metadata
import src.modules.auth.auth_model          # noqa: F401
import src.modules.users.user_model         # noqa: F401
import src.modules.products.product_model   # noqa: F401
import src.modules.orders.order_model       # noqa: F401
import src.modules.payments.payment_model   # noqa: F401

# ── Alembic Config Object ──────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url dari .env (settings) agar tidak hardcode di alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup logging dari alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData target untuk autogenerate
target_metadata = Base.metadata


# ── Offline Mode (tanpa koneksi DB aktif, hanya generate SQL script) ──────────
def run_migrations_offline() -> None:
    """
    Jalankan migrasi dalam mode 'offline'.
    Menghasilkan SQL script yang bisa dieksekusi manual ke database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # Deteksi perubahan tipe kolom
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online Mode (koneksi DB aktif, async) ─────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Inisialisasi async engine dan jalankan migrasi secara async (asyncpg).
    """
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,  # Tidak pakai connection pool saat migrasi
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point untuk mode online (asyncio event loop)."""
    asyncio.run(run_async_migrations())


# ── Dispatch ──────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
