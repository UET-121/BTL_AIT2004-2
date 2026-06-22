from pydantic import BaseModel
import time


class CameraStreamRequest(BaseModel):
    camera_id: str
    link: str
    timestamp: int = int(time.time())
    name: str = "Unknown Camera"


class CameraStatusUpdate(BaseModel):
    camera_id: str
    is_active: bool
    
class CameraUpdateRequest(BaseModel):
    link: str
    name: str

