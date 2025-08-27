# TradingBot Pro - Makefile for Development and Deployment
# Usage: make <target>

.PHONY: help install dev prod test clean docker-build docker-up docker-down lint format security

# Default target
help:
	@echo "TradingBot Pro - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install all dependencies (backend + frontend)"
	@echo "  make dev         - Start development environment"
	@echo "  make dev-backend - Start backend development server only"
	@echo "  make dev-frontend- Start frontend development server only"
	@echo ""
	@echo "Production:"
	@echo "  make prod        - Deploy production environment with Docker"
	@echo "  make prod-build  - Build production Docker images"
	@echo "  make prod-up     - Start production containers"
	@echo "  make prod-down   - Stop production containers"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests (unit + integration + security)"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-security - Run security tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo ""
	@echo "Quality:"
	@echo "  make lint        - Run linting (backend + frontend)"
	@echo "  make format      - Format code (backend + frontend)"
	@echo "  make security    - Run security scans"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Clean build artifacts and cache"
	@echo "  make logs        - View production logs"
	@echo "  make health      - Check system health"
	@echo "  make backup      - Backup database"

# Installation targets
install: install-backend install-frontend
	@echo "✅ All dependencies installed successfully"

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install

# Development targets
dev: dev-setup
	@echo "🚀 Starting development environment..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:5000"
	@echo "Press Ctrl+C to stop all services"
	@make -j2 dev-backend dev-frontend

dev-setup:
	@echo "🔧 Setting up development environment..."
	@if not exist ".env" copy ".env.example" ".env"
	@echo "✅ Environment file ready"

dev-backend:
	@echo "🐍 Starting backend development server..."
	cd backend && python simple_app.py

dev-frontend:
	@echo "⚛️ Starting frontend development server..."
	cd frontend && npm start

# Production targets
prod: prod-setup prod-build prod-up
	@echo "🚀 Production environment deployed successfully!"
	@echo "Access your application at: http://localhost"

prod-setup:
	@echo "🔧 Setting up production environment..."
	@if not exist ".env" copy ".env.example" ".env"
	@echo "⚠️  Please configure your .env file with production settings"

prod-build:
	@echo "🏗️ Building production Docker images..."
	docker-compose -f docker-compose.prod.yml build --no-cache

prod-up:
	@echo "🚀 Starting production containers..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production environment is running"

prod-down:
	@echo "🛑 Stopping production containers..."
	docker-compose -f docker-compose.prod.yml down

prod-restart: prod-down prod-up
	@echo "🔄 Production environment restarted"

# Testing targets
test: test-unit test-integration test-security
	@echo "✅ All tests completed"

test-unit:
	@echo "🧪 Running unit tests..."
	cd backend && python -m pytest tests/unit/ -v --tb=short

test-integration:
	@echo "🔗 Running integration tests..."
	cd backend && python -m pytest tests/integration/ -v --tb=short

test-security:
	@echo "🔒 Running security tests..."
	cd backend && python -m pytest tests/security/ -v --tb=short

test-coverage:
	@echo "📊 Running tests with coverage..."
	cd backend && python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=70
	@echo "📈 Coverage report generated in backend/htmlcov/"

test-performance:
	@echo "⚡ Running performance tests..."
	cd backend && python -m pytest tests/performance/ -v --tb=short

# Quality targets
lint: lint-backend lint-frontend
	@echo "✅ Linting completed"

lint-backend:
	@echo "🔍 Linting backend code..."
	cd backend && python -m flake8 . --max-line-length=120 --exclude=migrations,venv,__pycache__
	cd backend && python -m pylint --rcfile=.pylintrc *.py || true

lint-frontend:
	@echo "🔍 Linting frontend code..."
	cd frontend && npm run lint || true

format: format-backend format-frontend
	@echo "✅ Code formatting completed"

format-backend:
	@echo "🎨 Formatting backend code..."
	cd backend && python -m black . --line-length=120
	cd backend && python -m isort . --profile black

format-frontend:
	@echo "🎨 Formatting frontend code..."
	cd frontend && npm run format || npx prettier --write src/

security:
	@echo "🔒 Running security scans..."
	cd backend && python -m bandit -r . -f json -o security-report.json || true
	cd backend && python -m safety check --json || true
	@echo "📋 Security reports generated"

# Docker targets
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build --no-cache

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker system prune -f
	docker volume prune -f

# Utility targets
clean:
	@echo "🧹 Cleaning build artifacts..."
	@if exist "backend\__pycache__" rmdir /s /q "backend\__pycache__"
	@if exist "backend\.pytest_cache" rmdir /s /q "backend\.pytest_cache"
	@if exist "backend\htmlcov" rmdir /s /q "backend\htmlcov"
	@if exist "backend\.coverage" del "backend\.coverage"
	@if exist "frontend\build" rmdir /s /q "frontend\build"
	@if exist "frontend\node_modules\.cache" rmdir /s /q "frontend\node_modules\.cache"
	@echo "✅ Cleanup completed"

logs:
	@echo "📋 Viewing production logs..."
	docker-compose -f docker-compose.prod.yml logs -f --tail=100

health:
	@echo "🏥 Checking system health..."
	@powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:5000/health' -Method Get | ConvertTo-Json } catch { Write-Host 'Backend health check failed' }"
	@powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3000' -Method Head | Select-Object StatusCode } catch { Write-Host 'Frontend health check failed' }"

backup:
	@echo "💾 Creating database backup..."
	@set BACKUP_FILE=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
	docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U trading_user trading_db > %BACKUP_FILE%
	@echo "✅ Database backup created: %BACKUP_FILE%"

# Database management
db-migrate:
	@echo "🗄️ Running database migrations..."
	cd backend && python -m flask db upgrade

db-reset:
	@echo "⚠️ Resetting database (WARNING: This will delete all data!)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@timeout /t 5
	cd backend && python recreate_db.py

db-seed:
	@echo "🌱 Seeding database with demo data..."
	cd backend && python create_demo_user.py

# License management
license-activate:
	@echo "🔑 Activating license..."
	python activate_license.py

license-check:
	@echo "🔍 Checking license status..."
	python -c "from backend.license_check import check_license; print('License valid' if check_license() else 'License invalid')"

# Quick start targets
quick-start: install dev-setup
	@echo "🚀 Quick start completed! Run 'make dev' to start development"

first-time-setup: install prod-setup db-migrate db-seed
	@echo "🎉 First-time setup completed!"
	@echo "Next steps:"
	@echo "1. Configure your .env file"
	@echo "2. Run 'make license-activate' to activate your license"
	@echo "3. Run 'make dev' for development or 'make prod' for production"

# Status and monitoring
status:
	@echo "📊 System Status:"
	@echo "=================="
	@docker-compose -f docker-compose.prod.yml ps 2>nul || echo "Production containers not running"
	@docker-compose ps 2>nul || echo "Development containers not running"
	@echo ""
	@make health

monitor:
	@echo "📈 Starting monitoring dashboard..."
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"
	docker-compose -f docker-compose.monitoring.yml up -d || echo "Monitoring stack not configured"

# Development utilities
shell-backend:
	@echo "🐍 Opening backend shell..."
	cd backend && python -i -c "from app import app; app.app_context().push()"

shell-db:
	@echo "🗄️ Opening database shell..."
	docker-compose -f docker-compose.prod.yml exec postgres psql -U trading_user -d trading_db

# Performance and optimization
optimize:
	@echo "⚡ Optimizing application..."
	@make clean
	@make format
	@make lint
	@echo "✅ Optimization completed"

benchmark:
	@echo "📊 Running performance benchmarks..."
	cd backend && python -m pytest tests/performance/ --benchmark-only

# Deployment helpers
deploy-staging: prod-build
	@echo "🚀 Deploying to staging..."
	docker-compose -f docker-compose.staging.yml up -d

deploy-production: prod-build
	@echo "🚀 Deploying to production..."
	@echo "⚠️ Make sure you have proper backups!"
	@timeout /t 10
	docker-compose -f docker-compose.prod.yml up -d

# Documentation
docs:
	@echo "📚 Generating documentation..."
	cd backend && python -m pydoc -w .
	@echo "📖 Documentation generated in backend/"

# Version and release management
version:
	@echo "📋 Version Information:"
	@echo "======================"
	@type "backend\requirements.txt" | findstr "^[^#]" | head -5
	@echo ""
	@cd frontend && npm list --depth=0 | head -10

# Help for specific environments
help-dev:
	@echo "🔧 Development Help:"
	@echo "=================="
	@echo "1. make install      - Install dependencies"
	@echo "2. make dev-setup    - Setup environment"
	@echo "3. make dev          - Start development servers"
	@echo "4. make test         - Run tests"
	@echo "5. make lint         - Check code quality"

help-prod:
	@echo "🚀 Production Help:"
	@echo "=================="
	@echo "1. make prod-setup   - Setup production environment"
	@echo "2. make prod-build   - Build Docker images"
	@echo "3. make prod-up      - Start production"
	@echo "4. make backup       - Backup database"
	@echo "5. make logs         - View logs"

# Default target when no target is specified
.DEFAULT_GOAL := help