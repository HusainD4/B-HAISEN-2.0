import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_service import BaseService
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
    NotFoundException,
    ConflictException,
)
from src.config.settings import settings
from src.config.mailer import mailer
from src.modules.auth.auth_repository import AuthRepository
from src.modules.auth.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RoleResponse,
    PermissionResponse,
)


class AuthService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.repo = AuthRepository(db)

    async def _generate_token_response(self, user) -> TokenResponse:
        role_slug = user.role.slug if user.role else "user"

        access_token = create_access_token(
            subject=user.id,
            role=role_slug,
            extra_claims={"email": user.email, "name": user.full_name},
        )
        refresh_token_str = create_refresh_token(subject=user.id)

        # Simpan hash refresh token ke database
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.repo.save_refresh_token(
            user_id=user.id,
            raw_token=refresh_token_str,
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        # Cek ketersediaan email
        existing_user = await self.repo.get_user_by_email(payload.email)
        if existing_user:
            raise ConflictException("Alamat email ini sudah terdaftar. Silakan login.")

        # Ambil role bawaan 'user'
        default_role = await self.repo.get_default_role()

        hashed_pwd = hash_password(payload.password)
        new_user = await self.repo.create_user(
            email=payload.email,
            password_hash=hashed_pwd,
            full_name=payload.full_name,
            phone=payload.phone,
            address=payload.address,
            province=payload.province,
            city=payload.city,
            district=payload.district,
            postal_code=payload.postal_code,
            role_id=default_role.id if default_role else None,
        )

        token_response = await self._generate_token_response(new_user)
        await self.commit()
        return token_response

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.repo.get_user_by_email(payload.email)
        if not user:
            raise UnauthorizedException("Email atau password yang Anda masukkan salah.")

        if not verify_password(payload.password, user.password_hash):
            raise UnauthorizedException("Email atau password yang Anda masukkan salah.")

        if not user.is_active:
            raise UnauthorizedException("Akun Anda dinonaktifkan. Silakan hubungi admin.")

        token_response = await self._generate_token_response(user)
        await self.commit()
        return token_response

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        # Validasi struktur JWT refresh token
        payload = decode_token(refresh_token_str)
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise UnauthorizedException("Refresh token tidak valid.")

        # Validasi token di database (cek apakah sudah di-revoke atau kadaluwarsa)
        stored_token = await self.repo.get_valid_refresh_token(refresh_token_str)
        if not stored_token:
            # Jika token tidak ditemukan atau sudah dicabut, cabut semua token sesi user (deteksi token reuse attack)
            await self.repo.revoke_all_user_refresh_tokens(user_id)
            await self.commit()
            raise UnauthorizedException("Sesi telah kedaluwarsa atau token tidak valid. Silakan login kembali.")

        # Revoke token lama (Mekanisme Rotasi Refresh Token)
        await self.repo.revoke_refresh_token(refresh_token_str)

        user = await self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("Pengguna tidak ditemukan atau tidak aktif.")

        token_response = await self._generate_token_response(user)
        await self.commit()
        return token_response

    async def logout(self, refresh_token_str: str) -> None:
        await self.repo.revoke_refresh_token(refresh_token_str)
        await self.commit()

    async def forgot_password(self, email: str) -> None:
        user = await self.repo.get_user_by_email(email)
        if not user:
            # Tetap return sukses agar tidak membocorkan enumerasi email user
            return

        # Generate secure random token
        raw_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # Berlaku 1 jam
        await self.repo.save_password_reset_token(user.id, raw_token, expires_at)
        await self.commit()

        # Kirim email instruksi reset password
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw_token}"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Permintaan Reset Password</h2>
            <p>Halo <strong>{user.full_name}</strong>,</p>
            <p>Kami menerima permintaan untuk mereset kata sandi akun Haisen Official Store Anda.</p>
            <p style="margin: 24px 0;">
                <a href="{reset_link}" style="background-color: #2563eb; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Reset Kata Sandi
                </a>
            </p>
            <p>Atau salin tautan berikut ke browser Anda:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p style="color: #666; font-size: 13px;">Tautan ini hanya berlaku selama 1 jam. Jika Anda tidak meminta reset password, abaikan email ini.</p>
        </div>
        """
        await mailer.send_email(
            to_email=user.email,
            subject=f"Reset Password - {settings.APP_NAME}",
            html_content=html_body,
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        reset_token = await self.repo.get_valid_password_reset_token(token)
        if not reset_token:
            raise BadRequestException("Token reset password tidak valid atau telah kedaluwarsa.")

        hashed_pwd = hash_password(new_password)
        await self.repo.update_user_password(reset_token.user_id, hashed_pwd)
        await self.repo.mark_password_reset_token_used(reset_token.id)
        # Cabut semua sesi aktif pengguna demi keamanan
        await self.repo.revoke_all_user_refresh_tokens(reset_token.user_id)
        await self.commit()

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan.")

        if not verify_password(old_password, user.password_hash):
            raise BadRequestException("Password lama yang Anda masukkan tidak sesuai.")

        hashed_pwd = hash_password(new_password)
        await self.repo.update_user_password(user.id, hashed_pwd)
        await self.repo.revoke_all_user_refresh_tokens(user.id)
        await self.commit()

    async def get_all_roles(self) -> List[RoleResponse]:
        roles = await self.repo.get_all_roles()
        return [RoleResponse.model_validate(r) for r in roles]

    async def get_all_permissions(self) -> List[PermissionResponse]:
        perms = await self.repo.get_all_permissions()
        return [PermissionResponse.model_validate(p) for p in perms]
