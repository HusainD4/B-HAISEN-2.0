from typing import List, Union, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==========================================
    # Application Configuration
    # ==========================================
    APP_NAME: str = "Haisen Official Store"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_SUPER_SECURE_RANDOM_HASH"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 hari
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 hari

    # ==========================================
    # Database Configuration (PostgreSQL / Supabase Async)
    # ==========================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/haisen_store"
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            # Normalisasi URL postgresql biasa menjadi asyncpg
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ==========================================
    # Midtrans Payment Gateway
    # ==========================================
    MIDTRANS_SERVER_KEY: str = ""
    MIDTRANS_CLIENT_KEY: str = ""
    MIDTRANS_IS_PRODUCTION: bool = False

    @property
    def midtrans_snap_url(self) -> str:
        if self.MIDTRANS_IS_PRODUCTION:
            return "https://app.midtrans.com/snap/v1/transactions"
        return "https://app.sandbox.midtrans.com/snap/v1/transactions"

    @property
    def midtrans_status_url(self) -> str:
        if self.MIDTRANS_IS_PRODUCTION:
            return "https://api.midtrans.com/v2"
        return "https://api.sandbox.midtrans.com/v2"

    # ==========================================
    # Email SMTP (Gmail Configuration)
    # ==========================================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""  # App Password Gmail (16 digit)
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "Haisen Official Store"

    # ==========================================
    # WhatsApp Gateway (Self-Hosted QR Code Multi-Device)
    # Khusus Notifikasi Superadmin, Admin, dan Staff
    # ==========================================
    WA_GATEWAY_URL: str = "http://localhost:3333"  # Endpoint service engine QR WA
    WA_API_KEY: str = ""
    WA_ADMIN_NUMBERS: str = ""  # Format nomor: 628123456789,628987654321

    @property
    def admin_phone_list(self) -> List[str]:
        if not self.WA_ADMIN_NUMBERS:
            return []
        return [num.strip() for num in self.WA_ADMIN_NUMBERS.split(",") if num.strip()]

    # ==========================================
    # Supabase Storage (S3-Compatible Protocol)
    # ==========================================
    S3_ENDPOINT_URL: Optional[str] = "https://evfafqohymlnffieyntt.storage.supabase.co/storage/v1/s3"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "haisen-store-bucket"
    S3_REGION_NAME: str = "ap-southeast-1"
    S3_PUBLIC_URL_PREFIX: str = "https://evfafqohymlnffieyntt.supabase.co/storage/v1/object/public/haisen-store-bucket"

    FRONTEND_URL: str = "https://store.haisen.my.id"

    # ==========================================
    # Security & CORS
    # ==========================================
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://store.haisen.my.id",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
