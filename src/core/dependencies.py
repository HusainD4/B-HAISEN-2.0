from typing import List, Optional, Callable, Set
from dataclasses import dataclass, field
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.config.database import get_db
from src.core.security import decode_token
from src.core.exceptions import UnauthorizedException, ForbiddenException

# Skema OAuth2 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


@dataclass
class CurrentUser:
    """Representasi payload user yang terautentikasi dengan hak akses dynamic RBAC."""
    id: str
    role: str
    email: Optional[str] = None
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI Dependency untuk validasi Access Token dan mengambil data identitas pengguna
    beserta daftar permission dinamis dari database.
    """
    if not token:
        raise UnauthorizedException("Header Authorization (Bearer token) diperlukan")

    payload = decode_token(token)
    user_id: Optional[str] = payload.get("sub")
    role: Optional[str] = payload.get("role")
    token_type: Optional[str] = payload.get("type")

    if not user_id or token_type != "access":
        raise UnauthorizedException("Token akses tidak valid")

    # Ambil user dan nama slug role dari database
    user_query = text("""
        SELECT u.id, u.email, u.is_active, r.slug as role_slug
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.id = :id AND u.is_deleted = false
    """)
    result = await db.execute(user_query, {"id": user_id})
    user_row = result.fetchone()

    if not user_row:
        # Fallback jika baru inisialisasi awal
        return CurrentUser(id=user_id, role=role or "user", is_active=True, permissions=[])

    if not user_row.is_active:
        raise ForbiddenException("Akun Anda telah dinonaktifkan")

    user_role = user_row.role_slug or role or "user"

    # Ambil permissions dari role user
    perm_query = text("""
        SELECT p.code
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN users u ON u.role_id = rp.role_id
        WHERE u.id = :id
    """)
    perm_result = await db.execute(perm_query, {"id": user_id})
    user_permissions = [row.code for row in perm_result.fetchall()]

    return CurrentUser(
        id=str(user_row.id),
        role=user_role,
        email=user_row.email,
        is_active=user_row.is_active,
        permissions=user_permissions,
    )


def require_roles(*allowed_roles: str) -> Callable:
    """
    Dependency generator untuk pembatasan hak akses berbasis Role Slug (RBAC).
    """
    roles_set: Set[str] = {r.lower() for r in allowed_roles}

    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_role = current_user.role.lower()
        if "superadmin" in user_role:
            return current_user  # Superadmin memiliki hak akses menyeluruh

        if user_role not in roles_set:
            raise ForbiddenException(
                f"Akses ditolak. Endpoint ini memerlukan role: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def require_permissions(*required_permissions: str) -> Callable:
    """
    Dependency generator untuk pembatasan hak akses granular berbasis Permission Code.
    Contoh: require_permissions("product:create", "product:update")
    """
    req_set: Set[str] = set(required_permissions)

    async def permission_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role.lower() == "superadmin":
            return current_user  # Superadmin bypass seluruh permission check

        user_perms = set(current_user.permissions)
        # Jika salah satu permission terpenuhi
        if not user_perms.intersection(req_set):
            raise ForbiddenException(
                f"Akses ditolak. Anda memerlukan salah satu izin: {', '.join(required_permissions)}"
            )
        return current_user

    return permission_checker


# Shortcuts helper dependency
require_superadmin = require_roles("superadmin")
require_admin = require_roles("superadmin", "admin")
require_staff = require_roles("superadmin", "admin", "staff")
