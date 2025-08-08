#!/bin/bash

# Trading Bot Platform Deployment Script
# This script sets up and deploys the complete trading bot platform

set -e  # Exit on any error

echo "🚀 Trading Bot Platform Deployment Script"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Create environment file if it doesn't exist
setup_environment() {
    print_status "Setting up environment variables..."
    
    if [ ! -f "backend/.env" ]; then
        print_status "Creating backend .env file..."
        cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://trading_user:trading_password123@localhost:5432/trading_bot_db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production-$(openssl rand -hex 32)
JWT_EXPIRATION_HOURS=24

# Stripe Configuration (Replace with your actual keys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security
ENCRYPTION_KEY=$(openssl rand -hex 32)

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Trading Configuration
DEFAULT_RISK_PERCENTAGE=2
MAX_CONCURRENT_TRADES=10
EOF
        print_success "Backend .env file created"
    else
        print_warning "Backend .env file already exists"
    fi
    
    if [ ! -f "frontend/.env" ]; then
        print_status "Creating frontend .env file..."
        cat > frontend/.env << EOF
# API Configuration
REACT_APP_API_URL=http://localhost:5000

# Stripe Configuration (Replace with your actual publishable key)
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# App Configuration
REACT_APP_NAME=Trading Bot Platform
REACT_APP_VERSION=1.0.0
EOF
        print_success "Frontend .env file created"
    else
        print_warning "Frontend .env file already exists"
    fi
}

# Create database initialization script
setup_database() {
    print_status "Setting up database initialization..."
    
    if [ ! -f "backend/init.sql" ]; then
        cat > backend/init.sql << EOF
-- Trading Bot Platform Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database if not exists
SELECT 'CREATE DATABASE trading_bot_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_bot_db');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE trading_bot_db TO trading_user;
EOF
        print_success "Database initialization script created"
    fi
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose down --remove-orphans
    
    # Build and start services
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_services_health
}

# Check if services are running
check_services_health() {
    print_status "Checking service health..."
    
    services=("postgres" "redis" "backend" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "${service}.*Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
            docker-compose logs $service
        fi
    done
}

# Initialize database tables
init_database() {
    print_status "Initializing database tables..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run database migrations
    docker-compose exec backend python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"
    
    print_success "Database initialized"
}

# Create admin user
create_admin_user() {
    print_status "Creating admin user..."
    
    docker-compose exec backend python -c "
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
"
    
    print_success "Admin user setup complete"
}

# Show deployment information
show_deployment_info() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "Your Trading Bot Platform is now running:"
    echo ""
    echo "🌐 Frontend (React App):     http://localhost:3000"
    echo "🔧 Backend API:              http://localhost:5000"
    echo "🗄️  Database (PostgreSQL):    localhost:5432"
    echo "🔴 Redis Cache:              localhost:6379"
    echo "🔀 Nginx Reverse Proxy:      http://localhost:80"
    echo ""
    echo "👤 Admin Credentials:"
    echo "   Email: admin@tradingbot.com"
    echo "   Password: admin123"
    echo ""
    echo "📋 Useful Commands:"
    echo "   View logs:           docker-compose logs -f"
    echo "   Stop services:       docker-compose down"
    echo "   Restart services:    docker-compose restart"
    echo "   Update services:     docker-compose pull && docker-compose up -d"
    echo ""
    echo "⚠️  Important Notes:"
    echo "   1. Change default passwords in production"
    echo "   2. Update Stripe keys in .env files"
    echo "   3. Configure email settings for notifications"
    echo "   4. Set up SSL certificates for HTTPS"
    echo "   5. Configure firewall rules for production"
    echo ""
}

# Main deployment function
main() {
    print_status "Starting Trading Bot Platform deployment..."
    
    check_docker
    setup_environment
    setup_database
    deploy_services
    init_database
    create_admin_user
    show_deployment_info
    
    print_success "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "start")
        print_status "Starting services..."
        docker-compose up -d
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose down
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        print_warning "This will remove all containers and volumes. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup completed"
        fi
        ;;
    "update")
        print_status "Updating services..."
        docker-compose pull
        docker-compose up -d
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|logs|status|clean|update]"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - View service logs"
        echo "  status   - Show service status"
        echo "  clean    - Remove all containers and volumes"
        echo "  update   - Update and restart services"
        echo "  (no arg) - Full deployment"
        exit 1
        ;;
esac