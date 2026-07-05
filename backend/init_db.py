import os
os.environ["USE_SQLITE"] = "true"
from app.core.database import engine, Base
from app.models import User, CreditLedger, DeepExploreJob, Paper, GapObject, GapCluster, ReportCache
Base.metadata.create_all(bind=engine)
print("Database created!")
