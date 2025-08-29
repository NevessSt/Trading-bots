@echo off
echo ========================================
echo    Trading Bot Pro - Quick Start
echo ========================================
echo.
echo Starting Trading Bot Pro in Demo Mode...
echo This will take about 2-3 minutes.
echo.

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please download and install Node.js from: https://nodejs.org
    echo Then run this script again.
    pause
    exit /b 1
)

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please download and install Python from: https://python.org
    echo Then run this script again.
    pause
    exit /b 1
)

echo ✓ Node.js found
echo ✓ Python found
echo.

:: Install backend dependencies
echo [1/5] Installing backend dependencies...
cd backend
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Some Python packages may have failed to install
    echo This might not affect demo mode functionality
)
cd ..

:: Install frontend dependencies
echo [2/5] Installing frontend dependencies...
cd web-dashboard
npm install >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
cd ..

:: Build frontend for production
echo [3/5] Building frontend...
cd web-dashboard
npm run build >nul 2>&1
cd ..

:: Start license server
echo [4/5] Starting license server...
cd license-server
start /b python app.py
cd ..

:: Wait for license server to start
timeout /t 3 /nobreak >nul

:: Start backend with demo mode
echo [5/5] Starting backend in demo mode...
cd backend
set DEMO_MODE=true
set LICENSE_SERVER_URL=http://localhost:8080
start /b python app.py
cd ..

:: Wait for backend to start
timeout /t 5 /nobreak >nul

:: Start frontend development server
echo Starting web dashboard...
cd web-dashboard
start /b npm run dev
cd ..

:: Wait for frontend to start
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo 🚀 Trading Bot Pro is ready!
echo ========================================
echo.
echo Demo Login Credentials:
echo   Username: demo
echo   Password: demo123
echo.
echo Web Dashboard: http://localhost:3000
echo Backend API: http://localhost:5000
echo License Server: http://localhost:8080
echo.
echo ✨ Features enabled in Demo Mode:
echo   • Fake trading data
echo   • Paper trading
echo   • All strategies available
echo   • No API keys required
echo   • Risk-free testing
echo.
echo Press Ctrl+C to stop all services
echo.

:: Open browser automatically
start http://localhost:3000

:: Keep script running
echo Waiting for services... (Press Ctrl+C to stop)
pause >nul