import uuid

def generate_uuid():
    return str(uuid.uuid4())
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import String as UUID
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    security_key_hash = Column(String, nullable=False)
    credits = Column(Integer, default=50, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="active")
