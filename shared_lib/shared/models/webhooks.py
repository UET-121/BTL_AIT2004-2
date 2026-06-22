from sqlalchemy import Column, Integer, String, Boolean
from ..db.database import Base


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    secret_token = Column(String, nullable=True)
