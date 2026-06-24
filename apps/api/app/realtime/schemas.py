from typing import Any, Literal
from pydantic import BaseModel, Field

class StreamStartRequest(BaseModel):
    source: str = Field(..., description="Camera ID (e.g., '0' for webcam), RTSP URL, or local video file path")

class StreamStatusResponse(BaseModel):
    status: str = Field(..., description="Current status of the stream: stopped, starting, running, error")
    source: str | None = Field(None, description="Current configured source")
    error_message: str | None = Field(None, description="Last error message, if any")

class BBoxSchema(BaseModel):
    x: int
    y: int
    width: int
    height: int

class WebSocketEvent(BaseModel):
    type: Literal[
        "stream.started",
        "stream.stopped",
        "frame.processed",
        "vehicle.detected",
        "plate.detected",
        "plate.ocr_result",
        "plate.confirmed",
        "plate.rejected",
        "stream.error",
    ]
    timestamp: str
    camera_id: str = "cam-01"
    frame_id: int | None = None
    track_id: int | None = None
    plate_text: str | None = None
    confidence: float | None = None
    bbox: BBoxSchema | None = None
    image_base64: str | None = Field(None, description="Optional base64 encoded image frame or crop for frontend rendering")
    data: dict[str, Any] | None = None
