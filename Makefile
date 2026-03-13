.PHONY: help install install-dev install-prod test lint format type-check type-check-strict quality-gate ci-check ci-test precommit-full clean build up down restart logs

PYTHON_BIN ?= ./venv/bin/python
PYTEST_BIN ?= $(PYTHON_BIN) -m pytest
MYPY_BIN ?= $(PYTHON_BIN) -m mypy
STRICT_MYPY_TARGETS ?= config/ src/bot/core/alert_manager.py src/bot/core/alert_manager_models.py src/bot/core/lazy_imports.py src/bot/core/memory_mapped_files.py src/bot/core/smart_retry.py src/bot/core/anomaly src/bot/core/mmap src/bot/core/plugin_manager.py src/bot/core/logger_manager.py src/bot/core/config_manager.py src/bot/core/celery_app.py src/bot/core/backup_manager.py src/bot/core/priority_queue.py src/bot/core/archive_manager.py src/bot/core/health_monitor.py src/bot/core/command_health_monitor.py src/bot/core/command_alert_system.py src/bot/core/command_monitor_decorator.py src/bot/core/auto_recovery_handler.py src/bot/core/automation_system.py src/bot/core/recovery_manager.py src/bot/core/client_selector.py src/bot/core/thumbnail_manager.py src/bot/core/monitoring.py src/bot/core/performance_metrics_collector.py src/bot/core/bandwidth_limiter.py src/bot/core/metrics_server.py src/bot/core/logging_config.py src/bot/core/rate_limiter_models.py src/bot/core/batch_operations.py src/bot/core/enhanced_feedback_models.py src/bot/core/advanced_dashboard_html.py src/bot/core/api_gateway_models.py src/bot/core/batch_processor_models.py src/bot/core/cache_manager_models.py src/bot/core/celery_config.py src/bot/core/client_selector_models.py src/bot/core/connection_pool_manager_models.py src/bot/core/advanced_analytics.py src/bot/core/api_gateway_limiter.py src/bot/core/api_gateway_router.py src/bot/core/batch_processor.py src/bot/core/circuit_breaker.py src/bot/core/connection_pool_manager.py src/bot/core/task_models.py src/bot/core/performance_optimizer_models.py src/bot/core/query_optimizer_models.py src/bot/core/load_balancer_models.py src/bot/core/replication_models.py src/bot/core/rate_limiter.py src/bot/core/failover_models.py src/bot/core/cache_manager.py src/bot/core/caching.py src/bot/core/dashboard_html.py src/bot/core/debrid_manager.py src/bot/core/csrf_protection.py src/bot/core/drive_quota_bypass.py src/bot/core/cross_seed_farming.py src/bot/core/download_templates.py src/bot/core/blake3_hasher.py src/bot/core/api_gateway.py src/bot/core/health_models.py src/bot/core/index_generator.py src/bot/core/media_info.py src/bot/core/ml_anomaly_detection.py src/bot/core/recursive_extractor.py src/bot/core/salvage_mode.py src/bot/core/security_audit.py src/bot/core/gdrive_batch_optimizer.py src/bot/core/task_assignment_manager.py src/bot/core/task_execution_monitor.py src/bot/core/zero_copy_uploader.py src/bot/core/failover_cascade_detector.py src/bot/core/mfa_manager.py src/bot/core/mtproto_parallel_uploader.py src/bot/core/performance_scaling_engine.py src/bot/core/query_optimizer.py src/bot/core/replication_conflict_resolver.py src/bot/core/failover_recovery_executor.py src/bot/core/replication_sync_engine.py src/bot/core/task_categorizer.py src/bot/core/input_validator.py src/bot/core/link_bypassers.py src/bot/core/load_balancer.py src/bot/core/secrets_manager.py src/bot/core/security_headers.py src/bot/core/failover_manager.py src/bot/core/log_stream.py src/bot/core/smart_notifications.py src/bot/core/task_coordinator.py src/bot/core/replication_manager.py src/bot/core/secret_reader.py src/bot/core/web3_ipfs_storage.py src/bot/core/stream_proxy.py src/bot/core/web_dashboard.py src/bot/core/admin_auth.py src/bot/core/advanced_dashboard_websocket.py src/bot/core/memory_manager.py src/bot/core/advanced_cache.py src/bot/core/profiler.py src/bot/core/dashboard_manager.py src/bot/core/dashboard_routes.py src/bot/core/redis_manager.py src/bot/core/repositories/__init__.py src/bot/core/repositories/cache_repository.py src/bot/core/repositories/rate_limit_repository.py src/bot/core/repositories/session_repository.py src/bot/core/repositories/stats_repository.py src/bot/core/repositories/task_status_repository.py src/bot/core/databases.py src/bot/core/dlq_handler.py src/bot/core/edge_workers.py src/bot/core/load_tester.py src/bot/core/metadata_stripper.py src/bot/core/resilience.py src/bot/core/security.py src/bot/core/security_middleware.py src/bot/core/task_scheduler.py src/bot/core/file_cache_manager.py src/bot/core/handler_registry.py src/bot/core/handlers.py src/bot/core/core_handlers.py src/bot/core/enhanced_feedback.py src/bot/core/enhanced_stats.py src/bot/core/captcha_solver.py src/web/admin_auth.py src/web/admin_login.py src/bot/modules/history.py src/bot/modules/gd_delete.py src/bot/modules/shell.py

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
	@echo "  make type-check           Run type safety checks (non-strict)"
	@echo "  make type-check-strict    Run strict type checking on core modules"
	@echo "  make quality-gate         Run enforceable type-quality checks"
	@echo "  make ci-check             CI-ready enforceable quality sequence"
	@echo "  make ci-test              Run full test suite (currently has known collection issues)"
	@echo "  make precommit-full       Run full pre-commit hook suite (legacy backlog may fail)"
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
	$(MYPY_BIN) src/ config/ --pretty --show-error-codes || true

type-check:
	@echo "Running type safety checks..."
	$(MYPY_BIN) src/ config/ --pretty --show-error-codes
	@echo "✓ Type checking complete"

type-check-strict:
	@echo "Checking strict modules..."
	$(MYPY_BIN) --config-file pyproject.toml $(STRICT_MYPY_TARGETS) --pretty --show-error-codes
	@echo "✓ Strict type checking passed"

quality-gate:
	@echo "Running local quality gate..."
	$(MYPY_BIN) --config-file pyproject.toml $(STRICT_MYPY_TARGETS) --pretty --show-error-codes
	@echo "✓ Local quality gate passed"

ci-check:
	@echo "Running CI quality sequence..."
	$(MYPY_BIN) --config-file pyproject.toml $(STRICT_MYPY_TARGETS) --pretty --show-error-codes
	@echo "✓ CI quality sequence passed"

ci-test:
	@echo "Running full test suite..."
	$(PYTEST_BIN) tests/ -q

precommit-full:
	@echo "Running full pre-commit suite..."
	$(PYTHON_BIN) -m pre_commit run --all-files

format:
	@echo "Formatting with black..."
	black src/ tests/ --line-length=120
	@echo "Organizing imports..."
	isort src/ tests/ --profile black

test:
	$(PYTEST_BIN) tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-verbose:
	$(PYTEST_BIN) tests/ -vv --cov=src --cov-report=html --tb=short

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
