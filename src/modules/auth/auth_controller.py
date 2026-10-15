from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.rate_limiter import rate_limit
from src.core.dependencies import get_current_user, CurrentUser, require_roles
from src.modules.auth.auth_service import AuthService
from src.modules.auth.auth_schema import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    MessageResponse,
    RoleResponse,
    PermissionResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Roles"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrasi Akun Pengguna Baru",
)
@rate_limit(max_requests=10, window_seconds=60)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login Pengguna & Dapatkan Token Akses",
)
@rate_limit(max_requests=5, window_seconds=60)  # Proteksi brute-force
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.login(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token Menggunakan Refresh Token",
)
@rate_limit(max_requests=20, window_seconds=60)
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.refresh_tokens(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout dan Cabut Refresh Token Sesi",
)
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.logout(payload.refresh_token)
    return MessageResponse(message="Berhasil logout dari sistem.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Kirim Email Tautan Reset Password",
)
@rate_limit(max_requests=3, window_seconds=300)  # Batasi 3 permintaan per 5 menit
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.forgot_password(payload.email)
    return MessageResponse(
        message="Jika email terdaftar, instruksi reset kata sandi telah dikirim ke kotak masuk Anda."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset Kata Sandi dengan Token Valid",
)
@rate_limit(max_requests=5, window_seconds=300)
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.reset_password(payload.token, payload.new_password)
    return MessageResponse(message="Kata sandi berhasil diatur ulang. Silakan login dengan kata sandi baru.")


@router.get(
    "/me",
    summary="Ambil Informasi Profil & Permissions Akun Saat Ini",
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.repo.get_user_by_id(current_user.id)
    return {
        "user": UserResponse.model_validate(user) if user else None,
        "role": current_user.role,
        "permissions": current_user.permissions,
    }


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Ganti Kata Sandi (Wajib Login)",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(current_user.id, payload.old_password, payload.new_password)
    return MessageResponse(message="Kata sandi berhasil diperbarui.")


@router.get(
    "/roles",
    response_model=List[RoleResponse],
    summary="Daftar Semua Role yang Tersedia (Dynamic RBAC)",
)
async def get_roles(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.get_all_roles()


@router.get(
    "/permissions",
    response_model=List[PermissionResponse],
    summary="Daftar Seluruh Granular Permissions Sistem",
)
async def get_permissions(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.get_all_permissions()
