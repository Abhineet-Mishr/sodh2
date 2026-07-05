import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy import JSON
from app.core.database import Base

class ReportCache(Base):
    __tablename__ = "report_cache"

    cache_id = Column(String, primary_key=True, index=True)
    normalized_topic = Column(String, index=True, nullable=False)
    paper_limit = Column(Integer, nullable=False)
    generated_report = Column(JSON, nullable=False)
    cluster_ids = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
