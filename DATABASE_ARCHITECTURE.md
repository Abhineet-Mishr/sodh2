# Database Architecture & Integration

This document outlines the database schema for the SODH AI Research OS, how it is integrated with the FastAPI backend, and the exact steps required to set up and connect to the database.

## Architecture & Schema

The backend uses **PostgreSQL** coupled with the **`pgvector`** extension for high-dimensional vector storage and similarity search. The ORM used is **SQLAlchemy 2.x**.

### Core Models (`backend/app/models/`)

1. **User (`users`)**:
   - Stores authentication data (email, hashed password, security key).
   - Relationship to `CreditLedger`, `DeepExploreJob`, and `SearchBuilderJob`.

2. **CreditLedger (`credit_ledgers`)**:
   - A double-entry accounting ledger to track AI credit usage.
   - Contains `amount` (positive for grants, negative for consumption) and a `description` (e.g., "Initial grant", "Deep explore job").

3. **DeepExploreJob (`deep_explore_jobs`)**:
   - Tracks the state of the long-running AI literature review background jobs.
   - States: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`.
   - Stores the initial topic, the generated boolean query, and relationships to resulting papers and gap objects.

4. **Paper (`papers`)**:
   - Stores metadata and text extracted from PubMed.
   - Contains `pmid`, `title`, `abstract`, `authors`, `publication_date`, and the `full_text` (extracted from the XML).

5. **GapObject (`gap_objects`)**:
   - Stores the atomic "gaps", "limitations", or "contradictions" identified by the LLM in Phase 3.
   - Contains a `Vector` column: `embedding = Column(Vector(768))`. This allows the database to perform semantic similarity clustering.

6. **GapCluster (`gap_clusters`)**:
   - Represents a group of similar `GapObjects` clustered together during Phase 4 (using `pgvector`'s cosine distance calculation).

7. **ReportCache (`report_caches`)**:
   - Stores the final synthesized Markdown report generated in Phase 5, tied to a specific `DeepExploreJob`.

## Code Integration

- **`app.db.base_class.Base`**: The declarative base all models inherit from.
- **`app.core.database`**: Contains the SQLAlchemy `create_engine` and `sessionmaker` logic. It automatically reads the `DATABASE_URL` from the `.env` file.
- **SQLite Fallback**: For rapid local development or CI testing without Docker, setting `USE_SQLITE=true` dynamically intercepts the connection string, creates a local `sodh.db` file, and swaps `UUID` fields to strings and `Vector` fields to JSON fields dynamically. *Note: Vector similarity searches will not work in SQLite mode.*

---

## Setup & Connection Instructions

Follow these exact steps to set up the database and connect it to your application.

### Method 1: Local Docker Setup (Recommended)

1. **Install Docker Desktop**.
2. **Set Environment Variables**:
   Ensure `backend/.env` exists and contains:
   ```env
   DATABASE_URL=postgresql+psycopg2://research_user:research_password@db:5432/research_os
   ```
3. **Start the Database**:
   From the repository root, run:
   ```bash
   docker-compose up db -d
   ```
   *This starts the `ankane/pgvector` image which includes PostgreSQL + pgvector.*
4. **Run Migrations (Alembic)**:
   The backend container is configured to automatically run migrations on startup via `pre_start.py` and `alembic upgrade head`. If you are running the python app locally instead of via docker:
   ```bash
   cd backend
   python pre_start.py
   alembic upgrade head
   ```

### Method 2: Remote Deployment (e.g., Render, AWS RDS, Supabase)

1. **Provision a PostgreSQL Database**.
   - **CRITICAL:** Ensure the provider supports the `pgvector` extension.
2. **Enable the Extension**:
   Before running Alembic migrations, connect to your database using a SQL client (like DBeaver or pgAdmin) and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   *(Note: The `pre_start.py` script attempts to run this automatically on application startup, provided the database user has sufficient privileges).*
3. **Set the Connection String**:
   In your hosting platform's environment variable settings, add:
   ```env
   DATABASE_URL=postgresql+psycopg2://<username>:<password>@<host>:<port>/<dbname>
   ```
   *If your provider gives you a URL starting with `postgres://`, Alembic might complain. Change it to `postgresql+psycopg2://`.*
4. **Deploy the App**:
   The `Dockerfile` entrypoint `CMD ["bash", "-c", "python pre_start.py && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]` will automatically ensure the database is accessible and the schema is up to date before launching the server.
