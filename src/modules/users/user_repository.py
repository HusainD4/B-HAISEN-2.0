from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.auth.auth_model import User, Role, Permission, RolePermission


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_users_paginated(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        role_slug: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        filters = [User.is_deleted == False]

        if search:
            search_pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                    User.phone.ilike(search_pattern),
                )
            )

        if role_slug:
            filters.append(User.role.has(Role.slug == role_slug.lower()))

        if is_active is not None:
            filters.append(User.is_active == is_active)

        # Count total
        count_stmt = select(func.count(User.id)).where(and_(*filters))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one() or 0

        # Query items
        offset = (page - 1) * limit
        stmt = (
            select(User)
            .where(and_(*filters))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items_res = await self.db.execute(stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).where(and_(User.id == user_id, User.is_deleted == False))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(and_(User.email == email.lower(), User.is_deleted == False))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = (
            update(User)
            .where(and_(User.id == user_id, User.is_deleted == False))
            .values(**kwargs)
        )
        await self.db.execute(stmt)
        return await self.get_user_by_id(user_id)

    async def soft_delete_user(self, user_id: str) -> bool:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    # ==========================================
    # Dynamic Role & Permission Operations
    # ==========================================

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        stmt = select(Role).where(Role.id == role_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_role_by_slug(self, slug: str) -> Optional[Role]:
        stmt = select(Role).where(Role.slug == slug.lower())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_roles(self) -> List[Role]:
        stmt = select(Role).order_by(Role.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_role(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        is_system: bool = False,
    ) -> Role:
        role = Role(
            name=name.strip(),
            slug=slug.lower().strip(),
            description=description.strip() if description else None,
            is_system=is_system,
        )
        self.db.add(role)
        await self.db.flush()
        return role

    async def update_role(self, role_id: str, **kwargs) -> Optional[Role]:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = update(Role).where(Role.id == role_id).values(**kwargs)
        await self.db.execute(stmt)
        return await self.get_role_by_id(role_id)

    async def delete_role(self, role_id: str) -> bool:
        stmt = delete(Role).where(and_(Role.id == role_id, Role.is_system == False))
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def sync_role_permissions(self, role_id: str, permission_ids: List[str]) -> None:
        # Hapus asosiasi permission lama
        await self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))

        # Masukkan asosiasi baru
        for pid in permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=pid))
        await self.db.flush()

    async def get_all_permissions(self) -> List[Permission]:
        stmt = select(Permission).order_by(Permission.module.asc(), Permission.code.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
