.PHONY: install test migrate runserver

install:
	pip install -e .

test:
	PYTHONPATH=services/backend pytest

migrate:
	python services/backend/manage.py migrate

runserver:
	python services/backend/manage.py runserver
