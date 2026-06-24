from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..db.database import Base


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    license_plate_number = Column(String(20), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
