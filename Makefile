.PHONY: install dev-up dev-down migrate api test lint format check

install:
	pip install -e .[dev]

dev-up:
	docker compose up --build

dev-down:
	docker compose down

migrate:
	alembic upgrade head

api:
	uvicorn intake.api:app --reload --host 127.0.0.1 --port 8000

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

check: lint test
