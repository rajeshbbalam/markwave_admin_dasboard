# Use Python 3.11 slim for Cloud Run compatibility
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements first for better layer caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Copy static frontend placeholder if it exists
COPY frontend/ ./frontend/ || true

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Health check endpoint
RUN mkdir -p /app/healthcheck && \
    echo 'import requests\nresponse = requests.get("http://localhost:8080/health")\nexit(0 if response.status_code == 200 else 1)' > /app/healthcheck/app.py

# Use gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
