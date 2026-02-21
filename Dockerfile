# Base Image
FROM python:3.10-slim

# Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System Dependencies
# Needed for psycopg2 + SSL + curl (healthcheck)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create App Directory
WORKDIR /app

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy Application Code
COPY . .

# Create Logs Directory
# (Required for structured logging volume mount)
RUN mkdir -p /app/logs && touch /app/logs/agent_activity.log

# Expose API Port
EXPOSE 8000

# Default Command (API)
# Celery will override this in docker-compose
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
