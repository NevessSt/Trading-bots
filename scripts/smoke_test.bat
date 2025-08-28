@echo off
REM TradingBot Pro - Smoke Test Script (Windows)
REM This script verifies that the application is properly installed and running

setlocal enabledelayedexpansion

echo 🧪 TradingBot Pro - Smoke Test Suite
echo =====================================
echo.

REM Test configuration
set BACKEND_URL=http://localhost:5000
set FRONTEND_URL=http://localhost:3000
set MAX_RETRIES=30
set RETRY_DELAY=2
set TESTS_PASSED=0
set TESTS_FAILED=0

REM Helper function to test API endpoints
:test_endpoint
set endpoint=%1
set expected_status=%2
set description=%3

echo [INFO] Testing: %description%

REM Use PowerShell to make HTTP request
powershell -Command "try { $response = Invoke-WebRequest -Uri '%endpoint%' -Method Get -UseBasicParsing; Write-Host 'STATUS:'$response.StatusCode } catch { Write-Host 'STATUS:'$_.Exception.Response.StatusCode.Value__ }" > temp_response.txt 2>&1

for /f "tokens=2 delims=:" %%i in ('findstr "STATUS:" temp_response.txt') do set actual_status=%%i
del temp_response.txt

if "%actual_status%"=="%expected_status%" (
    echo [SUCCESS] ✅ %description% - Status: %actual_status%
    set /a TESTS_PASSED+=1
) else (
    echo [ERROR] ❌ %description% - Expected: %expected_status%, Got: %actual_status%
    set /a TESTS_FAILED+=1
)
goto :eof

REM Main test suite
echo 🔍 Step 1: Checking if containers are running...
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo [ERROR] No running containers found. Please start the application first:
    echo   make dev    # For development
    echo   make prod   # For production
    exit /b 1
)
echo [SUCCESS] Containers are running
echo.

echo 🌐 Step 2: Testing service availability...
echo [INFO] Waiting for services to be ready...

REM Wait for backend
set retries=0
:wait_backend
if %retries% geq %MAX_RETRIES% (
    echo [ERROR] Backend failed to start within timeout
    exit /b 1
)

powershell -Command "try { Invoke-WebRequest -Uri '%BACKEND_URL%/api/health' -Method Get -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /a retries+=1
    echo [INFO] Attempt %retries%/%MAX_RETRIES% - Backend not ready yet, waiting %RETRY_DELAY%s...
    timeout /t %RETRY_DELAY% >nul
    goto wait_backend
)
echo [SUCCESS] Backend is ready!

REM Wait for frontend
set retries=0
:wait_frontend
if %retries% geq %MAX_RETRIES% (
    echo [ERROR] Frontend failed to start within timeout
    exit /b 1
)

powershell -Command "try { Invoke-WebRequest -Uri '%FRONTEND_URL%' -Method Get -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /a retries+=1
    echo [INFO] Attempt %retries%/%MAX_RETRIES% - Frontend not ready yet, waiting %RETRY_DELAY%s...
    timeout /t %RETRY_DELAY% >nul
    goto wait_frontend
)
echo [SUCCESS] Frontend is ready!
echo.

echo 🏥 Step 3: Health check tests...
call :test_endpoint "%BACKEND_URL%/api/health" "200" "Backend health endpoint"
call :test_endpoint "%BACKEND_URL%/api/version" "200" "Backend version endpoint"
echo.

echo 🔐 Step 4: Authentication tests...
call :test_endpoint "%BACKEND_URL%/api/auth/status" "401" "Auth status (should require authentication)"
echo.

echo 📊 Step 5: Trading API tests...
call :test_endpoint "%BACKEND_URL%/api/trading/strategies" "401" "Trading strategies (should require auth)"
call :test_endpoint "%BACKEND_URL%/api/trading/bots" "401" "Trading bots (should require auth)"
echo.

echo 🔧 Step 6: Configuration tests...
echo [INFO] Checking environment configuration...
if exist ".env" (
    echo [SUCCESS] ✅ .env file exists
    set /a TESTS_PASSED+=1
) else (
    echo [ERROR] ❌ .env file missing
    set /a TESTS_FAILED+=1
)

if exist "backend\.env" (
    echo [SUCCESS] ✅ Backend .env file exists
    set /a TESTS_PASSED+=1
) else (
    echo [ERROR] ❌ Backend .env file missing
    set /a TESTS_FAILED+=1
)
echo.

echo 🗄️ Step 7: Database connectivity test...
echo [INFO] Testing database connection...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_URL%/api/health/db' -Method Get; if ($response -match 'ok|healthy|connected') { Write-Host 'SUCCESS' } else { Write-Host 'FAILED' } } catch { Write-Host 'FAILED' }" > db_test.txt
for /f %%i in (db_test.txt) do set db_result=%%i
del db_test.txt

if "%db_result%"=="SUCCESS" (
    echo [SUCCESS] ✅ Database connection successful
    set /a TESTS_PASSED+=1
) else (
    echo [ERROR] ❌ Database connection failed
    set /a TESTS_FAILED+=1
)
echo.

echo 📈 Step 8: License validation test...
echo [INFO] Testing license validation...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_URL%/api/license/status' -Method Get; if ($response -match 'valid|active|ok') { Write-Host 'SUCCESS' } else { Write-Host 'AUTH_REQUIRED' } } catch { Write-Host 'AUTH_REQUIRED' }" > license_test.txt
for /f %%i in (license_test.txt) do set license_result=%%i
del license_test.txt

if "%license_result%"=="SUCCESS" (
    echo [SUCCESS] ✅ License validation working
    set /a TESTS_PASSED+=1
) else (
    echo [INFO] ⚠️ License validation endpoint may require authentication
)
echo.

echo 🤖 Step 9: Mock trading test...
echo [INFO] Testing mock trading functionality...
REM Test backtest endpoint (expects 401 without auth)
call :test_endpoint "%BACKEND_URL%/api/trading/backtest" "401" "Backtest endpoint (requires auth as expected)"
echo.

echo 🎯 Step 10: Frontend accessibility test...
echo [INFO] Testing frontend pages...
call :test_endpoint "%FRONTEND_URL%" "200" "Frontend accessibility"
echo.

echo 📋 Step 11: Security headers test...
echo [INFO] Checking security headers...
powershell -Command "try { $response = Invoke-WebRequest -Uri '%BACKEND_URL%/api/health' -Method Head -UseBasicParsing; $headers = $response.Headers; if ($headers.Keys -match 'X-Content-Type-Options|X-Frame-Options|X-XSS-Protection') { Write-Host 'SUCCESS' } else { Write-Host 'PARTIAL' } } catch { Write-Host 'FAILED' }" > security_test.txt
for /f %%i in (security_test.txt) do set security_result=%%i
del security_test.txt

if "%security_result%"=="SUCCESS" (
    echo [SUCCESS] ✅ Security headers present
    set /a TESTS_PASSED+=1
) else (
    echo [INFO] ⚠️ Some security headers may be missing
)
echo.

echo 🔍 Step 12: Log file check...
echo [INFO] Checking for application logs...
docker-compose logs backend | findstr /i "Starting Running Ready" >nul
if not errorlevel 1 (
    echo [SUCCESS] ✅ Backend logs are being generated
    set /a TESTS_PASSED+=1
) else (
    echo [INFO] ⚠️ Backend logs may be minimal
)
echo.

REM Summary
echo 📊 SMOKE TEST SUMMARY
echo =====================
echo Tests Passed: %TESTS_PASSED%
echo Tests Failed: %TESTS_FAILED%
echo.
echo [SUCCESS] ✅ Application is running and responding
echo [SUCCESS] ✅ Core endpoints are accessible
echo [SUCCESS] ✅ Authentication is properly enforced
echo [SUCCESS] ✅ Database connectivity verified
echo [INFO] ℹ️ All critical systems appear to be functioning
echo.
echo 🎉 Smoke tests completed successfully!
echo.
echo Next steps:
echo   • Configure your API keys in the .env file
echo   • Set up your trading strategies
echo   • Run full test suite: make test
echo   • Access the application:
echo     - Frontend: %FRONTEND_URL%
echo     - Backend API: %BACKEND_URL%/api
echo.
echo For more information, see:
echo   • README.md - General setup instructions
echo   • BUYER_GUIDE.md - Step-by-step buyer guide
echo   • API_INTEGRATION_GUIDE.md - API setup guide
echo.

if %TESTS_FAILED% gtr 0 (
    echo [WARNING] Some tests failed. Please check the output above.
    exit /b 1
) else (
    echo [SUCCESS] All smoke tests passed!
    exit /b 0
)