from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean
from app.core.database import Base

class Paper(Base):
    __tablename__ = "papers"

    pmid = Column(String, primary_key=True, index=True)
    pmcid = Column(String, index=True, nullable=True)
    doi = Column(String, index=True, nullable=True)
    title = Column(String, nullable=False)
    journal = Column(String, nullable=True)
    publication_year = Column(Integer, nullable=True)
    study_type = Column(String, nullable=True)
    mesh_terms = Column(JSON, nullable=True)
    authors = Column(JSON, nullable=True)
    country = Column(String, nullable=True)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
