FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/worker/pyproject.toml .
COPY packages/shared/python /packages/shared/python

# Create stub package so pip can install dependencies
RUN mkdir -p src && touch src/__init__.py \
    && pip install --no-cache-dir -e .

# Dev stage
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY apps/worker/ .
CMD ["celery", "-A", "src.celery_app", "worker", "-l", "debug", "-Q", "default,grading,generation,export,calibration"]

# Production stage
FROM base AS prod
COPY apps/worker/ .
CMD ["celery", "-A", "src.celery_app", "worker", "-l", "info", "-Q", "default,grading,generation,export,calibration", "-c", "2"]
