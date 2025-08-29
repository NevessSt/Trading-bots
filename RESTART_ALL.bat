@echo off
echo ========================================
echo   Trading Bot Pro - Restart All Services
echo ========================================
echo.

echo Restarting all Trading Bot Pro services...
echo This will stop all running services and start them again.
echo.

:: First, stop all services
echo Step 1: Stopping existing services...
call STOP_ALL.bat

:: Wait a moment for complete shutdown
echo.
echo Waiting for complete shutdown...
timeout /t 3 /nobreak >nul

:: Then start all services
echo.
echo Step 2: Starting all services...
call START_ALL.bat

echo.
echo ========================================
echo 🔄 Restart completed successfully!
echo ========================================
echo.
echo All services should now be running with fresh instances.
echo Check the browser window that opened automatically.
echo.
pause