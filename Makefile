dev-backend: dev-backend-services
	cd backend; uv run uvicorn app.main:app --reload

dev-frontend: dev-frontend-install
	cd frontend; pnpm dev

test-backend:
	uv run --project backend pytest tests/backend/acceptance

dev-backend-services:
	docker compose --file docker-compose.services.yaml --env-file .env up --wait -d

dev-backend-services-down:
	docker compose --file docker-compose.services.yaml --env-file .env down

dev-backend-services-clean:
	docker compose --file docker-compose.services.yaml --env-file .env down -v db

dev-frontend-install:
	cd frontend; pnpm install
