.PHONY: bootstrap install test migrate runserver api-dev client-dev dev compose-up compose-down

bootstrap:
	bun install
	uv sync --project apps/api

install:
	uv sync --project apps/api

test:
	PYTHONPATH=apps/api pytest -c apps/api/pytest.ini

migrate:
	python apps/api/manage.py migrate

runserver:
	python apps/api/manage.py runserver

api-dev:
	PYTHONPATH=apps/api python apps/api/manage.py runserver

client-dev:
	bun --filter @dealopia/client dev

dev:
	bun run dev

compose-up:
	docker compose -f docker/docker-compose.yml up --build

compose-down:
	docker compose -f docker/docker-compose.yml down
