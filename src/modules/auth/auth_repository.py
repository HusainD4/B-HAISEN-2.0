import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.auth.auth_model import User, Role, Permission, RolePermission, RefreshToken, PasswordResetToken


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Hash token menggunakan SHA256 sebelum disimpan di database (anti-leak)."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(and_(User.email == email.lower(), User.is_deleted == False))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).where(and_(User.id == user_id, User.is_deleted == False))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_role_by_slug(self, slug: str) -> Optional[Role]:
        stmt = select(Role).where(Role.slug == slug.lower())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_default_role(self) -> Optional[Role]:
        role = await self.get_role_by_slug("user")
        if not role:
            # Fallback jika role belum di-seed
            role = Role(name="User", slug="user", description="Customer / Pengguna Umum", is_system=True)
            self.db.add(role)
            await self.db.flush()
        return role

    async def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        postal_code: Optional[str] = None,
        role_id: Optional[str] = None,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            address=address.strip() if address else None,
            province=province.strip() if province else None,
            city=city.strip() if city else None,
            district=district.strip() if district else None,
            postal_code=postal_code.strip() if postal_code else None,
            role_id=role_id,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def save_refresh_token(self, user_id: str, raw_token: str, expires_at: datetime) -> RefreshToken:
        token_hash = self.hash_token(raw_token)
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            is_revoked=False,
            expires_at=expires_at,
        )
        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token

    async def get_valid_refresh_token(self, raw_token: str) -> Optional[RefreshToken]:
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > now,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def revoke_refresh_token(self, raw_token: str) -> None:
        token_hash = self.hash_token(raw_token)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)

    async def revoke_all_user_refresh_tokens(self, user_id: str) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)

    async def save_password_reset_token(self, user_id: str, raw_token: str, expires_at: datetime) -> PasswordResetToken:
        token_hash = self.hash_token(raw_token)
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            is_used=False,
            expires_at=expires_at,
        )
        self.db.add(reset_token)
        await self.db.flush()
        return reset_token

    async def get_valid_password_reset_token(self, raw_token: str) -> Optional[PasswordResetToken]:
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > now,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def mark_password_reset_token_used(self, token_id: str) -> None:
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(is_used=True)
        )
        await self.db.execute(stmt)

    async def update_user_password(self, user_id: str, new_password_hash: str) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_password_hash, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    async def get_all_roles(self) -> List[Role]:
        stmt = select(Role).order_by(Role.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_permissions(self) -> List[Permission]:
        stmt = select(Permission).order_by(Permission.module.asc(), Permission.code.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def seed_initial_rbac_if_empty(self) -> None:
        """Seed otomatis role dan permissions bawaan jika tabel masih kosong."""
        roles = await self.get_all_roles()
        if roles:
            return

        # 1. Definisi Permission Dasar
        default_permissions = [
            # Modul Produk
            ("Lihat Katalog Produk", "product:read", "products"),
            ("Tambah Produk Baru", "product:create", "products"),
            ("Edit Data Produk", "product:update", "products"),
            ("Hapus Produk", "product:delete", "products"),
            # Modul Pesanan & Transaksi
            ("Lihat Pesanan Saya", "order:read_own", "orders"),
            ("Lihat Seluruh Pesanan Toko", "order:read_all", "orders"),
            ("Kelola & Update Status Pesanan", "order:manage", "orders"),
            # Modul Pembayaran
            ("Lihat Log Pembayaran", "payment:read", "payments"),
            ("Kelola Pembayaran & Refund", "payment:manage", "payments"),
            # Modul Role & User
            ("Lihat Daftar Pengguna", "user:read", "users"),
            ("Kelola Pengguna & Status", "user:manage", "users"),
            ("Kelola Role & Hak Akses", "role:manage", "roles"),
        ]

        created_perms: List[Permission] = []
        for name, code, module in default_permissions:
            perm = Permission(name=name, code=code, module=module)
            self.db.add(perm)
            created_perms.append(perm)
        await self.db.flush()

        # 2. Definisi Role Bawaan Sistem
        superadmin_role = Role(name="Super Admin", slug="superadmin", description="Akses penuh ke seluruh sistem", is_system=True)
        admin_role = Role(name="Admin", slug="admin", description="Administrator operasional toko & katalog", is_system=True)
        finance_role = Role(name="Finance", slug="finance", description="Manajemen keuangan, audit pembayaran & refund", is_system=True)
        staff_role = Role(name="Staff / Customer Service", slug="staff", description="Staf operasional & customer service bantuan pesanan", is_system=True)
        user_role = Role(name="User", slug="user", description="Pelanggan / Pengguna terdaftar", is_system=True)

        self.db.add_all([superadmin_role, admin_role, finance_role, staff_role, user_role])
        await self.db.flush()

        # 3. Asosiasi Permission ke Role
        # Superadmin mendapat semua permission
        for p in created_perms:
            self.db.add(RolePermission(role_id=superadmin_role.id, permission_id=p.id))

        # Admin mendapat permission produk, order, payment, user
        for p in created_perms:
            if not p.code.startswith("role:"):
                self.db.add(RolePermission(role_id=admin_role.id, permission_id=p.id))

        # Finance fokus ke pembayaran dan rekap pesanan
        for p in created_perms:
            if p.code in ["payment:read", "payment:manage", "order:read_all"]:
                self.db.add(RolePermission(role_id=finance_role.id, permission_id=p.id))

        # Staff / CS fokus ke produk, pesanan, dan customer data
        for p in created_perms:
            if p.code in ["product:read", "order:read_all", "order:manage", "user:read"]:
                self.db.add(RolePermission(role_id=staff_role.id, permission_id=p.id))

        # User hanya melihat produk dan pesanan sendiri
        for p in created_perms:
            if p.code in ["product:read", "order:read_own"]:
                self.db.add(RolePermission(role_id=user_role.id, permission_id=p.id))

        await self.db.flush()
