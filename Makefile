.PHONY: bootstrap install test migrate runserver web-install web-dev web-build

bootstrap:
	./scripts/bootstrap.sh

install:
	pip install -e .

test:
	PYTHONPATH=services/backend pytest

migrate:
	python services/backend/manage.py migrate

runserver:
	python services/backend/manage.py runserver

web-install:
	pnpm install

web-dev:
	pnpm --filter @dealopia/web dev

web-build:
	pnpm --filter @dealopia/web build
