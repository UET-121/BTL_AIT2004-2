"""
DetectionRequest — Lưu mỗi lần upload video/hình để nhận diện biển số.
Status flow: NOT_STARTED → PENDING → COMPLETED | FAILED | NEEDS_REVIEW
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from ..db.database import Base


class DetectionRequest(Base):
    __tablename__ = "detection_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # File upload info
    image_url = Column(String, nullable=True)       # MinIO URL of uploaded media
    # Detection result
    plate_number = Column(String(50), nullable=True)
    status = Column(String(20), default="NOT_STARTED", nullable=False)  # NOT_STARTED | PENDING | COMPLETED | FAILED | NEEDS_REVIEW
    error_message = Column(String, nullable=True)
    # Confidence scores
    confidence_score = Column(Integer, nullable=True)        # overall %
    detection_confidence = Column(Integer, nullable=True)    # vehicle/plate bbox confidence
    ocr_confidence = Column(Integer, nullable=True)          # OCR char confidence
    needs_review = Column(Boolean, default=False)
    # Bounding box (as JSON dict with x, y, width, height in px)
    bounding_box = Column(JSON, nullable=True)
    # Metadata
    plate_region = Column(String(20), nullable=True)         # e.g. "HN", "HCM"
    camera_id = Column(String, nullable=True)
    gate = Column(String, nullable=True)
    direction = Column(String(5), nullable=True)             # IN | OUT
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
