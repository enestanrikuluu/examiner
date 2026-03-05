.PHONY: dev dev-infra dev-api dev-web dev-worker lint lint-api lint-web typecheck typecheck-api typecheck-web test test-api test-worker build clean migrate

# ── Development ──────────────────────────────────────────
dev-infra:
	docker compose -f docker-compose.yml up postgres redis minio -d

dev-api: dev-infra
	cd apps/api && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

dev-web:
	cd apps/web && npm run dev

dev-worker: dev-infra
	cd apps/worker && celery -A src.celery_app worker -l info -Q default,grading,generation,export,calibration

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# ── Linting ──────────────────────────────────────────────
lint-api:
	cd apps/api && ruff check src tests && ruff format --check src tests

lint-web:
	cd apps/web && npx eslint src

lint: lint-api lint-web

# ── Type checking ────────────────────────────────────────
typecheck-api:
	cd apps/api && mypy src

typecheck-web:
	cd apps/web && npx tsc --noEmit

typecheck: typecheck-api typecheck-web

# ── Testing ──────────────────────────────────────────────
test-api:
	cd apps/api && pytest tests -v --cov=src --cov-report=term-missing

test-worker:
	cd apps/worker && pytest tests -v

test: test-api test-worker

# ── Database ─────────────────────────────────────────────
migrate:
	cd apps/api && alembic upgrade head

migrate-create:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

# ── Docker ───────────────────────────────────────────────
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

# ── Formatting ───────────────────────────────────────────
format-api:
	cd apps/api && ruff format src tests && ruff check --fix src tests

format: format-api

# ── Install ──────────────────────────────────────────────
install-api:
	cd apps/api && pip install -e ".[dev]"

install-web:
	cd apps/web && npm install

install-worker:
	cd apps/worker && pip install -e ".[dev]"

install: install-api install-web install-worker
