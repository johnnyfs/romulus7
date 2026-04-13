# Import dotfile
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

dev-backend: dev-backend-services dev-backend-migrations
	cd backend; uv run uvicorn app.main:app --reload --port $(BACKEND_PORT)

dev-frontend: dev-frontend-install
	cd frontend; pnpm dev --port $(FRONTEND_PORT)

dev-worker:
	cd worker; uv run uvicorn app.main:app --reload --port $(WORKER_PORT)

test-backend:
	uv run --project backend pytest tests/backend/acceptance

test-worker:
	uv run --project worker pytest tests/worker/acceptance

dev-test-worker: dev-backend-services dev-backend-migrations
	uv run --project worker pytest tests/worker/acceptance

dev-backend-services:
	docker compose --file docker-compose.services.yaml --env-file .env up --wait -d

dev-backend-migrations: dev-backend-services
	cd backend; uv run alembic upgrade head

dev-backend-services-down:
	docker compose --file docker-compose.services.yaml --env-file .env down

dev-backend-services-clean:
	docker compose --file docker-compose.services.yaml --env-file .env down -v db

dev-frontend-install:
	cd frontend; pnpm install
