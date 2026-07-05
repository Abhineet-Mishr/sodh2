# SODH AI Research OS: Summary

## Features Overview
- **User Authentication & Credit Ledger:** Secure JWT-based registration and login. Users are granted initial credits (50) which are consumed by AI jobs.
- **Search Builder (Feature C):** A standalone tool that uses LLMs to convert natural language research topics into highly optimized, Boolean PubMed queries.
- **Deep Explore Orchestrator (Feature B):** A multi-phase background pipeline that completely automates literature review.
  - *Phase 0 (Query Expansion):* Converts a user topic into a Boolean query.
  - *Phase 1 (Retrieval):* Fetches metadata from PubMed using E-utilities.
  - *Phase 2 (Candidate Extraction):* Downloads full XML text for open-access papers and extracts relevant sections (Results, Discussion).
  - *Phase 3 (Gap Extraction):* Uses LLMs to find contradictions, biases, or gaps in the literature.
  - *Phase 4 (Clustering):* Uses `pgvector` and cosine similarity to cluster identified gaps.
  - *Phase 5 (Synthesis):* The LLM synthesizes the clustered gaps into a final, comprehensive Markdown report.
- **Real-Time Polling UI:** The frontend continuously polls the backend for job status and beautifully renders the final Markdown report.

## Architecture & Technical Workflow
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Router DOM, Axios.
- **Backend:** FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.0.
- **Database:** PostgreSQL with `pgvector` for vector similarity searches. A fallback to `SQLite` is provided for local/test development (disabling vector clustering).
- **Background Jobs:** Handled asynchronously via `asyncio.create_task` and tracked in the database using the `DeepExploreJob` model.
- **LLM Integration:** Abstracted via an `LLMProvider` interface. Currently implemented using the `google-genai` SDK (Gemini 1.5/2.5 Flash).

## Debugging Support
- **Database Issues:** If Alembic fails or vector columns throw errors, ensure you have run `CREATE EXTENSION vector;`. The `pre_start.py` script does this automatically.
- **Testing:** Run backend tests with `PYTHONPATH=backend pytest backend/tests/`. This uses the SQLite fallback (`USE_SQLITE=true`) automatically.
- **Frontend Verifications:** Use the temporary Playwright scripts in `/home/jules/verification` to test UI flows.
