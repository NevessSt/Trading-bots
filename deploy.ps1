# Trading Bot Production Deployment Script for Windows
# PowerShell script for complete deployment process

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("deploy", "backup", "logs", "stop", "restart", "status", "health")]
    [string]$Action,
    
    [switch]$SkipBackup
)

# Configuration
$AppName = "trading-bot"
$DockerComposeFile = "docker-compose.yml"
$EnvFile = ".env"
$BackupDir = "./backups"
$LogFile = "./logs/deployment.log"

# Ensure logs directory exists
if (!(Test-Path "./logs")) {
    New-Item -ItemType Directory -Path "./logs" -Force | Out-Null
}

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        default { Write-Host $logMessage -ForegroundColor Blue }
    }
    
    Add-Content -Path $LogFile -Value $logMessage
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking prerequisites..."
    
    # Check if Docker is installed
    try {
        docker --version | Out-Null
        Write-Log "Docker is installed" "SUCCESS"
    } catch {
        Write-Log "Docker is not installed. Please install Docker Desktop first." "ERROR"
        exit 1
    }
    
    # Check if Docker Compose is available
    try {
        docker-compose --version | Out-Null
        Write-Log "Docker Compose is available" "SUCCESS"
    } catch {
        Write-Log "Docker Compose is not available. Please install Docker Compose." "ERROR"
        exit 1
    }
    
    # Check if .env file exists
    if (!(Test-Path $EnvFile)) {
        Write-Log ".env file not found. Creating from template..." "WARNING"
        if (Test-Path ".env.production") {
            Copy-Item ".env.production" $EnvFile
            Write-Log "Please edit .env file with your actual configuration values." "WARNING"
        } else {
            Write-Log "No .env template found. Please create .env file manually." "ERROR"
            exit 1
        }
    }
    
    Write-Log "Prerequisites check completed" "SUCCESS"
}

# Create necessary directories
function Initialize-Directories {
    Write-Log "Setting up directories..."
    
    $directories = @("logs", "data", "config", $BackupDir, "nginx/ssl")
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Log "Directories created" "SUCCESS"
}

# Backup existing data
function Backup-Data {
    if ($SkipBackup) {
        Write-Log "Skipping backup as requested"
        return
    }
    
    Write-Log "Creating backup..."
    
    $backupTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "$BackupDir/backup_$backupTimestamp"
    
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    
    # Backup database
    try {
        $postgresRunning = docker ps --filter "name=trading_bot_postgres" --format "{{.Names}}" | Select-String "trading_bot_postgres"
        if ($postgresRunning) {
            Write-Log "Backing up database..."
            docker exec trading_bot_postgres pg_dump -U postgres trading_bot > "$backupPath/database.sql"
        }
    } catch {
        Write-Log "Database backup failed: $($_.Exception.Message)" "WARNING"
    }
    
    # Backup application data
    if (Test-Path "./data") {
        Copy-Item "./data" "$backupPath/" -Recurse -Force
    }
    
    # Backup logs
    if (Test-Path "./logs") {
        Copy-Item "./logs" "$backupPath/" -Recurse -Force
    }
    
    Write-Log "Backup created at $backupPath" "SUCCESS"
}

# Build and deploy
function Start-Deployment {
    Write-Log "Starting deployment..."
    
    try {
        # Pull latest images
        Write-Log "Pulling latest images..."
        docker-compose pull
        
        # Build custom images
        Write-Log "Building application images..."
        docker-compose build --no-cache
        
        # Stop existing containers
        Write-Log "Stopping existing containers..."
        docker-compose down
        
        # Start services
        Write-Log "Starting services..."
        docker-compose up -d
        
        # Wait for services to be healthy
        Write-Log "Waiting for services to be ready..."
        Start-Sleep -Seconds 30
        
        # Check service health
        Test-ServiceHealth
        
        Write-Log "Deployment completed successfully" "SUCCESS"
    } catch {
        Write-Log "Deployment failed: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

# Check service health
function Test-ServiceHealth {
    Write-Log "Checking service health..."
    
    # Check backend health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "Backend service is healthy" "SUCCESS"
        }
    } catch {
        Write-Log "Backend service is not responding" "ERROR"
    }
    
    # Check frontend health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "Frontend service is healthy" "SUCCESS"
        }
    } catch {
        Write-Log "Frontend service may not be ready yet" "WARNING"
    }
    
    # Check database
    try {
        $dbCheck = docker exec trading_bot_postgres pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Database is healthy" "SUCCESS"
        }
    } catch {
        Write-Log "Database is not responding" "ERROR"
    }
    
    # Check Redis
    try {
        $redisCheck = docker exec trading_bot_redis redis-cli ping 2>$null
        if ($redisCheck -eq "PONG") {
            Write-Log "Redis is healthy" "SUCCESS"
        }
    } catch {
        Write-Log "Redis is not responding" "ERROR"
    }
}

# Show logs
function Show-Logs {
    Write-Log "Showing recent logs..."
    docker-compose logs --tail=50 -f
}

# Stop services
function Stop-Services {
    Write-Log "Stopping all services..."
    docker-compose down
    Write-Log "All services stopped" "SUCCESS"
}

# Restart services
function Restart-Services {
    Write-Log "Restarting services..."
    docker-compose restart
    Write-Log "Services restarted" "SUCCESS"
}

# Show status
function Show-Status {
    Write-Log "Service status:"
    docker-compose ps
    Write-Host ""
    Write-Log "Resource usage:"
    docker stats --no-stream
}

# Main script execution
switch ($Action) {
    "deploy" {
        Test-Prerequisites
        Initialize-Directories
        Backup-Data
        Start-Deployment
    }
    "backup" {
        Backup-Data
    }
    "logs" {
        Show-Logs
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Restart-Services
    }
    "status" {
        Show-Status
    }
    "health" {
        Test-ServiceHealth
    }
}

Write-Log "Script execution completed."