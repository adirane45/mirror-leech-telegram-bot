.PHONY: help install install-dev install-prod test lint format clean build up down restart logs

help:
	@echo "Mirror-Leech Telegram Bot - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install              Install development dependencies"
	@echo "  make install-dev          Install dev + testing tools"
	@echo "  make install-prod         Install production dependencies only"
	@echo ""
	@echo "Development:"
	@echo "  make lint                 Run linters (pylint, flake8, mypy)"
	@echo "  make format               Format code with black and isort"
	@echo "  make test                 Run test suite with coverage"
	@echo "  make test-verbose         Run tests with verbose output"
	@echo ""
	@echo "Docker:"
	@echo "  make build                Build Docker image"
	@echo "  make up                   Start all services (compose)"
	@echo "  make down                 Stop all services"
	@echo "  make restart              Restart all services"
	@echo "  make logs                 View service logs"
	@echo "  make logs-app             View app logs only"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                Clean cache and artifacts"
	@echo "  make init-env             Create .env from .env.example"
	@echo "  make health-check         Check service health status"
	@echo "  make shell                Open Python shell with app context"
	@echo ""

# Installation targets
install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements/base.txt
	@echo "✓ Base dependencies installed"

install-dev:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements/dev.txt
	pre-commit install 2>/dev/null || true
	@echo "✓ Development environment ready"

install-prod:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements/prod.txt
	@echo "✓ Production dependencies installed"

# Code Quality
lint:
	@echo "Running pylint..."
	pylint src/ --disable=all --enable=E,F || true
	@echo "Running flake8..."
	flake8 src/ --max-line-length=120 --extend-ignore=E203,W503 || true
	@echo "Running mypy..."
	mypy src/ --ignore-missing-imports --no-error-summary || true

format:
	@echo "Formatting with black..."
	black src/ tests/ --line-length=120
	@echo "Organizing imports..."
	isort src/ tests/ --profile black

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-verbose:
	pytest tests/ -vv --cov=src --cov-report=html --tb=short

# Docker targets
build:
	docker compose -f deployment/compose/docker-compose.yml build

up:
	docker compose -f deployment/compose/docker-compose.yml up -d
	@echo "✓ All services started"
	sleep 5
	@$(MAKE) health-check

down:
	docker compose -f deployment/compose/docker-compose.yml down
	@echo "✓ All services stopped"

restart:
	docker compose -f deployment/compose/docker-compose.yml restart
	@echo "✓ All services restarted"
	sleep 5
	@$(MAKE) health-check

logs:
	docker compose -f deployment/compose/docker-compose.yml logs -f --tail=50

logs-app:
	docker compose -f deployment/compose/docker-compose.yml logs -f mltb-app --tail=100

# Utilities
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✓ Cleaned cache and artifacts"

init-env:
	@if [ ! -f config/.env.production ]; then \
		cp config/.env.example config/.env.production; \
		echo "✓ Created config/.env.production from template"; \
		echo "⚠️  Update config/.env.production with your credentials"; \
	else \
		echo "⚠️  config/.env.production already exists"; \
	fi

health-check:
	@echo "Checking service health..."
	@docker compose -f deployment/compose/docker-compose.yml ps --format "table {{.Service}}\t{{.Status}}" || echo "Docker Compose not running"

shell:
	python -i -c "import sys; sys.path.insert(0, 'src'); from bot import LOGGER"

# Git helpers
commit-format:
	git add -A
	git commit -m "style: Format code with black/isort"

commit-fix:
	@read -p "Enter fix description: " desc; \
	git add -A; \
	git commit -m "fix: $$desc"

# Development server
dev:
	PYTHONPATH=/app/src:$$PYTHONPATH ENVIRONMENT=development python -m uvicorn src.web.wserver:app --reload --port 8060

prod:
	PYTHONPATH=/app/src:$$PYTHONPATH ENVIRONMENT=production gunicorn src.web.wserver:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8060

.DEFAULT_GOAL := help
