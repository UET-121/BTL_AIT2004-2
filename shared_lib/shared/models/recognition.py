from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(
        Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    image_url = Column(String)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("shared.models.profile.Profile", backref="logs")
    camera = relationship("shared.models.camera.Camera", backref="logs")
