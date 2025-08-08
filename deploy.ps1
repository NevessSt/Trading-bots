# Trading Bot Platform Deployment Script for Windows
# This script sets up and deploys the complete trading bot platform on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'logs', 'status', 'clean', 'update', '')]
    [string]$Action = ''
)

# Set error action preference
$ErrorActionPreference = 'Stop'

Write-Host "🚀 Trading Bot Platform Deployment Script (Windows)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Docker is installed
function Test-Docker {
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            throw "Docker not found"
        }
        
        $composeVersion = docker-compose --version 2>$null
        if (-not $composeVersion) {
            throw "Docker Compose not found"
        }
        
        Write-Success "Docker and Docker Compose are installed"
        Write-Host "Docker: $dockerVersion" -ForegroundColor Gray
        Write-Host "Docker Compose: $composeVersion" -ForegroundColor Gray
    }
    catch {
        Write-Error "Docker or Docker Compose is not installed. Please install Docker Desktop first."
        Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
}

# Generate random key
function New-RandomKey {
    param([int]$Length = 32)
    $bytes = New-Object byte[] $Length
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    return [System.Convert]::ToHexString($bytes).ToLower()
}

# Create environment file if it doesn't exist
function Initialize-Environment {
    Write-Status "Setting up environment variables..."
    
    # Create backend .env file
    $backendEnvPath = "backend\.env"
    if (-not (Test-Path $backendEnvPath)) {
        Write-Status "Creating backend .env file..."
        
        $jwtSecret = New-RandomKey
        $secretKey = New-RandomKey
        $encryptionKey = New-RandomKey
        
        $backendEnvContent = @"
# Database Configuration
DATABASE_URL=postgresql://trading_user:trading_password123@localhost:5432/trading_bot_db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET=$jwtSecret
JWT_EXPIRATION_HOURS=24

# Stripe Configuration (Replace with your actual keys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$secretKey

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
ENCRYPTION_KEY=$encryptionKey

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Trading Configuration
DEFAULT_RISK_PERCENTAGE=2
MAX_CONCURRENT_TRADES=10
"@
        
        Set-Content -Path $backendEnvPath -Value $backendEnvContent -Encoding UTF8
        Write-Success "Backend .env file created"
    }
    else {
        Write-Warning "Backend .env file already exists"
    }
    
    # Create frontend .env file
    $frontendEnvPath = "frontend\.env"
    if (-not (Test-Path $frontendEnvPath)) {
        Write-Status "Creating frontend .env file..."
        
        $frontendEnvContent = @"
# API Configuration
REACT_APP_API_URL=http://localhost:5000

# Stripe Configuration (Replace with your actual publishable key)
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# App Configuration
REACT_APP_NAME=Trading Bot Platform
REACT_APP_VERSION=1.0.0
"@
        
        Set-Content -Path $frontendEnvPath -Value $frontendEnvContent -Encoding UTF8
        Write-Success "Frontend .env file created"
    }
    else {
        Write-Warning "Frontend .env file already exists"
    }
}

# Create database initialization script
function Initialize-Database {
    Write-Status "Setting up database initialization..."
    
    $initSqlPath = "backend\init.sql"
    if (-not (Test-Path $initSqlPath)) {
        $initSqlContent = @"
-- Trading Bot Platform Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database if not exists
SELECT 'CREATE DATABASE trading_bot_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_bot_db');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE trading_bot_db TO trading_user;
"@
        
        Set-Content -Path $initSqlPath -Value $initSqlContent -Encoding UTF8
        Write-Success "Database initialization script created"
    }
}

# Build and start services
function Start-Services {
    Write-Status "Building and starting services..."
    
    # Stop any existing containers
    Write-Status "Stopping existing containers..."
    docker-compose down --remove-orphans 2>$null
    
    # Build and start services
    Write-Status "Building Docker images..."
    docker-compose build --no-cache
    
    Write-Status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    Write-Status "Waiting for services to be ready..."
    Start-Sleep -Seconds 30
    
    # Check service health
    Test-ServicesHealth
}

# Check if services are running
function Test-ServicesHealth {
    Write-Status "Checking service health..."
    
    $services = @('postgres', 'redis', 'backend', 'frontend', 'nginx')
    
    foreach ($service in $services) {
        $status = docker-compose ps $service 2>$null
        if ($status -match "Up") {
            Write-Success "$service is running"
        }
        else {
            Write-Error "$service is not running"
            docker-compose logs $service
        }
    }
}

# Initialize database tables
function Initialize-DatabaseTables {
    Write-Status "Initializing database tables..."
    
    # Wait for database to be ready
    Start-Sleep -Seconds 10
    
    # Run database migrations
    $initScript = @"
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"@
    
    docker-compose exec backend python -c "$initScript"
    
    Write-Success "Database initialized"
}

# Create admin user
function New-AdminUser {
    Write-Status "Creating admin user..."
    
    $adminScript = @"
from app import app, db
from models.user import User
from werkzeug.security import generate_password_hash
import uuid

with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(email='admin@tradingbot.com').first()
    if not admin:
        admin_user = User(
            id=str(uuid.uuid4()),
            username='admin',
            email='admin@tradingbot.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
            is_verified=True,
            is_active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created: admin@tradingbot.com / admin123')
    else:
        print('Admin user already exists')
"@
    
    docker-compose exec backend python -c "$adminScript"
    
    Write-Success "Admin user setup complete"
}

# Show deployment information
function Show-DeploymentInfo {
    Write-Host ""
    Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
    Write-Host "======================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Trading Bot Platform is now running:" -ForegroundColor White
    Write-Host ""
    Write-Host "🌐 Frontend (React App):     http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Backend API:              http://localhost:5000" -ForegroundColor Cyan
    Write-Host "🗄️  Database (PostgreSQL):    localhost:5432" -ForegroundColor Cyan
    Write-Host "🔴 Redis Cache:              localhost:6379" -ForegroundColor Cyan
    Write-Host "🔀 Nginx Reverse Proxy:      http://localhost:80" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "👤 Admin Credentials:" -ForegroundColor Yellow
    Write-Host "   Email: admin@tradingbot.com" -ForegroundColor White
    Write-Host "   Password: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Useful Commands:" -ForegroundColor Yellow
    Write-Host "   View logs:           .\deploy.ps1 logs" -ForegroundColor White
    Write-Host "   Stop services:       .\deploy.ps1 stop" -ForegroundColor White
    Write-Host "   Restart services:    .\deploy.ps1 restart" -ForegroundColor White
    Write-Host "   Update services:     .\deploy.ps1 update" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Important Notes:" -ForegroundColor Red
    Write-Host "   1. Change default passwords in production" -ForegroundColor White
    Write-Host "   2. Update Stripe keys in .env files" -ForegroundColor White
    Write-Host "   3. Configure email settings for notifications" -ForegroundColor White
    Write-Host "   4. Set up SSL certificates for HTTPS" -ForegroundColor White
    Write-Host "   5. Configure firewall rules for production" -ForegroundColor White
    Write-Host ""
}

# Main deployment function
function Start-Deployment {
    Write-Status "Starting Trading Bot Platform deployment..."
    
    Test-Docker
    Initialize-Environment
    Initialize-Database
    Start-Services
    Initialize-DatabaseTables
    New-AdminUser
    Show-DeploymentInfo
    
    Write-Success "Deployment completed successfully!"
}

# Handle script arguments
switch ($Action) {
    'start' {
        Write-Status "Starting services..."
        docker-compose up -d
    }
    'stop' {
        Write-Status "Stopping services..."
        docker-compose down
    }
    'restart' {
        Write-Status "Restarting services..."
        docker-compose restart
    }
    'logs' {
        docker-compose logs -f
    }
    'status' {
        docker-compose ps
    }
    'clean' {
        Write-Warning "This will remove all containers and volumes. Are you sure? (y/N)"
        $response = Read-Host
        if ($response -eq 'y' -or $response -eq 'Y') {
            docker-compose down -v --remove-orphans
            docker system prune -f
            Write-Success "Cleanup completed"
        }
    }
    'update' {
        Write-Status "Updating services..."
        docker-compose pull
        docker-compose up -d
    }
    '' {
        Start-Deployment
    }
    default {
        Write-Host "Usage: .\deploy.ps1 [start|stop|restart|logs|status|clean|update]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  start    - Start all services" -ForegroundColor White
        Write-Host "  stop     - Stop all services" -ForegroundColor White
        Write-Host "  restart  - Restart all services" -ForegroundColor White
        Write-Host "  logs     - View service logs" -ForegroundColor White
        Write-Host "  status   - Show service status" -ForegroundColor White
        Write-Host "  clean    - Remove all containers and volumes" -ForegroundColor White
        Write-Host "  update   - Update and restart services" -ForegroundColor White
        Write-Host "  (no arg) - Full deployment" -ForegroundColor White
        exit 1
    }
}