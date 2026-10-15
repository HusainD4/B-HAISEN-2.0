import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.settings import settings

logger = logging.getLogger("middleware")


class RequestTimingAndLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware untuk mengukur waktu eksekusi request dan mencatat log akses HTTP.
    Menambahkan custom header 'X-Process-Time'.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        
        # Logging ringkas akses endpoint
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Waktu: {process_time * 1000:.2f}ms"
        )
        return response


def setup_middlewares(app: FastAPI):
    """
    Registrasi seluruh middleware ke aplikasi FastAPI.
    """
    # 1. Timing & Request Logging
    app.add_middleware(RequestTimingAndLoggingMiddleware)

    # 2. Gzip Compression (untuk response > 1KB)
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # 3. CORS Middleware
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )
