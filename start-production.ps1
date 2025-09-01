# Production Startup Script for Trading Bot Platform
# This script starts the application in production mode with proper configuration

param(
    [switch]$Build,
    [switch]$Logs,
    [switch]$Monitor
)

# Configuration
$ErrorActionPreference = "Stop"
$AppName = "Trading Bot Platform"
$LogFile = "./logs/startup.log"

# Ensure logs directory exists
if (!(Test-Path "./logs")) {
    New-Item -ItemType Directory -Path "./logs" -Force | Out-Null
}

# Logging function
function Write-StartupLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        default { Write-Host $logMessage -ForegroundColor Cyan }
    }
    
    Add-Content -Path $LogFile -Value $logMessage
}

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host "    🚀 TRADING BOT PLATFORM - PRODUCTION STARTUP 🚀" -ForegroundColor Magenta
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host ""
}

# Check system requirements
function Test-SystemRequirements {
    Write-StartupLog "Checking system requirements..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-StartupLog "Docker: $dockerVersion" "SUCCESS"
    } catch {
        Write-StartupLog "Docker is not installed or not running" "ERROR"
        throw "Docker is required for production deployment"
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-StartupLog "Docker Compose: $composeVersion" "SUCCESS"
    } catch {
        Write-StartupLog "Docker Compose is not available" "ERROR"
        throw "Docker Compose is required"
    }
    
    # Check available memory
    $memory = Get-WmiObject -Class Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
    $memoryGB = [math]::Round($memory / 1GB, 2)
    
    if ($memoryGB -lt 4) {
        Write-StartupLog "Available RAM: $memoryGB GB (Warning: Recommended minimum is 4GB)" "WARNING"
    } else {
        Write-StartupLog "Available RAM: $memoryGB GB" "SUCCESS"
    }
    
    # Check disk space
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object -ExpandProperty FreeSpace
    $diskGB = [math]::Round($disk / 1GB, 2)
    
    if ($diskGB -lt 10) {
        Write-StartupLog "Free disk space: $diskGB GB (Warning: Recommended minimum is 10GB)" "WARNING"
    } else {
        Write-StartupLog "Free disk space: $diskGB GB" "SUCCESS"
    }
}

# Validate configuration
function Test-Configuration {
    Write-StartupLog "Validating configuration..."
    
    # Check .env file
    if (!(Test-Path ".env")) {
        Write-StartupLog ".env file not found" "ERROR"
        if (Test-Path ".env.production") {
            Write-StartupLog "Copying .env.production to .env" "WARNING"
            Copy-Item ".env.production" ".env"
            Write-StartupLog "Please review and update .env file with your actual values" "WARNING"
        } else {
            throw ".env file is required for production deployment"
        }
    }
    
    # Check docker-compose.yml
    if (!(Test-Path "docker-compose.yml")) {
        Write-StartupLog "docker-compose.yml not found" "ERROR"
        throw "docker-compose.yml is required"
    }
    
    Write-StartupLog "Configuration validation completed" "SUCCESS"
}

# Build images if requested
function Build-Images {
    if ($Build) {
        Write-StartupLog "Building Docker images..."
        try {
            docker-compose build --no-cache
            Write-StartupLog "Docker images built successfully" "SUCCESS"
        } catch {
            Write-StartupLog "Failed to build Docker images: $($_.Exception.Message)" "ERROR"
            throw "Image build failed"
        }
    }
}

# Start services
function Start-Services {
    Write-StartupLog "Starting production services..."
    
    try {
        # Start services in detached mode
        docker-compose up -d
        
        Write-StartupLog "Services started, waiting for initialization..." "SUCCESS"
        Start-Sleep -Seconds 15
        
        # Check service status
        $services = docker-compose ps --services
        foreach ($service in $services) {
            $status = docker-compose ps $service --format "{{.State}}"
            if ($status -eq "running") {
                Write-StartupLog "Service '$service' is running" "SUCCESS"
            } else {
                Write-StartupLog "Service '$service' status: $status" "WARNING"
            }
        }
        
    } catch {
        Write-StartupLog "Failed to start services: $($_.Exception.Message)" "ERROR"
        throw "Service startup failed"
    }
}

# Health check
function Test-ApplicationHealth {
    Write-StartupLog "Performing health checks..."
    
    # Wait a bit more for services to fully initialize
    Start-Sleep -Seconds 10
    
    # Check backend API
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 30
        if ($backendResponse.StatusCode -eq 200) {
            Write-StartupLog "Backend API health check: PASSED" "SUCCESS"
        }
    } catch {
        Write-StartupLog "Backend API health check: FAILED" "WARNING"
    }
    
    # Check frontend
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 30
        if ($frontendResponse.StatusCode -eq 200) {
            Write-StartupLog "Frontend health check: PASSED" "SUCCESS"
        }
    } catch {
        Write-StartupLog "Frontend health check: FAILED" "WARNING"
    }
    
    # Check database connectivity
    try {
        $dbCheck = docker exec trading_bot_postgres pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-StartupLog "Database connectivity: PASSED" "SUCCESS"
        }
    } catch {
        Write-StartupLog "Database connectivity: FAILED" "WARNING"
    }
}

# Show access information
function Show-AccessInfo {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "    🎉 TRADING BOT PLATFORM IS NOW RUNNING! 🎉" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Frontend Dashboard: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Backend API: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "📈 API Documentation: http://localhost:5000/docs" -ForegroundColor Cyan
    Write-Host "💾 Database: localhost:5432" -ForegroundColor Cyan
    Write-Host "🔄 Redis Cache: localhost:6379" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Management Commands:" -ForegroundColor Yellow
    Write-Host "   • View logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "   • Stop services: docker-compose down" -ForegroundColor White
    Write-Host "   • Restart: docker-compose restart" -ForegroundColor White
    Write-Host "   • Status: docker-compose ps" -ForegroundColor White
    Write-Host ""
}

# Monitor services
function Start-Monitoring {
    if ($Monitor) {
        Write-StartupLog "Starting monitoring mode..."
        Write-Host "Press Ctrl+C to exit monitoring" -ForegroundColor Yellow
        Write-Host ""
        
        try {
            docker-compose logs -f
        } catch {
            Write-StartupLog "Monitoring interrupted" "INFO"
        }
    }
}

# Main execution
try {
    Show-Banner
    Test-SystemRequirements
    Test-Configuration
    Build-Images
    Start-Services
    Test-ApplicationHealth
    Show-AccessInfo
    
    if ($Logs) {
        Write-Host "Showing recent logs..." -ForegroundColor Yellow
        docker-compose logs --tail=50
    }
    
    Start-Monitoring
    
} catch {
    Write-StartupLog "Startup failed: $($_.Exception.Message)" "ERROR"
    Write-Host ""
    Write-Host "❌ Startup failed. Check the logs for details." -ForegroundColor Red
    Write-Host "📋 Log file: $LogFile" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-StartupLog "Production startup completed successfully" "SUCCESS"