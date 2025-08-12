.PHONY: up down rebuild logs test

up:
	docker compose up --build

down:
	docker compose down

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f

test:
	curl -s -X POST http://localhost:8000/analyze -H "Content-Type: application/json" -d '{"text":"I love clean code but hate bugs. Fast APIs are awesome!"}' | jq .