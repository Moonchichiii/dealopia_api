.PHONY: bootstrap install test migrate runserver api-dev client-dev dev compose-up compose-down

bootstrap:
	./scripts/bootstrap.sh

install:
	uv pip install -e .

test:
	PYTHONPATH=apps/api pytest

migrate:
	python apps/api/manage.py migrate

runserver:
	python apps/api/manage.py runserver

api-dev:
	python apps/api/manage.py runserver

client-dev:
	bun --filter @dealopia/client dev

dev:
	@echo "Run API and Client in separate terminals: make api-dev / make client-dev"

compose-up:
	docker compose -f docker/docker-compose.yml up --build

compose-down:
	docker compose -f docker/docker-compose.yml down
