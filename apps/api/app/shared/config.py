from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/plate_recognition",
        alias="DATABASE_URL",
    )

    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Storage
    storage_type: Literal["local", "minio", "s3", "supabase"] = Field(
        default="local", alias="STORAGE_TYPE"
    )
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    minio_url: str = Field(default="http://localhost:9000", alias="MINIO_URL")
    minio_public_url: str = Field(default="http://localhost:9000", alias="MINIO_PUBLIC_URL")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="uploads", alias="MINIO_BUCKET")


    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    # Detection
    use_plate_detection: bool = Field(default=True, alias="USE_PLATE_DETECTION")
    plate_detection_model: str = Field(default="yolov8n.pt", alias="PLATE_DETECTION_MODEL")
    plate_detection_confidence: float = Field(default=0.5, alias="PLATE_DETECTION_CONFIDENCE")
    use_onnx_inference: bool = Field(default=False, alias="USE_ONNX_INFERENCE")
    onnx_model_path: str = Field(
        default="models/onnx/yolov8-plate-v1.onnx", alias="ONNX_MODEL_PATH"
    )
    detection_decimation: int = Field(default=2, alias="DETECTION_DECIMATION")


    # OCR
    ocr_min_confidence: float = Field(default=0.3, alias="OCR_MIN_CONFIDENCE")
    ocr_gpu: bool = Field(default=False, alias="OCR_GPU")

    # Confidence thresholds
    needs_review_threshold: float = Field(default=0.6, alias="NEEDS_REVIEW_THRESHOLD")
    auto_accept_threshold: float = Field(default=0.85, alias="AUTO_ACCEPT_THRESHOLD")

    # Retry
    enable_enhanced_retry: bool = Field(default=True, alias="ENABLE_ENHANCED_RETRY")
    max_processing_attempts: int = Field(default=3, alias="MAX_PROCESSING_ATTEMPTS")

    # Validation
    default_plate_region: str = Field(default="BR", alias="DEFAULT_PLATE_REGION")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: Literal["json", "text"] = Field(default="text", alias="LOG_FORMAT")
    debug: bool = Field(default=False, alias="DEBUG")

    app_version: str = "1.0.0"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            import json

            return json.loads(value)
        if isinstance(value, list):
            return value
        raise ValueError("CORS_ORIGINS must be a JSON array or list")


@lru_cache
def get_settings() -> Settings:
    return Settings()
