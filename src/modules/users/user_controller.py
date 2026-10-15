from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.dependencies import (
    get_current_user,
    CurrentUser,
    require_roles,
    require_permissions,
)
from src.modules.users.user_service import UserService
from src.modules.users.user_schema import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserAdminCreateRequest,
    UserAdminUpdateRequest,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
    PaginatedUsersResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    RolePermissionSyncRequest,
)
from src.modules.auth.auth_schema import (
    RoleResponse,
    PermissionResponse,
    MessageResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["Users & Role Management"])


# ==========================================
# 1. Profile Pengguna (Self)
# ==========================================

@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Ambil Profil Akun Saya",
)
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_profile(current_user.id)


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Perbarui Profil Akun Saya",
)
async def update_my_profile(
    payload: UserProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.update_profile(current_user.id, payload)


# ==========================================
# 2. Manajemen Pengguna (Admin / Staff / Superadmin)
# ==========================================

@router.get(
    "",
    response_model=PaginatedUsersResponse,
    summary="Daftar Pengguna (Paginasi, Pencarian & Filter)",
    dependencies=[Depends(require_permissions("user:read"))],
)
async def list_users(
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah data per halaman"),
    search: Optional[str] = Query(None, description="Cari nama, email, atau no HP"),
    role: Optional[str] = Query(None, description="Filter slug role (superadmin, admin, finance, staff, user)"),
    is_active: Optional[bool] = Query(None, description="Filter status akun aktif"),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_users_list(
        page=page,
        limit=limit,
        search=search,
        role_slug=role,
        is_active=is_active,
    )


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Detail Akun Pengguna Berdasarkan ID",
    dependencies=[Depends(require_permissions("user:read"))],
)
async def get_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_user_detail(user_id)


@router.post(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin Membuat User Baru Dengan Role Tertentu",
    dependencies=[Depends(require_permissions("user:manage"))],
)
async def create_user_by_admin(
    payload: UserAdminCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.admin_create_user(payload, actor_role=current_user.role)


@router.put(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Admin Memperbarui Data Pengguna",
    dependencies=[Depends(require_permissions("user:manage"))],
)
async def update_user_by_admin(
    user_id: str,
    payload: UserAdminUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.admin_update_user(user_id, payload, actor_role=current_user.role)


@router.patch(
    "/{user_id}/role",
    response_model=UserProfileResponse,
    summary="Ganti Role Pengguna (Superadmin / Admin)",
    dependencies=[Depends(require_roles("superadmin", "admin"))],
)
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.change_user_role(user_id, payload.role_id, actor_role=current_user.role)


@router.patch(
    "/{user_id}/status",
    response_model=UserProfileResponse,
    summary="Aktifkan atau Nonaktifkan Akun Pengguna",
    dependencies=[Depends(require_roles("superadmin", "admin"))],
)
async def update_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.change_user_status(user_id, payload.is_active, actor_id=current_user.id)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Hapus Pengguna (Soft-Delete)",
    dependencies=[Depends(require_roles("superadmin", "admin"))],
)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.delete_user(user_id, actor_id=current_user.id)
    return MessageResponse(message="Akun pengguna berhasil dihapus.")


# ==========================================
# 3. Dynamic Roles & Permissions CRUD (Superadmin Only)
# ==========================================

@router.get(
    "/roles/all",
    response_model=List[RoleResponse],
    summary="Daftar Seluruh Role & Permissions (Admin/Superadmin)",
    dependencies=[Depends(require_roles("superadmin", "admin"))],
)
async def get_all_roles(
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_all_roles()


@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Detail Role Berdasarkan ID",
    dependencies=[Depends(require_roles("superadmin", "admin"))],
)
async def get_role_detail(
    role_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_role_detail(role_id)


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat Role Baru (Superadmin Only)",
    dependencies=[Depends(require_roles("superadmin"))],
)
async def create_new_role(
    payload: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.create_role(payload)


@router.put(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Perbarui Role (Superadmin Only)",
    dependencies=[Depends(require_roles("superadmin"))],
)
async def update_role(
    role_id: str,
    payload: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.update_role(role_id, payload)


@router.delete(
    "/roles/{role_id}",
    response_model=MessageResponse,
    summary="Hapus Custom Role (Superadmin Only - Role Sistem Tidak Dapat Dihapus)",
    dependencies=[Depends(require_roles("superadmin"))],
)
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.delete_role(role_id)
    return MessageResponse(message="Role berhasil dihapus.")


@router.put(
    "/roles/{role_id}/permissions",
    response_model=RoleResponse,
    summary="Sinkronisasi Permissions untuk Suatu Role (Superadmin Only)",
    dependencies=[Depends(require_roles("superadmin"))],
)
async def sync_role_permissions(
    role_id: str,
    payload: RolePermissionSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.sync_role_permissions(role_id, payload.permission_ids)


@router.get(
    "/permissions/all",
    response_model=List[PermissionResponse],
    summary="Daftar Master Seluruh Permissions Sistem",
    dependencies=[Depends(require_roles("superadmin", "admin"))],
)
async def get_all_permissions(
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_all_permissions()
