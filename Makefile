.PHONY: install dev-up dev-down prod-up prod-down migrate api worker demo test test-unit test-contract lint format security check smoke compose-smoke qa release-check

install:
	pip install -e .[dev]

dev-up:
	docker compose up --build

dev-down:
	docker compose down

prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

migrate:
	alembic upgrade head

api:
	uvicorn intake.api:app --reload --host 127.0.0.1 --port 8000

worker:
	intake-worker

demo:
	python scripts/seed_demo.py

test:
	pytest

test-unit:
	pytest -m "unit or not (contract or integration or smoke)"

test-contract:
	pytest -m contract

lint:
	ruff check .

format:
	ruff format .

security:
	bandit -q -r src/intake
	pip-audit

check: lint test-unit test-contract

smoke:
	bash scripts/smoke.sh

compose-smoke:
	@set -eu; \
		docker compose up -d --build; \
		trap 'docker compose down -v' EXIT; \
		bash scripts/smoke.sh

qa: check security compose-smoke

release-check: qa
	python -m build
