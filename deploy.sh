#!/bin/bash

# =============================================================================
# Trading Bot Docker Deployment Script for Linux/macOS
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Trading Bot Docker Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Function to print status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Docker is installed and running
echo "[1/8] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi
print_status "Docker is installed and running"
echo

# Check if docker-compose is available
echo "[2/8] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available"
    echo "Please install Docker Compose"
    exit 1
fi
print_status "Docker Compose is available"
echo

# Setup environment file
echo "[3/8] Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.docker" ]; then
        cp ".env.docker" ".env"
        print_status "Environment file created from template"
        echo
        print_warning "IMPORTANT: Please edit .env file with your actual configuration:"
        echo "  - Database passwords"
        echo "  - API keys for trading exchanges"
        echo "  - Email settings"
        echo "  - Security keys"
        echo
        read -p "Press Enter to continue or Ctrl+C to exit and configure .env first..."
    else
        print_error ".env.docker template not found"
        exit 1
    fi
else
    print_status "Environment file already exists"
fi
echo

# Create necessary directories
echo "[4/8] Creating necessary directories..."
mkdir -p backend/logs
mkdir -p backend/data
mkdir -p nginx
print_status "Directories created"
echo

# Stop any existing containers
echo "[5/8] Stopping existing containers..."
docker-compose down &> /dev/null || docker compose down &> /dev/null || true
print_status "Existing containers stopped"
echo

# Build and start services
echo "[6/8] Building and starting services..."
print_info "This may take several minutes on first run..."
if command -v docker-compose &> /dev/null; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

if [ $? -ne 0 ]; then
    print_error "Failed to start services"
    echo "Check the logs with: docker-compose logs or docker compose logs"
    exit 1
fi
print_status "Services started successfully"
echo

# Wait for services to be healthy
echo "[7/8] Waiting for services to be ready..."
print_info "Checking database connection..."
while ! docker-compose exec -T postgres pg_isready -U postgres &> /dev/null && ! docker compose exec -T postgres pg_isready -U postgres &> /dev/null; do
    echo "Waiting for database..."
    sleep 5
done
print_status "Database is ready"

print_info "Checking backend API..."
while ! curl -f http://localhost:5000/health &> /dev/null; do
    echo "Waiting for backend API..."
    sleep 5
done
print_status "Backend API is ready"

print_info "Checking frontend..."
while ! curl -f http://localhost:3000/health &> /dev/null; do
    echo "Waiting for frontend..."
    sleep 3
done
print_status "Frontend is ready"
echo

# Final status check
echo "[8/8] Final deployment status..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi
echo

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Your Trading Bot is now running:"
echo
echo -e "🌐 Frontend:     ${BLUE}http://localhost:3000${NC}"
echo -e "🔧 Backend API:  ${BLUE}http://localhost:5000${NC}"
echo -e "📊 Database:     ${BLUE}localhost:5432${NC}"
echo -e "🔴 Redis:        ${BLUE}localhost:6379${NC}"
echo
echo "Useful commands:"
echo "  View logs:      docker-compose logs -f  (or docker compose logs -f)"
echo "  Stop services:  docker-compose down     (or docker compose down)"
echo "  Restart:        docker-compose restart  (or docker compose restart)"
echo "  Update:         docker-compose pull && docker-compose up -d"
echo
echo -e "📖 Check the ${BLUE}README.md${NC} for detailed usage instructions"
echo -e "🔒 Remember to secure your API keys and change default passwords!"
echo