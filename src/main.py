import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config.settings import settings
from src.config.database import engine, async_session_factory
from src.core.database_base import Base
from src.core.middleware import setup_middlewares
from src.core.exceptions import register_exception_handlers
from src.modules.auth import auth_router
from src.modules.users import users_router
from src.modules.products import products_router
from src.modules.orders import orders_router
from src.modules.payments import payments_router
from src.modules.auth.auth_repository import AuthRepository

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inisialisasi skema tabel & seed default roles & permissions
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified/created successfully.")

        # Seed initial Dynamic RBAC (Superadmin, Admin, Staff, User + Permissions)
        async with async_session_factory() as session:
            repo = AuthRepository(session)
            await repo.seed_initial_rbac_if_empty()
            await session.commit()
        logger.info("Initial roles and permissions checked/seeded.")
    except Exception as e:
        logger.warning(f"Database initialization warning (DB server might be offline during build): {str(e)}")

    yield

    # Shutdown: Tutup koneksi engine
    await engine.dispose()
    logger.info("Database engine connection pool closed.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API Haisen Official Store - Digital Products & Services",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 1. Registrasi Middleware (CORS, Logging, Timing, Gzip)
setup_middlewares(app)

# 2. Registrasi Global Exception Handlers
register_exception_handlers(app)

# 3. Registrasi Module Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payments_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "success": True,
        "message": f"Selamat datang di API {settings.APP_NAME}",
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
    }
