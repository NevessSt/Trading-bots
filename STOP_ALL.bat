@echo off
echo ========================================
echo    Trading Bot Pro - Stop All Services
echo ========================================
echo.

echo Stopping all Trading Bot Pro services...
echo.

:: Stop processes by port (more reliable than process name)
echo [1/4] Stopping Web Dashboard (port 3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ Web Dashboard stopped
    )
)

echo [2/4] Stopping Backend API (port 5000)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ Backend API stopped
    )
)

echo [3/4] Stopping License Server (port 8080)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ License Server stopped
    )
)

:: Stop any remaining Node.js and Python processes related to our app
echo [4/4] Cleaning up remaining processes...

:: Kill Node.js processes that might be running our frontend
tasklist | find "node.exe" >nul
if %errorlevel% equ 0 (
    wmic process where "name='node.exe' and commandline like '%%npm run dev%%'" delete >nul 2>&1
    wmic process where "name='node.exe' and commandline like '%%web-dashboard%%'" delete >nul 2>&1
)

:: Kill Python processes that might be running our backend
tasklist | find "python.exe" >nul
if %errorlevel% equ 0 (
    wmic process where "name='python.exe' and commandline like '%%app.py%%'" delete >nul 2>&1
)

:: Wait a moment for processes to fully terminate
timeout /t 2 /nobreak >nul

:: Verify ports are free
echo.
echo Verifying services are stopped...

netstat -an | find ":3000" >nul
if %errorlevel% neq 0 (
    echo ✓ Port 3000 is free
) else (
    echo ⚠ Port 3000 is still in use
)

netstat -an | find ":5000" >nul
if %errorlevel% neq 0 (
    echo ✓ Port 5000 is free
) else (
    echo ⚠ Port 5000 is still in use
)

netstat -an | find ":8080" >nul
if %errorlevel% neq 0 (
    echo ✓ Port 8080 is free
) else (
    echo ⚠ Port 8080 is still in use
)

echo.
echo ========================================
echo 🛑 All services have been stopped!
echo ========================================
echo.
echo 🚀 To start services again, run: START_ALL.bat
echo 🔄 To restart services, run: RESTART_ALL.bat
echo ⚡ For quick demo setup, run: QUICK_START.bat
echo.
pause