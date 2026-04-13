# Import dotfile
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

dev-backend: dev-backend-services dev-backend-migrations
	cd backend; uv sync --all-extras; uv run uvicorn app.main:app --reload --port $(BACKEND_PORT)

dev-frontend: dev-frontend-install
	cd frontend; pnpm dev --port $(FRONTEND_PORT)

dev-worker:
	cd worker; uv run uvicorn app.main:app --reload --port $(WORKER_PORT)

test-backend:
	uv run --project backend pytest tests/backend/acceptance

test-worker:
	uv run --project worker pytest tests/worker/acceptance

test-frontend:
	cd frontend; pnpm exec playwright test

dev-backend-services:
	docker compose --file docker-compose.services.yaml --env-file .env up --wait -d

dev-backend-migrations: dev-backend-services
	cd backend; DB_USER=$(DB_USER) DB_PASS=$(DB_PASS) DB_HOST=$(DB_HOST) DB_NAME=$(DB_NAME) uv run alembic upgrade head

dev-backend-services-down:
	docker compose --file docker-compose.services.yaml --env-file .env down

dev-backend-services-clean:
	docker compose --file docker-compose.services.yaml --env-file .env down --volumes --remove-orphans

dev-frontend-install:
	cd frontend; pnpm install
