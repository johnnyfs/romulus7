
db:
	docker compose --file docker-compose.services.yaml --env-file .env up --wait -d

db-down:
	docker compose --file docker-compose.services.yaml --env-file .env down

db-clean:
	docker compose --file docker-compose.services.yaml --env-file .env down -v db
