import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


class RecognitionStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class RecognitionRequest(Base):
    __tablename__ = "recognition_requests"
    __table_args__ = (Index("ix_recognition_requests_created_at_desc", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    plate_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[RecognitionStatus] = mapped_column(
        Enum(RecognitionStatus, name="recognition_status"),
        nullable=False,
        default=RecognitionStatus.NOT_STARTED,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    detection_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bounding_box: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    plate_region: Mapped[str | None] = mapped_column(String(8), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
