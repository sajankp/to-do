# FastTodo Developer Makefile
# Common tasks for development workflow
# Usage: make <target>

.PHONY: help setup dev test test-quick lint format docker-build docker-dev clean

# Default target - show help
help:
	@echo "FastTodo Development Commands:"
	@echo ""
	@echo "  make setup       - Install dependencies and pre-commit hooks"
	@echo "  make dev         - Start development server with hot-reload"
	@echo "  make test        - Run tests with coverage report"
	@echo "  make test-quick  - Run tests without coverage"
	@echo "  make lint        - Run ruff linter"
	@echo "  make format      - Auto-format code with ruff"
	@echo "  make docker-build- Build Docker image"
	@echo "  make docker-dev  - Start docker-compose stack"
	@echo "  make clean       - Remove cache and build files"
	@echo ""

# First-time setup
setup:
	@echo "🚀 Setting up development environment..."
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pre-commit install
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env from .env.example - edit with your credentials"; \
	else \
		echo "✅ .env already exists"; \
	fi
	@echo "✅ Setup complete! Activate venv with: source venv/bin/activate"

# Development server
dev:
	uvicorn app.main:app --reload --port 8000

# Run tests with coverage
test:
	pytest --cov=app --cov-report=term-missing --cov-report=html

# Run tests quickly without coverage
test-quick:
	pytest -q

# Linting
lint:
	ruff check app/

# Format code
format:
	ruff format app/
	ruff check --fix app/

# Build Docker image
docker-build:
	docker build -t fasttodo .

# Start docker-compose development stack
docker-dev:
	docker-compose up --build

# Stop docker-compose stack
docker-down:
	docker-compose down

# Clean up cache and build files
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	@echo "✅ Clean complete"
