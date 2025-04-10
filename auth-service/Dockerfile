# Build stage – install dependencies
FROM python:3.11-alpine AS build-stage

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for building packages like psycopg2-binary
RUN apk add --no-cache gcc musl-dev libpq-dev

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Final stage – runtime only
FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Add only runtime dependencies
RUN apk add --no-cache libpq

WORKDIR /app

# Copy all installed Python packages and binaries from build stage
COPY --from=build-stage /usr/local /usr/local

# Copy application source code
COPY . .

# Remove pip cache (cleanup)
RUN rm -rf /root/.cache

# Expose FastAPI port
EXPOSE 8002

# Default command to start FastAPI backend
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]