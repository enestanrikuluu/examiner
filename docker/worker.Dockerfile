FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/worker/pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY packages/shared/python /packages/shared/python
COPY apps/worker/ .

CMD ["celery", "-A", "src.celery_app", "worker", "-l", "info", "-Q", "default,grading,generation,export,calibration"]
