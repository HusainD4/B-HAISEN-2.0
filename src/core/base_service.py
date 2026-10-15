import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import AppException

logger = logging.getLogger("base_service")


class BaseService:
    """
    Base Class berorientasi objek (OOP) untuk seluruh Service Layer.
    Mengelola transaksi database, logging seragam, dan helper kalkulasi umum.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def commit(self) -> None:
        """Melakukan commit transaksi dengan penanganan rollback jika gagal."""
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Gagal melakukan commit database: {str(e)}")
            raise AppException(f"Terjadi kegagalan saat menyimpan data: {str(e)}")

    async def rollback(self) -> None:
        """Melakukan rollback manual transaksi saat terjadi error bisnis."""
        await self.db.rollback()

    async def refresh(self, instance: Any) -> None:
        """Memuat ulang attribute instance dari database."""
        await self.db.refresh(instance)

    @staticmethod
    def paginate(items: List[Any], total: int, page: int, limit: int) -> Dict[str, Any]:
        """
        Helper standard format paginasi list data.
        """
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "items": items,
            "meta": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }
