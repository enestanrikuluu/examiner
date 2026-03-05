FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml .
COPY packages/shared/python /packages/shared/python

# Create stub package so pip can install dependencies
RUN mkdir -p src && touch src/__init__.py \
    && pip install --no-cache-dir -e .

# Dev stage: includes test/lint tools + hot reload
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY apps/api/ .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS prod
COPY apps/api/ .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
