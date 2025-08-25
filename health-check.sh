#!/bin/bash

# =============================================================================
# Trading Bot Health Check Script for Linux/macOS
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
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

# Check if docker-compose command exists
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        print_error "Docker Compose not found"
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)
all_healthy=true

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Trading Bot Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check if Docker is running
echo "[1/6] Checking Docker status..."
if docker info &> /dev/null; then
    print_success "Docker is running"
else
    print_error "Docker is not running"
    all_healthy=false
fi
echo

# Check container status
echo "[2/6] Checking container status..."
container_ids=$($COMPOSE_CMD ps -q)
if [ -z "$container_ids" ]; then
    print_error "No containers are running"
    all_healthy=false
else
    for container_id in $container_ids; do
        container_name=$(docker inspect --format='{{.Name}}' "$container_id" | sed 's/^\///')
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "no-health-check")
        
        if [ "$health_status" = "healthy" ]; then
            print_success "$container_name is healthy"
        elif [ "$health_status" = "unhealthy" ]; then
            print_error "$container_name is unhealthy"
            all_healthy=false
        else
            status=$(docker inspect --format='{{.State.Status}}' "$container_id")
            if [ "$status" = "running" ]; then
                print_success "$container_name is running"
            else
                print_error "$container_name is $status"
                all_healthy=false
            fi
        fi
    done
fi
echo

# Check database connectivity
echo "[3/6] Checking database connectivity..."
if $COMPOSE_CMD exec -T postgres pg_isready -U postgres &> /dev/null; then
    print_success "Database is accessible"
else
    print_error "Database is not accessible"
    all_healthy=false
fi
echo

# Check Redis connectivity
echo "[4/6] Checking Redis connectivity..."
if $COMPOSE_CMD exec -T redis redis-cli ping &> /dev/null; then
    print_success "Redis is accessible"
else
    print_error "Redis is not accessible"
    all_healthy=false
fi
echo

# Check backend API
echo "[5/6] Checking backend API..."
if curl -f -s http://localhost:5000/health &> /dev/null; then
    print_success "Backend API is responding"
    
    # Get API status details
    response=$(curl -s http://localhost:5000/health 2>/dev/null || echo "No response")
    echo "  Response: $response"
else
    print_error "Backend API is not responding"
    all_healthy=false
fi
echo

# Check frontend
echo "[6/6] Checking frontend..."
if curl -f -s http://localhost:3000/health &> /dev/null; then
    print_success "Frontend is responding"
else
    print_error "Frontend is not responding"
    all_healthy=false
fi
echo

# Resource usage check
echo "Resource Usage:"
echo "========================================"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo

# Port check
echo "Port Status:"
echo "========================================"
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln 2>/dev/null | grep ":$port " &> /dev/null || ss -tuln 2>/dev/null | grep ":$port " &> /dev/null; then
        print_success "Port $port ($service) is open"
    else
        print_error "Port $port ($service) is not open"
    fi
}

check_port 3000 "Frontend"
check_port 5000 "Backend"
check_port 5432 "Database"
check_port 6379 "Redis"
echo

# Disk space check
echo "Disk Usage:"
echo "========================================"
df -h . | tail -1 | awk '{print "Free disk space: " $4 " (" $5 " used)"}'
echo

# Docker volume usage
echo "Docker Volume Usage:"
echo "========================================"
docker system df
echo

# Memory usage check
echo "System Memory:"
echo "========================================"
if command -v free &> /dev/null; then
    free -h
elif command -v vm_stat &> /dev/null; then
    # macOS
    vm_stat | head -5
fi
echo

# Final health status
echo "========================================"
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✓ ALL SYSTEMS HEALTHY${NC}"
    echo
    echo "Your Trading Bot is fully operational:"
    echo -e "  🌐 Frontend:    ${BLUE}http://localhost:3000${NC}"
    echo -e "  🔧 Backend API: ${BLUE}http://localhost:5000${NC}"
    echo -e "  📊 Database:    ${BLUE}localhost:5432${NC}"
    echo -e "  🔴 Redis:       ${BLUE}localhost:6379${NC}"
    echo
    echo "Next steps:"
    echo "  - Configure your trading API keys in the dashboard"
    echo "  - Set up your trading strategies"
    echo "  - Review risk management settings"
    echo "  - Enable notifications if desired"
else
    echo -e "${RED}✗ SOME ISSUES DETECTED${NC}"
    echo
    echo "Troubleshooting steps:"
    echo "  1. Check logs: $COMPOSE_CMD logs"
    echo "  2. Restart services: $COMPOSE_CMD restart"
    echo "  3. Check configuration: .env file"
    echo "  4. Verify Docker resources: docker stats"
    echo "  5. Check network connectivity"
    echo
    echo "For detailed troubleshooting, see DOCKER_DEPLOYMENT.md"
fi
echo "========================================"
echo