@echo off
echo ========================================
echo Trading Bot Pro - Windows Installer Builder
echo ========================================
echo.

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not available
    echo Please ensure Node.js is properly installed
    pause
    exit /b 1
)

echo ✅ Node.js and npm are available
echo.

:: Install dependencies if needed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
    echo.
)

:: Install electron-builder if not present
npm list electron-builder >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing electron-builder...
    npm install --save-dev electron-builder
    if %errorlevel% neq 0 (
        echo ❌ Failed to install electron-builder
        pause
        exit /b 1
    )
    echo ✅ electron-builder installed successfully
    echo.
)

:: Build the application first
echo 🔨 Building the application...
npm run build
if %errorlevel% neq 0 (
    echo ❌ Failed to build the application
    pause
    exit /b 1
)
echo ✅ Application built successfully
echo.

:: Build the Windows installer
echo 📦 Building Windows installer...
node build-installer.js win32
if %errorlevel% neq 0 (
    echo ❌ Failed to build installer
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Windows installer built successfully!
echo ========================================
echo.
echo 📁 Installer files are located in: dist\installers
echo.
echo Available installers:
echo   • NSIS Installer (.exe) - Full installer with uninstaller
echo   • Portable (.exe) - Standalone executable
echo.
echo 🚀 You can now distribute these files to users!
echo.

:: Open the output directory
set /p open_folder="Open installer folder? (y/n): "
if /i "%open_folder%"=="y" (
    start "" "dist\installers"
)

echo.
echo Press any key to exit...
pause >nul