import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy import String as UUID
from app.core.database import Base

class DeepExploreJob(Base):
    __tablename__ = "deep_explore_jobs"

    job_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    requested_topic = Column(String, nullable=False)
    normalized_topic = Column(String, nullable=False)
    paper_limit = Column(Integer, nullable=False)
    credits_used = Column(Integer, nullable=False)
    status = Column(String, default="Queued")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Integer, nullable=True)
    report_cache_id = Column(String, nullable=True)
    search_queries = Column(JSON, nullable=True) # Stores the expanded queries
