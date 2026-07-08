# SODH AI-powered Research Operating System - Architecture

This document describes the architectural layout of the unified SODH system containing Literature Toolkit, Research Suggestions, Deep Explore, and Search Builder.

## System Overview

SODH follows a modular Monolith architecture using a FastAPI backend and a React/Vite frontend. The core goal is to provide a single collaborative research ecosystem. All API routes share a unified PostgreSQL (or SQLite locally) Database to track Credit Ledgers and JWT Authentication.

## Backend Structure (`/backend/app/`)

- `main.py`: Entrypoint for FastAPI, configures CORS, handles startup tasks, and aggregates routers.
- `core/`: Contains fundamental app configuration (`config.py`), database engine connection logic (`database.py`), dependency injection including `get_current_user` (`dependencies.py`), and JWT security helpers (`security.py`).
- `models/`: SQLAlchemy ORM models tracking persistence for the entire ecosystem (e.g. `user.py`, `credit_ledger.py`, `gap_object.py`).
- `schemas/`: Pydantic Models for strict type validation of inputs and outputs for different submodules.
- `routers/`: Exposes HTTP API endpoints divided into domains (`convert.py`, `deduplicate.py`, `deep_explore.py`, `research_suggestions.py`, etc). Each router leverages `Depends(get_current_user)` to ensure uniform authentication.
- `services/`: Encapsulated business logic grouped by domain:
  - `auth/`: Generates and verifies JWT tokens.
  - `credit/`: Handles reserving and deducting user credits for expensive actions.
  - `literature/`: In-memory parsing, deduplication, conversion, and normalization of RIS, NBIB, and CSV references (Literature Toolkit).
  - `research_suggestions/`: Uses LLM prompts to brainstorm structured research directions.
  - `deep_explore/`: Advanced evidence processing using PubMed retrieval, background jobs, clustering, and AI gap extraction.
  - `llm/` and `literature_ai/`: Base LLM interaction via Google GenAI or potentially other providers.

## Frontend Structure (`/frontend/src/`)

- `main.tsx` & `App.tsx`: App Entrypoint, routing via `react-router-dom`, and main App layout.
- `context/`: `AuthContext.tsx` handles JWT storage and user state (credits, email).
- `pages/`: High-level views mapped directly to application routes (`LiteratureToolkit.tsx`, `ResearchSuggestions.tsx`, `DeepExplore.tsx`, `SearchBuilder.tsx`).
- `features/`: Extracted feature-specific components, hooks, and types (e.g., `research_suggestions/`, `auth/`).
- `lib/`: Shared utilities, including `literature_api.ts` which handles `fetch` commands with automatically injected `Authorization` headers.

## Data Flow (Literature Toolkit Example)
1. User uploads a file via the `LiteratureToolkit` page.
2. The UI triggers `convertFile()` in `lib/literature_api.ts`.
3. The request hits `convert.py` Router.
4. `get_current_user` verifies the JWT token.
5. `credit_service.has_sufficient_credits` checks if the user has enough credits.
6. Credits are reserved.
7. The file is parsed by `services/literature/parser_base.py`.
8. Converted bytes are stored via `services/literature/artifact_manager.py`.
9. The resulting payload is returned and displayed on the UI.
10. Credits deduction is finalized.
