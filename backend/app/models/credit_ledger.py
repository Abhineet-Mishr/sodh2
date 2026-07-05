import uuid

def generate_uuid():
    return str(uuid.uuid4())
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy import String as UUID
from app.core.database import Base

class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    feature = Column(String, nullable=False)
    credits_before = Column(Integer, nullable=False)
    credits_deducted = Column(Integer, nullable=False)
    credits_after = Column(Integer, nullable=False)
    job_id = Column(String, nullable=True) # string job_id from DeepExploreJob
    status = Column(String, default="Reserved")
    created_at = Column(DateTime, default=datetime.utcnow)
