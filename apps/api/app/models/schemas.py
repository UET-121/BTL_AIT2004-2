from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.recognition import RecognitionStatus


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class RecognitionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    plate_number: str | None
    status: RecognitionStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    confidence_score: float | None = None
    detection_confidence: float | None = None
    ocr_confidence: float | None = None
    needs_review: bool = False
    bounding_box: BoundingBox | None = None
    plate_region: str | None = None


class RecognitionRequestSubmitResponse(BaseModel):
    request_id: UUID
    status: RecognitionStatus
    created_at: datetime


class RecognitionRequestListResponse(BaseModel):
    items: list[RecognitionRequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str = "ok"
    db: str | None = None
    redis: str | None = None
    version: str | None = None


class ErrorResponse(BaseModel):
    detail: str | list[dict] = Field(examples=["Not found"])
