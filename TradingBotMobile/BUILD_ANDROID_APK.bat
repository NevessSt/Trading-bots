@echo off
REM Trading Bot Pro - Android APK Builder for Windows
REM This script builds the Android APK with all necessary setup

setlocal EnableDelayedExpansion

echo ========================================
echo Trading Bot Pro - Android APK Builder
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo ✓ Node.js is installed

REM Check if Java is installed
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Java is not installed or not in PATH
    echo Please install Java JDK 11 or higher
    pause
    exit /b 1
)

echo ✓ Java is installed

REM Check Android SDK
if not defined ANDROID_HOME (
    if not defined ANDROID_SDK_ROOT (
        echo WARNING: ANDROID_HOME or ANDROID_SDK_ROOT not set
        echo Please set up Android SDK environment variables
        echo Continuing anyway...
    )
) else (
    echo ✓ Android SDK environment found
)

echo.
echo Installing dependencies...
echo ========================================

REM Install npm dependencies
if not exist node_modules (
    echo Installing npm packages...
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install npm dependencies
        pause
        exit /b 1
    )
) else (
    echo ✓ Dependencies already installed
)

echo.
echo Preparing Android build...
echo ========================================

REM Create dist directory
if not exist dist mkdir dist

REM Check if keystore exists, create if not
if not exist android\app\release-key.keystore (
    echo Generating release keystore...
    echo NOTE: Using default passwords for demo purposes
    echo In production, use strong passwords!
    
    keytool -genkeypair -v -storetype PKCS12 -keystore android\app\release-key.keystore -alias release-key -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Trading Bot Pro, OU=Mobile, O=Trading Bot Pro, L=City, S=State, C=US"
    
    if %errorlevel% neq 0 (
        echo ERROR: Failed to generate keystore
        echo Make sure Java JDK is properly installed
        pause
        exit /b 1
    )
    
    echo ✓ Keystore generated successfully
) else (
    echo ✓ Release keystore found
)

REM Update gradle.properties with keystore info
echo Configuring gradle properties...
if not exist android\gradle.properties (
    echo Creating gradle.properties...
    (
        echo # Release keystore configuration
        echo RELEASE_STORE_FILE=release-key.keystore
        echo RELEASE_KEY_ALIAS=release-key
        echo RELEASE_STORE_PASSWORD=android
        echo RELEASE_KEY_PASSWORD=android
    ) > android\gradle.properties
) else (
    REM Check if keystore config exists in gradle.properties
    findstr /C:"RELEASE_STORE_FILE" android\gradle.properties >nul
    if %errorlevel% neq 0 (
        echo Adding keystore configuration to gradle.properties...
        (
            echo.
            echo # Release keystore configuration
            echo RELEASE_STORE_FILE=release-key.keystore
            echo RELEASE_KEY_ALIAS=release-key
            echo RELEASE_STORE_PASSWORD=android
            echo RELEASE_KEY_PASSWORD=android
        ) >> android\gradle.properties
    )
)

echo ✓ Gradle properties configured

echo.
echo Building Android APK...
echo ========================================

REM Clean previous builds
echo Cleaning previous builds...
cd android
call gradlew clean
if %errorlevel% neq 0 (
    echo ERROR: Failed to clean Android project
    cd ..
    pause
    exit /b 1
)

echo Building release APK...
call gradlew assembleRelease
if %errorlevel% neq 0 (
    echo ERROR: Failed to build APK
    cd ..
    pause
    exit /b 1
)

cd ..

REM Copy APK to dist folder
if exist android\app\build\outputs\apk\release\app-release.apk (
    copy "android\app\build\outputs\apk\release\app-release.apk" "dist\TradingBotMobile-1.0.0.apk"
    echo.
    echo ========================================
    echo ✓ SUCCESS: APK built successfully!
    echo ========================================
    echo.
    echo APK Location: %cd%\dist\TradingBotMobile-1.0.0.apk
    
    REM Get file size
    for %%A in ("dist\TradingBotMobile-1.0.0.apk") do (
        set /a "size=%%~zA/1024/1024"
        echo APK Size: !size! MB
    )
    
    echo.
    echo Next steps:
    echo 1. Test the APK on an Android device
    echo 2. Upload to Google Play Console for distribution
    echo 3. Enable Google Play App Signing for production
    echo.
    echo Opening output directory...
    explorer dist
    
) else (
    echo ERROR: APK file not found after build
    echo Check the build logs above for errors
    pause
    exit /b 1
)

echo.
echo Build completed! Press any key to exit...
pause >nul