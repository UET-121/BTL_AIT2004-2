import logging
import io
from abc import ABC, abstractmethod
from pathlib import Path

from minio import Minio
from app.shared.config import Settings, get_settings


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
}


def validate_image_magic(content: bytes, extension: str) -> bool:
    ext = extension.lower().lstrip(".")
    if ext == "jpeg":
        ext = "jpg"
    for magic, fmt in MAGIC_BYTES.items():
        if content.startswith(magic) and fmt == ext:
            return True
    return False


class StorageService(ABC):
    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """Save file and return public URL/path."""

    @abstractmethod
    async def get_url(self, filename: str) -> str:
        """Return URL for stored file."""

    @abstractmethod
    async def delete(self, filename: str) -> None:
        """Remove stored file."""


class LocalStorage(StorageService):
    def __init__(self, upload_dir: str) -> None:
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        path = self.upload_dir / filename
        path.write_bytes(content)
        logger.debug("Saved file to %s", path)
        return f"/uploads/{filename}"

    async def get_url(self, filename: str) -> str:
        return f"/uploads/{filename}"

    async def delete(self, filename: str) -> None:
        path = self.upload_dir / filename
        if path.exists():
            path.unlink()


class MinioStorage(StorageService):
    """MinIO storage service."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # Parse host/port and secure protocol from url
        endpoint_url = settings.minio_url.rstrip("/")
        url = endpoint_url.replace("http://", "").replace("https://", "")
        secure = endpoint_url.startswith("https://")
        
        self.client = Minio(
            endpoint=url,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Created MinIO bucket: %s", self.bucket)
        except Exception as e:
            logger.exception("Failed to verify/create MinIO bucket %s: %s", self.bucket, e)

    def save_sync(self, filename: str, content: bytes) -> str:
        data = io.BytesIO(content)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=filename,
            data=data,
            length=len(content),
        )
        return filename

    def get_url_sync(self, filename: str) -> str:
        from datetime import timedelta
        url = self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=filename,
            expires=timedelta(days=7),
        )
        # Rewrite internal docker minio url to public endpoint if different
        internal_base = self._settings.minio_url.rstrip("/")
        public_base = self._settings.minio_public_url.rstrip("/")
        if internal_base != public_base:
            url = url.replace(internal_base, public_base)
        return url

    def delete_sync(self, filename: str) -> None:
        self.client.remove_object(self.bucket, filename)

    def download_sync(self, filename: str, target_path: str) -> None:
        self.client.fget_object(self.bucket, filename, target_path)

    async def save(self, filename: str, content: bytes) -> str:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.save_sync, filename, content)

    async def get_url(self, filename: str) -> str:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_url_sync, filename)

    async def delete(self, filename: str) -> None:
        import asyncio
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delete_sync, filename)



def get_storage_service(settings: Settings | None = None) -> StorageService:
    settings = settings or get_settings()
    if settings.storage_type == "local":
        return LocalStorage(settings.upload_dir)
    if settings.storage_type == "minio":
        return MinioStorage(settings)
    raise ValueError(f"Unsupported storage type: {settings.storage_type}")
