@echo off
REM One-Click Demo License Activation for Trading Bot
REM This script sets up everything needed for non-tech buyers

echo.
echo ================================================================
echo                 TRADING BOT - DEMO LICENSE ACTIVATION
echo ================================================================
echo.
echo This will set up your trading bot with a premium demo license!
echo Please wait while we configure everything for you...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found! Starting demo license setup...
echo.

REM Run the demo license setup script
python demo_license_setup.py

if errorlevel 1 (
    echo.
    echo ERROR: Demo license setup failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo                    SETUP COMPLETE!
echo ================================================================
echo Your trading bot is now ready with premium features!
echo.
echo Next steps:
echo 1. Open a new command prompt
echo 2. Run: cd web-dashboard ^&^& npm run dev
echo 3. Open your browser to http://localhost:5173
echo.
echo Your premium license is valid for 365 days!
echo ================================================================
echo.
pause