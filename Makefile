.PHONY: help up down build logs test lint clean

help:
	@echo "datasecurely Scanner Makefile"
	@echo "  up       - Start all Docker Compose services"
	@echo "  down     - Stop all Docker Compose services"
	@echo "  build    - Build Docker images"
	@echo "  logs     - Follow container logs"
	@echo "  test     - Run pytest test suite"
	@echo "  lint     - Run ruff linter"
	@echo "  clean    - Remove build and test artifacts"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	pytest backend/tests -v

lint:
	ruff check backend/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
