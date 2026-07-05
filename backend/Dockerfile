FROM python:3.12-slim

WORKDIR /app

# Install build dependencies and PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "bcrypt==3.2.2" tenacity

COPY . .

# Set Python path so imports work
ENV PYTHONPATH=/app

CMD ["bash", "-c", "python pre_start.py && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
