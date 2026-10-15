from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class PermissionResponse(BaseModel):
    id: str
    name: str
    code: str
    module: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[PermissionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: Optional[RoleResponse] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Alamat email aktif")
    password: str = Field(..., min_length=8, description="Password minimal 8 karakter")
    full_name: str = Field(..., min_length=2, max_length=100, description="Nama lengkap")
    phone: Optional[str] = Field(None, max_length=25, description="Nomor WhatsApp/HP aktif")
    
    # Alamat Lengkap Pengiriman (Kawasan Indonesia)
    address: Optional[str] = Field(None, max_length=500, description="Nama jalan, RT/RW, Patokan/Detail rumah")
    province: Optional[str] = Field(None, max_length=100, description="Provinsi di Indonesia (untuk RajaOngkir)")
    city: Optional[str] = Field(None, max_length=100, description="Kabupaten / Kota (untuk RajaOngkir)")
    district: Optional[str] = Field(None, max_length=100, description="Kecamatan (untuk RajaOngkir)")
    postal_code: Optional[str] = Field(None, max_length=10, description="Kode Pos validasi kurir")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Token reset password dari email")
    new_password: str = Field(..., min_length=8, description="Password baru minimal 8 karakter")


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    success: bool = True
    message: str
