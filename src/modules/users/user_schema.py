from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.modules.auth.auth_schema import RoleResponse, PermissionResponse


class UserProfileResponse(BaseModel):
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
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)
    address: Optional[str] = Field(None, max_length=500, description="Nama jalan, RT/RW, Patokan/Detail rumah (kawasan Indonesia)")
    province: Optional[str] = Field(None, max_length=100, description="Provinsi")
    city: Optional[str] = Field(None, max_length=100, description="Kabupaten / Kota")
    district: Optional[str] = Field(None, max_length=100, description="Kecamatan")
    postal_code: Optional[str] = Field(None, max_length=10, description="Kode Pos")


class UserAdminCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)
    address: Optional[str] = Field(None, max_length=500)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    role_slug: str = Field("user", description="Slug role (superadmin, admin, finance, staff, user)")
    is_active: bool = True


class UserAdminUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=25)
    address: Optional[str] = Field(None, max_length=500)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    role_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserRoleUpdateRequest(BaseModel):
    role_id: str = Field(..., description="ID Role baru yang akan diberikan kepada user")


class UserStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Status aktif akun (True=Aktif, False=Dinonaktifkan)")


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Nama role (contoh: Auditor)")
    slug: str = Field(..., min_length=2, max_length=50, description="Slug unik (contoh: auditor)")
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: List[str] = Field(default_factory=list, description="Daftar ID permission yang dimiliki")


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: Optional[List[str]] = None


class RolePermissionSyncRequest(BaseModel):
    permission_ids: List[str] = Field(..., description="Daftar lengkap ID permission untuk role ini")


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedUsersResponse(BaseModel):
    items: List[UserProfileResponse]
    meta: PaginationMeta
