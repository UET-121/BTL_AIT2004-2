from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DetectionCreate(BaseModel):
    camera_id: str
    image_url: str
