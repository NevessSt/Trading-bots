@echo off
REM =============================================================================
REM Trading Bot Health Check Script for Windows
REM =============================================================================

echo ========================================
echo Trading Bot Health Check
echo ========================================
echo.

set "all_healthy=true"

REM Check if Docker is running
echo [1/6] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Docker is not running
    set "all_healthy=false"
) else (
    echo ✓ Docker is running
)
echo.

REM Check container status
echo [2/6] Checking container status...
for /f "tokens=*" %%i in ('docker-compose ps -q') do (
    set "container_id=%%i"
    if not "!container_id!"=="" (
        for /f "tokens=*" %%j in ('docker inspect --format="{{.State.Health.Status}}" !container_id! 2^>nul') do (
            set "health_status=%%j"
        )
        for /f "tokens=*" %%k in ('docker inspect --format="{{.Name}}" !container_id!') do (
            set "container_name=%%k"
            set "container_name=!container_name:~1!"
        )
        
        if "!health_status!"=="healthy" (
            echo ✓ !container_name! is healthy
        ) else if "!health_status!"=="unhealthy" (
            echo ✗ !container_name! is unhealthy
            set "all_healthy=false"
        ) else (
            for /f "tokens=*" %%l in ('docker inspect --format="{{.State.Status}}" !container_id!') do (
                set "status=%%l"
            )
            if "!status!"=="running" (
                echo ✓ !container_name! is running
            ) else (
                echo ✗ !container_name! is !status!
                set "all_healthy=false"
            )
        )
    )
)
echo.

REM Check database connectivity
echo [3/6] Checking database connectivity...
docker-compose exec -T postgres pg_isready -U postgres >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Database is accessible
) else (
    echo ✗ Database is not accessible
    set "all_healthy=false"
)
echo.

REM Check Redis connectivity
echo [4/6] Checking Redis connectivity...
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Redis is accessible
) else (
    echo ✗ Redis is not accessible
    set "all_healthy=false"
)
echo.

REM Check backend API
echo [5/6] Checking backend API...
curl -f -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Backend API is responding
    
    REM Get API status details
    for /f "delims=" %%i in ('curl -s http://localhost:5000/health') do (
        echo   Response: %%i
    )
else (
    echo ✗ Backend API is not responding
    set "all_healthy=false"
)
echo.

REM Check frontend
echo [6/6] Checking frontend...
curl -f -s http://localhost:3000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Frontend is responding
else (
    echo ✗ Frontend is not responding
    set "all_healthy=false"
)
echo.

REM Resource usage check
echo Resource Usage:
echo ========================================
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo.

REM Port check
echo Port Status:
echo ========================================
netstat -an | findstr ":3000 " >nul && echo ✓ Port 3000 (Frontend) is open || echo ✗ Port 3000 (Frontend) is not open
netstat -an | findstr ":5000 " >nul && echo ✓ Port 5000 (Backend) is open || echo ✗ Port 5000 (Backend) is not open
netstat -an | findstr ":5432 " >nul && echo ✓ Port 5432 (Database) is open || echo ✗ Port 5432 (Database) is not open
netstat -an | findstr ":6379 " >nul && echo ✓ Port 6379 (Redis) is open || echo ✗ Port 6379 (Redis) is not open
echo.

REM Disk space check
echo Disk Usage:
echo ========================================
for /f "tokens=3" %%i in ('dir /-c ^| find "bytes free"') do (
    set "free_space=%%i"
)
echo Free disk space: %free_space% bytes

REM Docker volume usage
echo.
echo Docker Volume Usage:
echo ========================================
docker system df
echo.

REM Final health status
echo ========================================
if "%all_healthy%"=="true" (
    echo ✓ ALL SYSTEMS HEALTHY
    echo.
    echo Your Trading Bot is fully operational:
    echo   🌐 Frontend:    http://localhost:3000
    echo   🔧 Backend API: http://localhost:5000
    echo   📊 Database:    localhost:5432
    echo   🔴 Redis:       localhost:6379
    echo.
    echo Next steps:
    echo   - Configure your trading API keys in the dashboard
    echo   - Set up your trading strategies
    echo   - Review risk management settings
    echo   - Enable notifications if desired
) else (
    echo ✗ SOME ISSUES DETECTED
    echo.
    echo Troubleshooting steps:
    echo   1. Check logs: docker-compose logs
    echo   2. Restart services: docker-compose restart
    echo   3. Check configuration: .env file
    echo   4. Verify Docker resources: docker stats
    echo   5. Check network connectivity
    echo.
    echo For detailed troubleshooting, see DOCKER_DEPLOYMENT.md
)
echo ========================================
echo.
pause