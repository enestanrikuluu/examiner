FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml .
COPY packages/shared/python /packages/shared/python

# Dev stage: includes test/lint tools + hot reload
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY apps/api/ .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage: only runtime deps
FROM base AS prod
RUN pip install --no-cache-dir -e .
COPY apps/api/ .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
