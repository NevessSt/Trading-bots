# Makefile for Trading Bot Platform Testing and Development

.PHONY: help install install-dev test test-unit test-integration test-e2e test-security test-performance
.PHONY: test-all test-fast test-slow coverage lint type-check security-scan format clean
.PHONY: load-test stress-test smoke-test regression-test setup-db migrate-db seed-db
.PHONY: start-services stop-services restart-services logs build deploy docs

# Default target
help:
	@echo "Trading Bot Platform - Development Commands"
	@echo "==========================================="
	@echo ""
	@echo "Installation:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development and testing dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e         Run end-to-end tests only"
	@echo "  test-security    Run security tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-fast        Run fast tests (unit + integration)"
	@echo "  test-slow        Run slow tests (e2e + performance)"
	@echo "  smoke-test       Run smoke tests"
	@echo "  regression-test  Run regression tests"
	@echo ""
	@echo "Load Testing:"
	@echo "  load-test        Run load tests (10 users, 30s)"
	@echo "  stress-test      Run stress tests (100 users, 60s)"
	@echo ""
	@echo "Code Quality:"
	@echo "  coverage         Generate test coverage report"
	@echo "  lint             Run code linting"
	@echo "  type-check       Run type checking"
	@echo "  security-scan    Run security scanning"
	@echo "  format           Format code with black and isort"
	@echo ""
	@echo "Database:"
	@echo "  setup-db         Set up test database"
	@echo "  migrate-db       Run database migrations"
	@echo "  seed-db          Seed database with test data"
	@echo ""
	@echo "Services:"
	@echo "  start-services   Start required services (Redis, etc.)"
	@echo "  stop-services    Stop services"
	@echo "  restart-services Restart services"
	@echo "  logs             Show service logs"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up temporary files and caches"
	@echo "  build            Build the application"
	@echo "  docs             Generate documentation"
	@echo ""

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install -e .

# Testing targets
test:
	python run_tests.py --all

test-unit:
	python run_tests.py --unit

test-integration:
	python run_tests.py --integration

test-e2e:
	python run_tests.py --e2e

test-security:
	python run_tests.py --security

test-performance:
	python run_tests.py --performance

test-fast:
	pytest tests/unit/ tests/integration/ -v --tb=short

test-slow:
	pytest tests/e2e/ tests/performance/ -v --tb=short -m "slow"

smoke-test:
	pytest -m "smoke" -v --tb=short

regression-test:
	pytest -m "regression" -v --tb=short

# Load testing targets
load-test:
	python run_tests.py --load --load-users 10 --load-duration 30s

stress-test:
	python run_tests.py --load --load-users 100 --load-duration 60s

# Code quality targets
coverage:
	python run_tests.py --coverage

lint:
	python run_tests.py --lint

type-check:
	python run_tests.py --type-check

security-scan:
	python run_tests.py --security-scan

format:
	black .
	isort .
	flake8 . --count --statistics

# Database targets
setup-db:
	@echo "Setting up test database..."
	flask db init || true
	flask db migrate -m "Initial migration" || true
	flask db upgrade

migrate-db:
	flask db migrate
	flask db upgrade

seed-db:
	python scripts/seed_test_data.py

# Service management (Windows compatible)
start-services:
	@echo "Starting services..."
	@echo "Note: Please ensure Redis is running manually on Windows"
	@echo "Redis can be started with: redis-server"

stop-services:
	@echo "Stopping services..."
	@echo "Note: Please stop Redis manually on Windows"

restart-services: stop-services start-services

logs:
	@echo "Checking logs..."
	@if exist logs\app.log (type logs\app.log) else (echo "No logs found")

# Utility targets
clean:
	@echo "Cleaning up..."
	@if exist __pycache__ (rmdir /s /q __pycache__)
	@if exist .pytest_cache (rmdir /s /q .pytest_cache)
	@if exist .coverage (del .coverage)
	@if exist htmlcov (rmdir /s /q htmlcov)
	@if exist test-results (rmdir /s /q test-results)
	@if exist .mypy_cache (rmdir /s /q .mypy_cache)
	@if exist .tox (rmdir /s /q .tox)
	@if exist dist (rmdir /s /q dist)
	@if exist build (rmdir /s /q build)
	@if exist *.egg-info (rmdir /s /q *.egg-info)
	@for /r %%i in (*.pyc) do @del "%%i" 2>nul
	@for /r %%i in (*.pyo) do @del "%%i" 2>nul
	@echo "Cleanup complete!"

build:
	@echo "Building application..."
	python setup.py build

docs:
	@echo "Generating documentation..."
	@if exist docs (cd docs && make html) else (echo "No docs directory found")

# Development workflow targets
dev-setup: install-dev setup-db
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything is working."

dev-test: format lint type-check test-fast
	@echo "Development testing complete!"

ci-test: test-all coverage security-scan
	@echo "CI testing complete!"

full-test: clean dev-test test-slow load-test
	@echo "Full testing suite complete!"

# Quick commands for common workflows
quick-test:
	pytest tests/unit/ -x -v

watch-test:
	pytest-watch tests/unit/

debug-test:
	pytest tests/unit/ -x -v -s --pdb

# Performance profiling
profile-test:
	pytest tests/performance/ --profile

memory-test:
	pytest tests/performance/ --memory-profile

# Security focused testing
security-full:
	bandit -r . -f json -o test-results/bandit-report.json
	safety check --json --output test-results/safety-report.json
	pytest tests/security/ -v

# API testing
api-test:
	pytest tests/integration/test_api/ -v

# Database testing
db-test:
	pytest tests/integration/test_database/ -v

# WebSocket testing
ws-test:
	pytest tests/integration/ -k "websocket" -v

# Parallel testing
parallel-test:
	pytest tests/ -n auto

# Test with specific markers
test-critical:
	pytest -m "critical" -v

test-flaky:
	pytest -m "flaky" --reruns 3 -v

# Environment specific tests
test-windows:
	pytest -m "windows_only" -v

test-linux:
	pytest -m "linux_only" -v

# Coverage targets with different thresholds
coverage-strict:
	pytest --cov=. --cov-fail-under=90

coverage-report:
	coverage html
	coverage report --show-missing

# Benchmark testing
benchmark:
	pytest tests/performance/ --benchmark-only

# Test data management
generate-test-data:
	python scripts/generate_test_data.py

clean-test-data:
	python scripts/clean_test_data.py

# Docker related (if using Docker)
docker-test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-clean:
	docker-compose -f docker-compose.test.yml down -v

# Continuous testing
watch:
	pytest-watch tests/ --clear

# Test report generation
report:
	allure generate test-results/allure-results -o test-results/allure-report --clean
	allure open test-results/allure-report

# Help for specific categories
help-testing:
	@echo "Testing Commands:"
	@echo "  test-unit        - Fast unit tests"
	@echo "  test-integration - API and database tests"
	@echo "  test-e2e         - Full workflow tests"
	@echo "  test-security    - Security vulnerability tests"
	@echo "  test-performance - Performance and load tests"

help-quality:
	@echo "Code Quality Commands:"
	@echo "  lint            - Check code style and quality"
	@echo "  type-check      - Verify type annotations"
	@echo "  security-scan   - Scan for security issues"
	@echo "  format          - Auto-format code"

help-coverage:
	@echo "Coverage Commands:"
	@echo "  coverage        - Generate coverage report"
	@echo "  coverage-strict - Require 90% coverage"
	@echo "  coverage-report - Generate HTML coverage report"

# Version and info
version:
	@python -c "import sys; print(f'Python {sys.version}')"
	@python -c "import pytest; print(f'pytest {pytest.__version__}')"
	@python -c "try: import flask; print(f'Flask {flask.__version__}'); except: print('Flask not installed')"

info:
	@echo "Trading Bot Platform Test Suite"
	@echo "==============================="
	@echo "Test files: $(shell find tests -name '*.py' | wc -l)"
	@echo "Source files: $(shell find . -name '*.py' -not -path './tests/*' -not -path './venv/*' | wc -l)"
	@echo "Last test run: $(shell if exist test-results\junit.xml (echo 'Available') else (echo 'Not found'))"