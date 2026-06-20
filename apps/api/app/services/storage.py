import logging
from abc import ABC, abstractmethod
from pathlib import Path

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
    """MinIO storage — stretch goal; raises until configured."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        raise NotImplementedError("MinIO storage not yet configured. Use STORAGE_TYPE=local.")

    async def save(self, filename: str, content: bytes) -> str:
        raise NotImplementedError

    async def get_url(self, filename: str) -> str:
        raise NotImplementedError

    async def delete(self, filename: str) -> None:
        raise NotImplementedError


def get_storage_service(settings: Settings | None = None) -> StorageService:
    settings = settings or get_settings()
    if settings.storage_type == "local":
        return LocalStorage(settings.upload_dir)
    if settings.storage_type == "minio":
        return MinioStorage(settings)
    raise ValueError(f"Unsupported storage type: {settings.storage_type}")
