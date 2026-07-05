import pytest
from app.models.deep_explore_job import DeepExploreJob
from app.models.gap_object import GapObject
from app.models.report_cache import ReportCache
from app.core.database import Base

def test_models_exist():
    assert DeepExploreJob.__tablename__ == "deep_explore_jobs"
    assert hasattr(DeepExploreJob, "search_queries")

    assert GapObject.__tablename__ == "gap_objects"
    assert hasattr(GapObject, "embedding")

    assert ReportCache.__tablename__ == "report_cache"
