"""
Script Generate Akun Superadmin (1x Pakai)
HAISEN OFFICIAL STORE

Penggunaan:
    python scripts/generate_superadmin.py
    Atau dengan argumen:
    python scripts/generate_superadmin.py --email admin@haisen.my.id --name "Super Admin Haisen" --password "Rahasia123!"
"""
import sys
import os
import asyncio
import getpass
import argparse
from pathlib import Path

# Tambahkan direktori root backend ke PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from src.config.database import async_session_factory, engine
from src.core.database_base import Base
from src.core.security import hash_password
from src.modules.auth.auth_model import User, Role
from src.modules.auth.auth_repository import AuthRepository


async def run_generate_superadmin(email: str, name: str, password: str, force: bool = False):
    print("\n=======================================================")
    print("🔐 HAISEN OFFICIAL - GENERATOR AKUN SUPERADMIN (1X PAKAI)")
    print("=======================================================\n")

    # Pastikan skema tabel sudah terinisialisasi
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        auth_repo = AuthRepository(session)
        # 1. Pastikan Role & Permissions sudah di-seed
        await auth_repo.seed_initial_rbac_if_empty()
        await session.commit()

        # 2. Ambil role superadmin
        superadmin_role = await auth_repo.get_role_by_slug("superadmin")
        if not superadmin_role:
            print("❌ Gagal menemukan role 'superadmin' di database.")
            return False

        # 3. Cek apakah Superadmin sudah pernah dibuat (Proteksi 1x Pakai)
        existing_superadmin_stmt = (
            select(User)
            .where(User.role_id == superadmin_role.id, User.is_deleted.is_(False))
        )
        existing_res = await session.execute(existing_superadmin_stmt)
        existing_superadmin = existing_res.scalars().first()

        if existing_superadmin and not force:
            print("⚠️  PERINGATAN: Superadmin sudah terdaftar dalam sistem!")
            print(f"    Email: {existing_superadmin.email}")
            print(f"    Nama : {existing_superadmin.full_name}")
            print("\n⛔ Script 1x pakai diblokir untuk keamanan.")
            print("   Jika Anda benar-benar ingin menambahkan akun baru, jalankan dengan flag: --force\n")
            return False

        # 4. Cek apakah email yang dimasukkan sudah dipakai akun lain
        existing_user = await auth_repo.get_user_by_email(email)
        if existing_user:
            if force:
                print(f"ℹ️  Mengupdate akun yang sudah ada ({email}) menjadi Superadmin...")
                existing_user.role_id = superadmin_role.id
                existing_user.password_hash = hash_password(password)
                existing_user.is_active = True
                existing_user.is_verified = True
                await session.commit()
                print("✅ Akun berhasil diperbarui menjadi Superadmin!")
                return True
            else:
                print(f"❌ Email '{email}' sudah digunakan oleh user lain. Gunakan email berbeda.")
                return False

        # 5. Buat Akun Superadmin Baru
        new_superadmin = User(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            full_name=name.strip(),
            role_id=superadmin_role.id,
            is_active=True,
            is_verified=True,
        )
        session.add(new_superadmin)
        await session.commit()
        await session.refresh(new_superadmin)

        print("🎉 AKUN SUPERADMIN BERHASIL DIBUAT!")
        print("-------------------------------------------------------")
        print(f"🆔 ID        : {new_superadmin.id}")
        print(f"📧 Email     : {new_superadmin.email}")
        print(f"👤 Nama      : {new_superadmin.full_name}")
        print(f"🛡️  Role      : {superadmin_role.name} ({superadmin_role.slug})")
        print(f"🔑 Status    : Aktif & Terverifikasi")
        print("-------------------------------------------------------")
        print("Simpan kredensial ini di tempat yang aman.\n")
        return True


def main():
    parser = argparse.ArgumentParser(description="Generate Akun Superadmin Awal Haisen Official Store")
    parser.add_argument("--email", type=str, help="Email superadmin")
    parser.add_argument("--name", type=str, help="Nama lengkap superadmin")
    parser.add_argument("--password", type=str, help="Password superadmin")
    parser.add_argument("--force", action="store_true", help="Paksa buat atau timpa jika superadmin sudah ada")

    args = parser.parse_args()

    email = args.email
    name = args.name
    password = args.password

    # Input interaktif jika argumen tidak diberikan di CLI
    if not email:
        email = input("Masukkan Email Superadmin: ").strip()
    if not name:
        name = input("Masukkan Nama Lengkap: ").strip()
    if not password:
        password = getpass.getpass("Masukkan Password (min 8 karakter): ").strip()
        confirm_pass = getpass.getpass("Konfirmasi Password: ").strip()
        if password != confirm_pass:
            print("❌ Konfirmasi password tidak cocok!")
            sys.exit(1)

    if len(password) < 8:
        print("❌ Password minimal harus 8 karakter!")
        sys.exit(1)

    success = asyncio.run(run_generate_superadmin(email=email, name=name, password=password, force=args.force))
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
