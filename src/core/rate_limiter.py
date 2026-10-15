import time
import functools
from collections import defaultdict
from typing import Dict, List, Callable
from fastapi import Request
from src.core.exceptions import RateLimitException


class InMemoryRateLimiter:
    """
    In-memory Sliding Window Rate Limiter untuk memproteksi endpoint kritis
    (seperti login, registrasi, webhook) dari serangan brute-force dan DDoS.
    """

    def __init__(self):
        # Struktur: { "client_ip:endpoint": [timestamp1, timestamp2, ...] }
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds

        # Bersihkan timestamp di luar window waktu
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True


limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60) -> Callable:
    """
    Decorator untuk membatasi frekuensi request ke endpoint tertentu.
    Contoh:
    @router.post("/login")
    @rate_limit(max_requests=5, window_seconds=60)
    async def login(request: Request, ...):
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Mencari objek Request dari argumen fungsi
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                client_ip = request.client.host if request.client else "unknown"
                endpoint = request.url.path
                key = f"{client_ip}:{endpoint}"

                if not limiter.is_allowed(key, max_requests, window_seconds):
                    raise RateLimitException(
                        f"Batas permintaan tercapai ({max_requests} req / {window_seconds}s). "
                        "Silakan coba beberapa saat lagi."
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
