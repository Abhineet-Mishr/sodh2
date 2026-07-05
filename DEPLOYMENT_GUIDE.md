# Deployment Guide

This guide covers how to deploy the SODH AI Research OS both locally using Docker and remotely on platforms like Render or Vercel.

## 1. Local Deployment (Docker Compose)
The easiest way to run the entire stack (PostgreSQL + pgvector and the FastAPI backend) is to use Docker Compose.

1. **Clone the repository.**
2. **Set up Environment Variables:**
   - Copy `backend/.env.example` to `backend/.env`.
   - Add your `GEMINI_API_KEY` to the `.env` file.
3. **Run Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   This will:
   - Start a PostgreSQL database with the `pgvector` extension.
   - Run `pre_start.py` to ensure the database is ready and the `vector` extension is created.
   - Run Alembic migrations to set up the schema.
   - Start the FastAPI backend on `http://localhost:8000`.

4. **Start the Frontend:**
   - Open a new terminal.
   - `cd frontend`
   - `npm install`
   - `npm run dev`
   - The frontend will be available at `http://localhost:5173`.

## 2. Remote Deployment (e.g., Render for Backend, Vercel for Frontend)

### Backend (Render)
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Set the **Root Directory** to `backend`.
4. Set the **Environment** to `Docker`. (Render will automatically detect the `backend/Dockerfile`).
5. Provision a **PostgreSQL Database** on Render.
   - **Important:** Ensure the database supports `pgvector`. (Render currently supports pgvector natively on newer Postgres versions, check their docs).
6. **Set Environment Variables:**
   - `DATABASE_URL`: The internal connection string provided by your Render PostgreSQL instance.
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `SECRET_KEY`: A secure random string for JWT token generation.
   - `FRONTEND_URL`: The URL of your deployed frontend (e.g., `https://my-research-os.vercel.app`).
7. **Deploy!** The `Dockerfile` will automatically run the `pre_start.py` script to wait for the DB, run migrations, and then start `uvicorn`.

### Frontend (Vercel)
1. Create a new project on Vercel and import your repository.
2. **Framework Preset:** Vercel should auto-detect **Vite**.
3. **Root Directory:** Set to `frontend`.
4. **Environment Variables:**
   - Add `VITE_API_BASE_URL` pointing to your deployed Render backend (e.g., `https://my-research-backend.onrender.com/api`).
5. **Deploy!**
