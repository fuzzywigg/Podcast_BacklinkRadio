# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    BUILD_TIMESTAMP=20251228_05

# Set working directory
WORKDIR /app

# Install system dependencies (git is often needed for some pip packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories that might be excluded by .dockerignore but needed
RUN mkdir -p hive/honeycomb/logs

# Run the web service on container startup
CMD ["uvicorn", "hive.main_service:app", "--host", "0.0.0.0", "--port", "8080"]
