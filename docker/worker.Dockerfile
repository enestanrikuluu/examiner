FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/worker/pyproject.toml .
COPY packages/shared/python /packages/shared/python

# Dev stage
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY apps/worker/ .
CMD ["celery", "-A", "src.celery_app", "worker", "-l", "debug", "-Q", "default,grading,generation,export,calibration"]

# Production stage: only runtime deps
FROM base AS prod
RUN pip install --no-cache-dir -e .
COPY apps/worker/ .
CMD ["celery", "-A", "src.celery_app", "worker", "-l", "info", "-Q", "default,grading,generation,export,calibration", "-c", "2"]
