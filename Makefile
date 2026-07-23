.PHONY: install dev-up dev-down migrate api worker test test-unit test-contract lint format security check smoke compose-smoke qa

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

worker:
	intake-worker

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
