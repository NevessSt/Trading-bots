@echo off
echo ========================================
echo    Trading Bot Pro - Start All Services
echo ========================================
echo.

:: Check if services are already running
netstat -an | find ":3000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 3000 is already in use (Frontend may be running)
)

netstat -an | find ":5000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 5000 is already in use (Backend may be running)
)

netstat -an | find ":8080" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8080 is already in use (License server may be running)
)

echo.
echo Starting all services...
echo.

:: Start License Server
echo [1/3] Starting License Server...
cd license-server
start /b "License Server" python app.py
cd ..
timeout /t 2 /nobreak >nul
echo ✓ License Server started on port 8080

:: Start Backend
echo [2/3] Starting Backend API...
cd backend
start /b "Backend API" python app.py
cd ..
timeout /t 3 /nobreak >nul
echo ✓ Backend API started on port 5000

:: Start Frontend
echo [3/3] Starting Web Dashboard...
cd web-dashboard
start /b "Web Dashboard" npm run dev
cd ..
timeout /t 5 /nobreak >nul
echo ✓ Web Dashboard started on port 3000

echo.
echo ========================================
echo 🚀 All services are now running!
echo ========================================
echo.
echo 📊 Web Dashboard: http://localhost:3000
echo 🔧 Backend API: http://localhost:5000/health
echo 🔑 License Server: http://localhost:8080/health
echo.
echo 📱 Mobile App Connection:
echo    Server URL: http://your-ip:5000
echo    (Replace 'your-ip' with your actual IP address)
echo.
echo 🛑 To stop all services, run: STOP_ALL.bat
echo 🔄 To restart all services, run: RESTART_ALL.bat
echo.

:: Open browser automatically
start http://localhost:3000

echo Services are running in the background.
echo You can close this window safely.
echo.
pause