import logging
import os
import sys
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow testing with SQLite
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL")

if USE_SQLITE:
    logger.info("Using SQLite fallback, skipping PostgreSQL pre-start check.")
    sys.exit(0)

if not DATABASE_URL:
    logger.error("DATABASE_URL is not set!")
    sys.exit(1)

@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(3),
    before_sleep=before_sleep_log(logger, logging.INFO)
)
def check_db_connection() -> None:
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check connection
            conn.execute(text("SELECT 1"))
            logger.info("Database connection successful.")

            # Ensure pgvector extension exists
            logger.info("Ensuring pgvector extension exists...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("pgvector extension check complete.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e

def main() -> None:
    logger.info("Initializing service...")
    check_db_connection()
    logger.info("Service initialization complete.")

if __name__ == "__main__":
    main()
