FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY packages/shared/python /packages/shared/python
COPY apps/api/ .

# Dev stage with hot reload
FROM base AS dev
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS prod
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
