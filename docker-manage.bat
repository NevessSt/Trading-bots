@echo off
REM =============================================================================
REM Trading Bot Docker Management Script for Windows
REM =============================================================================

setlocal enabledelayedexpansion

if "%1"=="" goto show_help

set command=%1
shift

if "%command%"=="start" goto start_services
if "%command%"=="stop" goto stop_services
if "%command%"=="restart" goto restart_services
if "%command%"=="logs" goto show_logs
if "%command%"=="status" goto show_status
if "%command%"=="update" goto update_services
if "%command%"=="backup" goto backup_data
if "%command%"=="restore" goto restore_data
if "%command%"=="clean" goto clean_system
if "%command%"=="shell" goto shell_access
if "%command%"=="help" goto show_help

echo Unknown command: %command%
goto show_help

:show_help
echo ========================================
echo Trading Bot Docker Management
echo ========================================
echo.
echo Usage: docker-manage.bat [command] [options]
echo.
echo Commands:
echo   start     - Start all services
echo   stop      - Stop all services
echo   restart   - Restart all services
echo   logs      - Show logs (optional: service name)
echo   status    - Show service status
echo   update    - Update and restart services
echo   backup    - Backup database and data
echo   restore   - Restore from backup
echo   clean     - Clean unused Docker resources
echo   shell     - Access service shell (requires service name)
echo   help      - Show this help
echo.
echo Examples:
echo   docker-manage.bat start
echo   docker-manage.bat logs backend
echo   docker-manage.bat shell postgres
echo   docker-manage.bat backup
echo.
goto end

:start_services
echo Starting Trading Bot services...
docker compose up -d
if %errorlevel% equ 0 (
    echo ✓ Services started successfully
    echo.
    echo Your Trading Bot is running:
    echo   Frontend: http://localhost:3000
    echo   Backend:  http://localhost:5000
) else (
    echo ✗ Failed to start services
)
goto end

:stop_services
echo Stopping Trading Bot services...
docker compose down
if %errorlevel% equ 0 (
    echo ✓ Services stopped successfully
) else (
    echo ✗ Failed to stop services
)
goto end

:restart_services
echo Restarting Trading Bot services...
docker compose restart
if %errorlevel% equ 0 (
    echo ✓ Services restarted successfully
) else (
    echo ✗ Failed to restart services
)
goto end

:show_logs
if "%1"=="" (
    echo Showing logs for all services...
    docker compose logs -f
) else (
    echo Showing logs for %1...
    docker compose logs -f %1
)
goto end

:show_status
echo Trading Bot Service Status:
echo ========================================
docker compose ps
echo.
echo Resource Usage:
echo ========================================
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
goto end

:update_services
echo Updating Trading Bot services...
echo Pulling latest images...
docker compose pull
echo Rebuilding and restarting services...
docker compose up --build -d
if %errorlevel% equ 0 (
    echo ✓ Services updated successfully
) else (
    echo ✗ Failed to update services
)
goto end

:backup_data
set backup_dir=backups\%date:~-4,4%-%date:~-10,2%-%date:~-7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set backup_dir=%backup_dir: =0%

echo Creating backup in %backup_dir%...
if not exist "backups" mkdir "backups"
if not exist "%backup_dir%" mkdir "%backup_dir%"

REM Backup database
echo Backing up database...
docker compose exec -T postgres pg_dump -U postgres trading_bot > "%backup_dir%\database.sql"
if %errorlevel% equ 0 (
    echo ✓ Database backup completed
) else (
    echo ✗ Database backup failed
)

REM Backup application data
echo Backing up application data...
if exist "backend\data" (
    xcopy "backend\data" "%backup_dir%\data\" /E /I /Q
    echo ✓ Application data backup completed
)

REM Backup logs
echo Backing up logs...
if exist "backend\logs" (
    xcopy "backend\logs" "%backup_dir%\logs\" /E /I /Q
    echo ✓ Logs backup completed
)

REM Backup configuration
echo Backing up configuration...
if exist ".env" copy ".env" "%backup_dir%\.env"
if exist "docker-compose.yml" copy "docker-compose.yml" "%backup_dir%\docker-compose.yml"

echo ✓ Backup completed: %backup_dir%
goto end

:restore_data
if "%1"=="" (
    echo Please specify backup directory
    echo Usage: docker-manage.bat restore [backup_directory]
    goto end
)

set restore_dir=%1
if not exist "%restore_dir%" (
    echo Backup directory not found: %restore_dir%
    goto end
)

echo Restoring from backup: %restore_dir%
echo WARNING: This will overwrite current data!
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto end

REM Stop services
echo Stopping services...
docker compose down

REM Restore database
if exist "%restore_dir%\database.sql" (
    echo Restoring database...
    docker compose up -d postgres
    timeout /t 10 /nobreak >nul
    docker compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS trading_bot;"
    docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE trading_bot;"
    docker compose exec -T postgres psql -U postgres trading_bot < "%restore_dir%\database.sql"
    echo ✓ Database restored
)

REM Restore application data
if exist "%restore_dir%\data" (
    echo Restoring application data...
    if exist "backend\data" rmdir /s /q "backend\data"
    xcopy "%restore_dir%\data" "backend\data\" /E /I /Q
    echo ✓ Application data restored
)

REM Restore configuration
if exist "%restore_dir%\.env" (
    echo Restoring configuration...
    copy "%restore_dir%\.env" ".env"
    echo ✓ Configuration restored
)

REM Start services
echo Starting services...
docker compose up -d
echo ✓ Restore completed
goto end

:clean_system
echo Cleaning Docker system...
echo This will remove unused containers, networks, images, and volumes
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto end

docker system prune -a --volumes -f
echo ✓ Docker system cleaned
goto end

:shell_access
if "%1"=="" (
    echo Please specify service name
    echo Available services: backend, frontend, postgres, redis, nginx
    goto end
)

set service=%1
echo Accessing %service% shell...

if "%service%"=="backend" (
    docker compose exec backend /bin/bash
) else if "%service%"=="frontend" (
    docker compose exec frontend /bin/sh
) else if "%service%"=="postgres" (
    docker compose exec postgres psql -U postgres trading_bot
) else if "%service%"=="redis" (
    docker compose exec redis redis-cli
) else if "%service%"=="nginx" (
    docker compose exec nginx /bin/sh
) else (
    echo Unknown service: %service%
    echo Available services: backend, frontend, postgres, redis, nginx
)
goto end

:end
echo.
pause