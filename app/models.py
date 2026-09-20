import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=gen_id)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    relays = relationship("Relay", back_populates="owner", cascade="all, delete-orphan")


class Relay(Base):
    __tablename__ = "relays"

    id = Column(String, primary_key=True, default=gen_id)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=False)
    label = Column(String, nullable=True)
    discord_webhook_url = Column(String, nullable=False)
    # optional - if set, incoming events must include a valid HMAC signature
    secret = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    event_count = Column(Integer, default=0)

    owner = relationship("ApiKey", back_populates="relays")
