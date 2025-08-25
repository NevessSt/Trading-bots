@echo off
REM =============================================================================
REM Trading Bot Docker Deployment Script for Windows
REM =============================================================================

echo ========================================
echo Trading Bot Docker Deployment
echo ========================================
echo.

REM Check if Docker is installed and running
echo [1/8] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)
echo Docker is installed and running ✓
echo.

REM Check if docker-compose is available
echo [2/8] Checking Docker Compose...
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not available
    echo Please ensure you have Docker Desktop with Compose support
    pause
    exit /b 1
)
echo Docker Compose is available ✓
echo.

REM Setup environment file
echo [3/8] Setting up environment configuration...
if not exist ".env" (
    if exist ".env.docker" (
        copy ".env.docker" ".env"
        echo Environment file created from template ✓
        echo.
        echo IMPORTANT: Please edit .env file with your actual configuration:
        echo - Database passwords
        echo - API keys for trading exchanges
        echo - Email settings
        echo - Security keys
        echo.
        set /p continue="Press Enter to continue or Ctrl+C to exit and configure .env first..."
    ) else (
        echo ERROR: .env.docker template not found
        pause
        exit /b 1
    )
) else (
    echo Environment file already exists ✓
)
echo.

REM Create necessary directories
echo [4/8] Creating necessary directories...
if not exist "backend\logs" mkdir "backend\logs"
if not exist "backend\data" mkdir "backend\data"
if not exist "nginx" mkdir "nginx"
echo Directories created ✓
echo.

REM Stop any existing containers
echo [5/8] Stopping existing containers...
docker compose down >nul 2>&1
echo Existing containers stopped ✓
echo.

REM Build and start services
echo [6/8] Building and starting services...
echo This may take several minutes on first run...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start services
    echo Check the logs with: docker compose logs
    pause
    exit /b 1
)
echo Services started successfully ✓
echo.

REM Wait for services to be healthy
echo [7/8] Waiting for services to be ready...
echo Checking database connection...
:wait_db
timeout /t 5 /nobreak >nul
docker compose exec -T postgres pg_isready -U postgres >nul 2>&1
if %errorlevel% neq 0 (
    echo Waiting for database...
    goto wait_db
)
echo Database is ready ✓

echo Checking backend API...
:wait_backend
timeout /t 5 /nobreak >nul
curl -f http://localhost:5000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Waiting for backend API...
    goto wait_backend
)
echo Backend API is ready ✓

echo Checking frontend...
:wait_frontend
timeout /t 3 /nobreak >nul
curl -f http://localhost:3000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Waiting for frontend...
    goto wait_frontend
)
echo Frontend is ready ✓
echo.

REM Final status check
echo [8/8] Final deployment status...
docker compose ps
echo.

echo ========================================
echo DEPLOYMENT COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Your Trading Bot is now running:
echo.
echo 🌐 Frontend:     http://localhost:3000
echo 🔧 Backend API:  http://localhost:5000
echo 📊 Database:     localhost:5432
echo 🔴 Redis:        localhost:6379
echo.
echo Useful commands:
echo   View logs:      docker compose logs -f
echo   Stop services:  docker compose down
echo   Restart:        docker compose restart
echo   Update:         docker compose pull && docker compose up -d
echo.
echo 📖 Check the README.md for detailed usage instructions
echo 🔒 Remember to secure your API keys and change default passwords!
echo.
pause