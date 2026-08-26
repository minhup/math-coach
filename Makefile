SHELL := /bin/bash

API_DIR := services/api
PLAYWRIGHT_IMAGE := mcr.microsoft.com/playwright:v1.62.1-noble
PYTHON := uv run --project $(API_DIR)
RUFF := $(PYTHON) ruff --config $(API_DIR)/pyproject.toml
TEST_ENV := MATH_COACH_ENVIRONMENT=test MATH_COACH_DATABASE_URL=postgresql+asyncpg://math_coach:math_coach_dev@localhost:5432/math_coach_test MATH_COACH_OBJECT_STORAGE_BUCKET=math-coach-test

.PHONY: setup format format-check lint typecheck test-unit test-integration test-e2e content-schema-generate content-validate test check services services-down migrate seed api-generate api-contract-check build dev-api dev-web

setup:
	npm ci
	uv sync --project $(API_DIR) --all-groups --locked
	docker pull $(PLAYWRIGHT_IMAGE)
	$(MAKE) services migrate seed

format:
	npm run format
	$(RUFF) format services/api scripts

format-check:
	npm run format:check
	$(RUFF) format --check services/api scripts

lint:
	npm run lint
	$(RUFF) check services/api scripts

typecheck:
	npm run typecheck
	cd $(API_DIR) && uv run mypy app

test-unit:
	npm run test:unit
	cd $(API_DIR) && uv run pytest -m "not integration"

test-integration: services
	cd $(API_DIR) && $(TEST_ENV) uv run alembic downgrade base
	cd $(API_DIR) && $(TEST_ENV) uv run alembic upgrade head
	cd $(API_DIR) && $(TEST_ENV) uv run alembic downgrade base
	cd $(API_DIR) && $(TEST_ENV) uv run alembic upgrade head
	cd $(API_DIR) && $(TEST_ENV) uv run pytest -m integration

test-e2e: services migrate seed build
	./scripts/run_e2e.sh

content-validate:
	cd $(API_DIR) && uv run python -m app.scripts.validate_content ../../content ../../packages/content-schema/content-package.schema.json

content-schema-generate:
	cd $(API_DIR) && uv run python -m app.scripts.export_content_schema ../../packages/content-schema/content-package.schema.json

test: test-unit test-integration test-e2e

check: format-check lint typecheck api-contract-check content-validate build test

services:
	docker compose up -d --wait

services-down:
	docker compose down

migrate:
	cd $(API_DIR) && uv run alembic upgrade head

seed:
	cd $(API_DIR) && uv run python -m app.scripts.seed_dev
	cd $(API_DIR) && uv run python -m app.scripts.seed_content ../../content

api-generate:
	cd $(API_DIR) && uv run python -m app.scripts.export_openapi ../../packages/api-client/openapi.json
	npm run api:generate

api-contract-check:
	./scripts/check_api_contract.sh

build:
	npm run build

dev-api:
	cd $(API_DIR) && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	npm run dev:web
