from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..db.database import Base


class DetectionLog(Base):
    __tablename__ = "detection_logs"
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, index=True)
    person_id = Column(String, index=True)
    image_url = Column(String)
    create_at = Column(DateTime(timezone=True), server_default=func.now())
