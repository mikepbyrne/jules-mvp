.PHONY: help install dev test lint format clean docker-up docker-down migrate migrate-create db-shell

help:
	@echo "Jules Backend - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies with Poetry"
	@echo "  make dev           Start development server"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     Start all services with Docker Compose"
	@echo "  make docker-down   Stop all services"
	@echo "  make docker-logs   View API logs"
	@echo "  make docker-shell  Open shell in API container"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       Run database migrations"
	@echo "  make migrate-create MSG='description'  Create new migration"
	@echo "  make db-shell      Open PostgreSQL shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make test-watch    Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run linters (ruff, mypy)"
	@echo "  make format        Format code with black"
	@echo "  make check         Run all checks (lint + test)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove temporary files"

# Setup
install:
	poetry install

dev:
	poetry run uvicorn src.main:app --reload --port 8000

# Docker
docker-up:
	docker-compose up -d
	@echo "Services started. API: http://localhost:8000, Docs: http://localhost:8000/docs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-shell:
	docker-compose exec api /bin/bash

docker-restart:
	docker-compose restart api

# Database
migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	poetry run alembic downgrade -1

db-shell:
	docker-compose exec postgres psql -U jules -d jules_dev

# Testing
test:
	poetry run pytest -v

test-cov:
	poetry run pytest -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-watch:
	poetry run ptw -- -v

test-integration:
	docker-compose run --rm api pytest tests/test_api_webhooks.py -v

# Code Quality
lint:
	poetry run ruff check src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run ruff check --fix src tests

check: lint test

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

# Production
build:
	docker build --target production -t jules-backend:latest .

run-prod:
	docker run -d -p 8000:8000 --env-file .env jules-backend:latest
