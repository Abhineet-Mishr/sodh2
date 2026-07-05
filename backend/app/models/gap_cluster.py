import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.database import Base

# Gap Cluster Mapping Table
gap_cluster_mapping = Table(
    'gap_cluster_mapping', Base.metadata,
    Column('cluster_id', String, ForeignKey('gap_clusters.cluster_id'), primary_key=True),
    Column('gap_object_id', String, ForeignKey('gap_objects.gap_object_id'), primary_key=True)
)

class GapCluster(Base):
    __tablename__ = "gap_clusters"

    cluster_id = Column(String, primary_key=True, index=True)
    cluster_title = Column(String, nullable=False)
    cluster_summary = Column(String, nullable=False)
    gap_category = Column(String, nullable=False)
    evidence_score = Column(Float, nullable=False)
    confidence_level = Column(String, nullable=False)
    gap_object_count = Column(Integer, nullable=False)
    paper_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    from sqlalchemy.orm import relationship
    gap_objects = relationship("GapObject", secondary=gap_cluster_mapping, back_populates="clusters")
