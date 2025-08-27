@echo off
REM TradingBot Pro - Windows Batch Script for Development and Deployment
REM Usage: make.bat <target>

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="install-backend" goto install-backend
if "%1"=="install-frontend" goto install-frontend
if "%1"=="dev" goto dev
if "%1"=="dev-setup" goto dev-setup
if "%1"=="dev-backend" goto dev-backend
if "%1"=="dev-frontend" goto dev-frontend
if "%1"=="prod" goto prod
if "%1"=="prod-setup" goto prod-setup
if "%1"=="prod-build" goto prod-build
if "%1"=="prod-up" goto prod-up
if "%1"=="prod-down" goto prod-down
if "%1"=="prod-restart" goto prod-restart
if "%1"=="test" goto test
if "%1"=="test-unit" goto test-unit
if "%1"=="test-integration" goto test-integration
if "%1"=="test-security" goto test-security
if "%1"=="test-coverage" goto test-coverage
if "%1"=="test-performance" goto test-performance
if "%1"=="lint" goto lint
if "%1"=="lint-backend" goto lint-backend
if "%1"=="lint-frontend" goto lint-frontend
if "%1"=="format" goto format
if "%1"=="format-backend" goto format-backend
if "%1"=="format-frontend" goto format-frontend
if "%1"=="security" goto security
if "%1"=="docker-build" goto docker-build
if "%1"=="docker-up" goto docker-up
if "%1"=="docker-down" goto docker-down
if "%1"=="docker-logs" goto docker-logs
if "%1"=="docker-clean" goto docker-clean
if "%1"=="clean" goto clean
if "%1"=="logs" goto logs
if "%1"=="health" goto health
if "%1"=="backup" goto backup
if "%1"=="db-migrate" goto db-migrate
if "%1"=="db-reset" goto db-reset
if "%1"=="db-seed" goto db-seed
if "%1"=="license-activate" goto license-activate
if "%1"=="license-check" goto license-check
if "%1"=="quick-start" goto quick-start
if "%1"=="first-time-setup" goto first-time-setup
if "%1"=="status" goto status
if "%1"=="monitor" goto monitor
if "%1"=="shell-backend" goto shell-backend
if "%1"=="shell-db" goto shell-db
if "%1"=="optimize" goto optimize
if "%1"=="benchmark" goto benchmark
if "%1"=="deploy-staging" goto deploy-staging
if "%1"=="deploy-production" goto deploy-production
if "%1"=="docs" goto docs
if "%1"=="version" goto version
if "%1"=="help-dev" goto help-dev
if "%1"=="help-prod" goto help-prod

echo Unknown target: %1
goto help

:help
echo TradingBot Pro - Available Commands:
echo.
echo Development:
echo   make.bat install     - Install all dependencies (backend + frontend)
echo   make.bat dev         - Start development environment
echo   make.bat dev-backend - Start backend development server only
echo   make.bat dev-frontend- Start frontend development server only
echo.
echo Production:
echo   make.bat prod        - Deploy production environment with Docker
echo   make.bat prod-build  - Build production Docker images
echo   make.bat prod-up     - Start production containers
echo   make.bat prod-down   - Stop production containers
echo.
echo Testing:
echo   make.bat test        - Run all tests (unit + integration + security)
echo   make.bat test-unit   - Run unit tests only
echo   make.bat test-integration - Run integration tests only
echo   make.bat test-security - Run security tests only
echo   make.bat test-coverage - Run tests with coverage report
echo.
echo Quality:
echo   make.bat lint        - Run linting (backend + frontend)
echo   make.bat format      - Format code (backend + frontend)
echo   make.bat security    - Run security scans
echo.
echo Utilities:
echo   make.bat clean       - Clean build artifacts and cache
echo   make.bat logs        - View production logs
echo   make.bat health      - Check system health
echo   make.bat backup      - Backup database
echo.
echo For more help: make.bat help-dev or make.bat help-prod
goto end

:install
echo 📦 Installing all dependencies...
call :install-backend
call :install-frontend
echo ✅ All dependencies installed successfully
goto end

:install-backend
echo 📦 Installing backend dependencies...
cd backend
pip install -r requirements.txt
cd ..
goto end

:install-frontend
echo 📦 Installing frontend dependencies...
cd frontend
npm install
cd ..
goto end

:dev
echo 🚀 Starting development environment...
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:5000
echo Press Ctrl+C to stop all services
call :dev-setup
start /b cmd /c "cd backend && python simple_app.py"
start /b cmd /c "cd frontend && npm start"
echo Development servers started in background
goto end

:dev-setup
echo 🔧 Setting up development environment...
if not exist ".env" copy ".env.example" ".env"
echo ✅ Environment file ready
goto end

:dev-backend
echo 🐍 Starting backend development server...
cd backend
python simple_app.py
cd ..
goto end

:dev-frontend
echo ⚛️ Starting frontend development server...
cd frontend
npm start
cd ..
goto end

:prod
echo 🚀 Deploying production environment...
call :prod-setup
call :prod-build
call :prod-up
echo 🚀 Production environment deployed successfully!
echo Access your application at: http://localhost
goto end

:prod-setup
echo 🔧 Setting up production environment...
if not exist ".env" copy ".env.example" ".env"
echo ⚠️  Please configure your .env file with production settings
goto end

:prod-build
echo 🏗️ Building production Docker images...
docker-compose -f docker-compose.prod.yml build --no-cache
goto end

:prod-up
echo 🚀 Starting production containers...
docker-compose -f docker-compose.prod.yml up -d
echo ✅ Production environment is running
goto end

:prod-down
echo 🛑 Stopping production containers...
docker-compose -f docker-compose.prod.yml down
goto end

:prod-restart
call :prod-down
call :prod-up
echo 🔄 Production environment restarted
goto end

:test
echo 🧪 Running all tests...
call :test-unit
call :test-integration
call :test-security
echo ✅ All tests completed
goto end

:test-unit
echo 🧪 Running unit tests...
cd backend
python -m pytest tests/unit/ -v --tb=short
cd ..
goto end

:test-integration
echo 🔗 Running integration tests...
cd backend
python -m pytest tests/integration/ -v --tb=short
cd ..
goto end

:test-security
echo 🔒 Running security tests...
cd backend
python -m pytest tests/security/ -v --tb=short
cd ..
goto end

:test-coverage
echo 📊 Running tests with coverage...
cd backend
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=70
echo 📈 Coverage report generated in backend/htmlcov/
cd ..
goto end

:test-performance
echo ⚡ Running performance tests...
cd backend
python -m pytest tests/performance/ -v --tb=short
cd ..
goto end

:lint
echo 🔍 Running linting...
call :lint-backend
call :lint-frontend
echo ✅ Linting completed
goto end

:lint-backend
echo 🔍 Linting backend code...
cd backend
python -m flake8 . --max-line-length=120 --exclude=migrations,venv,__pycache__
python -m pylint --rcfile=.pylintrc *.py 2>nul
cd ..
goto end

:lint-frontend
echo 🔍 Linting frontend code...
cd frontend
npm run lint 2>nul
cd ..
goto end

:format
echo 🎨 Formatting code...
call :format-backend
call :format-frontend
echo ✅ Code formatting completed
goto end

:format-backend
echo 🎨 Formatting backend code...
cd backend
python -m black . --line-length=120
python -m isort . --profile black
cd ..
goto end

:format-frontend
echo 🎨 Formatting frontend code...
cd frontend
npm run format 2>nul || npx prettier --write src/
cd ..
goto end

:security
echo 🔒 Running security scans...
cd backend
python -m bandit -r . -f json -o security-report.json 2>nul
python -m safety check --json 2>nul
echo 📋 Security reports generated
cd ..
goto end

:docker-build
echo 🐳 Building Docker images...
docker-compose build --no-cache
goto end

:docker-up
echo 🐳 Starting Docker containers...
docker-compose up -d
goto end

:docker-down
echo 🐳 Stopping Docker containers...
docker-compose down
goto end

:docker-logs
echo 📋 Viewing Docker logs...
docker-compose logs -f
goto end

:docker-clean
echo 🧹 Cleaning Docker resources...
docker system prune -f
docker volume prune -f
goto end

:clean
echo 🧹 Cleaning build artifacts...
if exist "backend\__pycache__" rmdir /s /q "backend\__pycache__"
if exist "backend\.pytest_cache" rmdir /s /q "backend\.pytest_cache"
if exist "backend\htmlcov" rmdir /s /q "backend\htmlcov"
if exist "backend\.coverage" del "backend\.coverage"
if exist "frontend\build" rmdir /s /q "frontend\build"
if exist "frontend\node_modules\.cache" rmdir /s /q "frontend\node_modules\.cache"
echo ✅ Cleanup completed
goto end

:logs
echo 📋 Viewing production logs...
docker-compose -f docker-compose.prod.yml logs -f --tail=100
goto end

:health
echo 🏥 Checking system health...
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:5000/health' -Method Get | ConvertTo-Json } catch { Write-Host 'Backend health check failed' }"
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3000' -Method Head | Select-Object StatusCode } catch { Write-Host 'Frontend health check failed' }"
goto end

:backup
echo 💾 Creating database backup...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/: " %%a in ("%TIME%") do (set mytime=%%a%%b)
set BACKUP_FILE=backup_%mydate%_%mytime%.sql
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U trading_user trading_db > %BACKUP_FILE%
echo ✅ Database backup created: %BACKUP_FILE%
goto end

:db-migrate
echo 🗄️ Running database migrations...
cd backend
python -m flask db upgrade
cd ..
goto end

:db-reset
echo ⚠️ Resetting database (WARNING: This will delete all data!)
echo Press Ctrl+C to cancel, or wait 5 seconds to continue...
timeout /t 5
cd backend
python recreate_db.py
cd ..
goto end

:db-seed
echo 🌱 Seeding database with demo data...
cd backend
python create_demo_user.py
cd ..
goto end

:license-activate
echo 🔑 Activating license...
python activate_license.py
goto end

:license-check
echo 🔍 Checking license status...
python -c "from backend.license_check import check_license; print('License valid' if check_license() else 'License invalid')"
goto end

:quick-start
echo 🚀 Quick start setup...
call :install
call :dev-setup
echo 🚀 Quick start completed! Run 'make.bat dev' to start development
goto end

:first-time-setup
echo 🎉 First-time setup...
call :install
call :prod-setup
call :db-migrate
call :db-seed
echo 🎉 First-time setup completed!
echo Next steps:
echo 1. Configure your .env file
echo 2. Run 'make.bat license-activate' to activate your license
echo 3. Run 'make.bat dev' for development or 'make.bat prod' for production
goto end

:status
echo 📊 System Status:
echo ==================
docker-compose -f docker-compose.prod.yml ps 2>nul || echo Production containers not running
docker-compose ps 2>nul || echo Development containers not running
echo.
call :health
goto end

:monitor
echo 📈 Starting monitoring dashboard...
echo Grafana: http://localhost:3001
echo Prometheus: http://localhost:9090
docker-compose -f docker-compose.monitoring.yml up -d 2>nul || echo Monitoring stack not configured
goto end

:shell-backend
echo 🐍 Opening backend shell...
cd backend
python -i -c "from app import app; app.app_context().push()"
cd ..
goto end

:shell-db
echo 🗄️ Opening database shell...
docker-compose -f docker-compose.prod.yml exec postgres psql -U trading_user -d trading_db
goto end

:optimize
echo ⚡ Optimizing application...
call :clean
call :format
call :lint
echo ✅ Optimization completed
goto end

:benchmark
echo 📊 Running performance benchmarks...
cd backend
python -m pytest tests/performance/ --benchmark-only
cd ..
goto end

:deploy-staging
echo 🚀 Deploying to staging...
call :prod-build
docker-compose -f docker-compose.staging.yml up -d
goto end

:deploy-production
echo 🚀 Deploying to production...
echo ⚠️ Make sure you have proper backups!
timeout /t 10
call :prod-build
docker-compose -f docker-compose.prod.yml up -d
goto end

:docs
echo 📚 Generating documentation...
cd backend
python -m pydoc -w .
echo 📖 Documentation generated in backend/
cd ..
goto end

:version
echo 📋 Version Information:
echo ======================
type "backend\requirements.txt" | findstr "^[^#]" | head -5
echo.
cd frontend
npm list --depth=0 | head -10
cd ..
goto end

:help-dev
echo 🔧 Development Help:
echo ==================
echo 1. make.bat install      - Install dependencies
echo 2. make.bat dev-setup    - Setup environment
echo 3. make.bat dev          - Start development servers
echo 4. make.bat test         - Run tests
echo 5. make.bat lint         - Check code quality
goto end

:help-prod
echo 🚀 Production Help:
echo ==================
echo 1. make.bat prod-setup   - Setup production environment
echo 2. make.bat prod-build   - Build Docker images
echo 3. make.bat prod-up      - Start production
echo 4. make.bat backup       - Backup database
echo 5. make.bat logs         - View logs
goto end

:end