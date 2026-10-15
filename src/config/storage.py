import os
import uuid
import asyncio
import logging
from typing import Optional, Tuple
from fastapi import UploadFile
from src.config.settings import settings

logger = logging.getLogger("storage")

try:
    import boto3
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class S3BucketStorage:
    """
    Client Supabase Storage (S3-Compatible Protocol).
    Mendukung upload gambar publik ke bucket Supabase (banner, thumbnail, varian)
    serta file aset digital terproteksi dengan presigned URL berbatas waktu.
    """

    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY_ID
        self.secret_key = settings.S3_SECRET_ACCESS_KEY
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region_name = settings.S3_REGION_NAME or "auto"
        self.public_prefix = settings.S3_PUBLIC_URL_PREFIX.rstrip("/") if settings.S3_PUBLIC_URL_PREFIX else None

        self._client = None
        if BOTO3_AVAILABLE and self.access_key and self.secret_key:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region_name,
                config=Config(signature_version="s3v4"),
            )

    def _get_public_url(self, file_key: str) -> str:
        if self.public_prefix:
            return f"{self.public_prefix}/{file_key}"
        if self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{file_key}"
        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{file_key}"

    def _sync_upload(self, file_content: bytes, file_key: str, content_type: str) -> str:
        """Upload sinkron via boto3."""
        if not self._client:
            # Fallback Local Storage jika kredensial S3 belum diisi saat dev lokal
            local_dir = os.path.join("uploads", os.path.dirname(file_key))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join("uploads", file_key)
            with open(local_path, "wb") as f:
                f.write(file_content)
            logger.info(f"S3 credentials kosong. File disimpan lokal: {local_path}")
            return f"/static-uploads/{file_key}"

        self._client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
        )
        return self._get_public_url(file_key)

    async def upload_file(
        self,
        upload_file: UploadFile,
        folder_prefix: str = "products",
    ) -> Tuple[str, str]:
        """
        Upload file publik (gambar banner, thumbnail, varian).
        Return: (file_key, public_url)
        """
        filename = upload_file.filename or "file.bin"
        ext = os.path.splitext(filename)[1].lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_key = f"{folder_prefix}/{unique_name}"

        content = await upload_file.read()
        content_type = upload_file.content_type or "application/octet-stream"

        public_url = await asyncio.to_thread(self._sync_upload, content, file_key, content_type)
        return file_key, public_url

    async def upload_protected_digital_file(
        self,
        upload_file: UploadFile,
        folder_prefix: str = "protected-assets",
    ) -> Tuple[str, int]:
        """
        Upload file produk digital (ZIP, PDF, Software) yang hanya bisa diunduh
        oleh pembeli yang sah via Presigned URL.
        Return: (file_key, file_size_in_bytes)
        """
        filename = upload_file.filename or "asset.zip"
        ext = os.path.splitext(filename)[1].lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_key = f"{folder_prefix}/{unique_name}"

        content = await upload_file.read()
        content_type = upload_file.content_type or "application/octet-stream"
        file_size = len(content)

        await asyncio.to_thread(self._sync_upload, content, file_key, content_type)
        return file_key, file_size

    def generate_presigned_download_url(self, file_key: str, expires_in_seconds: int = 3600) -> str:
        """
        Membuat tautan unduhan berbatas waktu (Presigned URL) untuk pembeli.
        """
        if not self._client:
            return f"/static-uploads/{file_key}"

        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=expires_in_seconds,
            )
            return url
        except Exception as e:
            logger.error(f"Gagal generate presigned URL untuk {file_key}: {str(e)}")
            return self._get_public_url(file_key)

    async def delete_file(self, file_key: str) -> bool:
        """Menghapus objek dari bucket."""
        if not self._client:
            return True

        def _sync_delete():
            self._client.delete_object(Bucket=self.bucket_name, Key=file_key)

        try:
            await asyncio.to_thread(_sync_delete)
            return True
        except Exception as e:
            logger.error(f"Gagal menghapus file {file_key} di S3: {str(e)}")
            return False


storage_client = S3BucketStorage()
