import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class GapObject(Base):
    __tablename__ = "gap_objects"

    gap_object_id = Column(String, primary_key=True, index=True)
    pmid = Column(String, ForeignKey("papers.pmid"), index=True, nullable=False)
    pmcid = Column(String, nullable=True)
    gap_category = Column(String, index=True, nullable=False)
    gap_statement = Column(String, nullable=False)
    supporting_evidence = Column(String, nullable=False)
    section = Column(String, nullable=False)
    confidence = Column(Float, index=True, nullable=False)
    suggested_study = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 768 is the default dimension for text-embedding-004 from Gemini
    embedding = Column(Vector(768), nullable=True)

    from sqlalchemy.orm import relationship
    from app.models.gap_cluster import gap_cluster_mapping
    clusters = relationship("GapCluster", secondary=gap_cluster_mapping, back_populates="gap_objects")
