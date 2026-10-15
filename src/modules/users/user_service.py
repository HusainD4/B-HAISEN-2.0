from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.base_service import BaseService
from src.core.security import hash_password
from src.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    ConflictException,
)
from src.modules.users.user_repository import UserRepository
from src.modules.users.user_schema import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserAdminCreateRequest,
    UserAdminUpdateRequest,
    PaginatedUsersResponse,
    PaginationMeta,
    RoleCreateRequest,
    RoleUpdateRequest,
)
from src.modules.auth.auth_schema import RoleResponse, PermissionResponse


class UserService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = UserRepository(db)

    async def get_profile(self, user_id: str) -> UserProfileResponse:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Pengguna tidak ditemukan.")
        return UserProfileResponse.model_validate(user)

    async def update_profile(self, user_id: str, payload: UserProfileUpdateRequest) -> UserProfileResponse:
        update_data = {}
        if payload.full_name is not None:
            update_data["full_name"] = payload.full_name.strip()
        if payload.phone is not None:
            update_data["phone"] = payload.phone.strip()
        if payload.address is not None:
            update_data["address"] = payload.address.strip()
        if payload.province is not None:
            update_data["province"] = payload.province.strip()
        if payload.city is not None:
            update_data["city"] = payload.city.strip()
        if payload.district is not None:
            update_data["district"] = payload.district.strip()
        if payload.postal_code is not None:
            update_data["postal_code"] = payload.postal_code.strip()

        if not update_data:
            return await self.get_profile(user_id)

        user = await self.repo.update_user(user_id, **update_data)
        await self.commit()
        return UserProfileResponse.model_validate(user)

    async def get_users_list(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        role_slug: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedUsersResponse:
        items, total = await self.repo.get_users_paginated(
            page=page,
            limit=limit,
            search=search,
            role_slug=role_slug,
            is_active=is_active,
        )

        pagination = self.paginate(items=items, total=total, page=page, limit=limit)
        return PaginatedUsersResponse(
            items=[UserProfileResponse.model_validate(u) for u in items],
            meta=PaginationMeta(**pagination["meta"]),
        )

    async def get_user_detail(self, user_id: str) -> UserProfileResponse:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("Data user tidak ditemukan.")
        return UserProfileResponse.model_validate(user)

    async def admin_create_user(self, payload: UserAdminCreateRequest, actor_role: str) -> UserProfileResponse:
        existing = await self.repo.get_user_by_email(payload.email)
        if existing:
            raise ConflictException("Email tersebut sudah terdaftar.")

        role = await self.repo.get_role_by_slug(payload.role_slug)
        if not role:
            raise NotFoundException(f"Role dengan slug '{payload.role_slug}' tidak ditemukan.")

        # Hanya Superadmin yang berhak membuat user ber-role Superadmin atau Admin
        if role.slug in ["superadmin", "admin"] and actor_role.lower() != "superadmin":
            raise ForbiddenException("Hanya Superadmin yang memiliki izin membuat akun admin/superadmin.")

        from src.modules.auth.auth_repository import AuthRepository
        auth_repo = AuthRepository(self.db)
        hashed_pwd = hash_password(payload.password)

        new_user = await auth_repo.create_user(
            email=payload.email,
            password_hash=hashed_pwd,
            full_name=payload.full_name,
            phone=payload.phone,
            address=payload.address,
            province=payload.province,
            city=payload.city,
            district=payload.district,
            postal_code=payload.postal_code,
            role_id=role.id,
        )
        if not payload.is_active:
            await self.repo.update_user(new_user.id, is_active=False)

        await self.commit()
        return await self.get_user_detail(new_user.id)

    async def admin_update_user(self, user_id: str, payload: UserAdminUpdateRequest, actor_role: str) -> UserProfileResponse:
        target_user = await self.repo.get_user_by_id(user_id)
        if not target_user:
            raise NotFoundException("User tidak ditemukan.")

        target_role = target_user.role.slug if target_user.role else "user"
        if target_role == "superadmin" and actor_role.lower() != "superadmin":
            raise ForbiddenException("Anda tidak berhak mengedit akun Superadmin.")

        update_data = {}
        if payload.full_name is not None:
            update_data["full_name"] = payload.full_name.strip()
        if payload.phone is not None:
            update_data["phone"] = payload.phone.strip()
        if payload.address is not None:
            update_data["address"] = payload.address.strip()
        if payload.province is not None:
            update_data["province"] = payload.province.strip()
        if payload.city is not None:
            update_data["city"] = payload.city.strip()
        if payload.district is not None:
            update_data["district"] = payload.district.strip()
        if payload.postal_code is not None:
            update_data["postal_code"] = payload.postal_code.strip()
        if payload.is_active is not None:
            update_data["is_active"] = payload.is_active
        if payload.role_id is not None:
            role = await self.repo.get_role_by_id(payload.role_id)
            if not role:
                raise NotFoundException("Role yang dipilih tidak ditemukan.")
            if role.slug == "superadmin" and actor_role.lower() != "superadmin":
                raise ForbiddenException("Hanya Superadmin yang dapat memberikan role Superadmin.")
            update_data["role_id"] = role.id

        user = await self.repo.update_user(user_id, **update_data)
        await self.commit()
        return UserProfileResponse.model_validate(user)

    async def change_user_role(self, user_id: str, new_role_id: str, actor_role: str) -> UserProfileResponse:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan.")

        target_role_slug = user.role.slug if user.role else "user"
        if target_role_slug == "superadmin" and actor_role.lower() != "superadmin":
            raise ForbiddenException("Hanya Superadmin yang berhak mengganti role akun Superadmin.")

        new_role = await self.repo.get_role_by_id(new_role_id)
        if not new_role:
            raise NotFoundException("Role baru tidak ditemukan.")

        if new_role.slug == "superadmin" and actor_role.lower() != "superadmin":
            raise ForbiddenException("Hanya Superadmin yang berhak menugaskan role Superadmin.")

        user = await self.repo.update_user(user_id, role_id=new_role.id)
        await self.commit()
        return UserProfileResponse.model_validate(user)

    async def change_user_status(self, user_id: str, is_active: bool, actor_id: str) -> UserProfileResponse:
        if user_id == actor_id:
            raise BadRequestException("Anda tidak dapat menonaktifkan akun Anda sendiri.")

        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan.")

        user = await self.repo.update_user(user_id, is_active=is_active)
        await self.commit()
        return UserProfileResponse.model_validate(user)

    async def delete_user(self, user_id: str, actor_id: str) -> None:
        if user_id == actor_id:
            raise BadRequestException("Anda tidak dapat menghapus akun Anda sendiri.")

        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan.")

        if user.role and user.role.slug == "superadmin":
            raise ForbiddenException("Akun Superadmin tidak dapat dihapus.")

        await self.repo.soft_delete_user(user_id)
        await self.commit()

    # ==========================================
    # Dynamic Role Management Service
    # ==========================================

    async def get_all_roles(self) -> List[RoleResponse]:
        roles = await self.repo.get_all_roles()
        return [RoleResponse.model_validate(r) for r in roles]

    async def get_role_detail(self, role_id: str) -> RoleResponse:
        role = await self.repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Role tidak ditemukan.")
        return RoleResponse.model_validate(role)

    async def create_role(self, payload: RoleCreateRequest) -> RoleResponse:
        existing = await self.repo.get_role_by_slug(payload.slug)
        if existing:
            raise ConflictException(f"Role dengan slug '{payload.slug}' sudah ada.")

        role = await self.repo.create_role(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            is_system=False,
        )

        if payload.permission_ids:
            await self.repo.sync_role_permissions(role.id, payload.permission_ids)

        await self.commit()
        return await self.get_role_detail(role.id)

    async def update_role(self, role_id: str, payload: RoleUpdateRequest) -> RoleResponse:
        role = await self.repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Role tidak ditemukan.")

        update_data = {}
        if payload.name is not None:
            update_data["name"] = payload.name.strip()
        if payload.description is not None:
            update_data["description"] = payload.description.strip()

        if update_data:
            await self.repo.update_role(role_id, **update_data)

        if payload.permission_ids is not None:
            await self.repo.sync_role_permissions(role_id, payload.permission_ids)

        await self.commit()
        return await self.get_role_detail(role_id)

    async def delete_role(self, role_id: str) -> None:
        role = await self.repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Role tidak ditemukan.")

        if role.is_system:
            raise ForbiddenException(f"Role sistem '{role.name}' tidak dapat dihapus.")

        deleted = await self.repo.delete_role(role_id)
        if not deleted:
            raise BadRequestException("Gagal menghapus role.")
        await self.commit()

    async def sync_role_permissions(self, role_id: str, permission_ids: List[str]) -> RoleResponse:
        role = await self.repo.get_role_by_id(role_id)
        if not role:
            raise NotFoundException("Role tidak ditemukan.")

        await self.repo.sync_role_permissions(role_id, permission_ids)
        await self.commit()
        return await self.get_role_detail(role_id)

    async def get_all_permissions(self) -> List[PermissionResponse]:
        perms = await self.repo.get_all_permissions()
        return [PermissionResponse.model_validate(p) for p in perms]
