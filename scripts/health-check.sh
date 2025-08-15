#!/bin/bash
# =============================================================================
# TradingBot Pro - Health Check Script
# =============================================================================
# This script performs comprehensive health checks on the trading bot platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:5000"
TIMEOUT=10

echo -e "${BLUE}=== Trading Bot Platform Health Check ===${NC}"
echo "Date: $(date)"
echo ""

# Function to check service status
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "Checking $service_name... "
    if eval "$check_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        return 1
    fi
}

# Check if Docker is running
echo -e "${YELLOW}Docker Services:${NC}"
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker is running${NC}"
        
        # Check Docker Compose services
        if command -v docker-compose >/dev/null 2>&1; then
            echo ""
            echo "Service Status:"
            docker-compose ps
        fi
    else
        echo -e "${RED}✗ Docker is not running${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Application Health:${NC}"

# Check API health endpoint
check_service "API Health" "curl -s -f --max-time $TIMEOUT $API_URL/health"

# Check detailed health endpoint
echo -n "Checking detailed health... "
HEALTH_RESPONSE=$(curl -s --max-time $TIMEOUT "$API_URL/api/health/detailed" 2>/dev/null || echo "")
if [ -n "$HEALTH_RESPONSE" ]; then
    echo -e "${GREEN}✓ Available${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Unavailable${NC}"
fi

echo ""
echo -e "${YELLOW}Infrastructure Health:${NC}"

# Check database (if running in Docker)
if docker-compose ps postgres | grep -q "Up"; then
    check_service "Database" "docker-compose exec -T postgres pg_isready -U tradingbot"
else
    echo -e "${RED}✗ Database container not running${NC}"
fi

# Check Redis (if running in Docker)
if docker-compose ps redis | grep -q "Up"; then
    check_service "Redis" "docker-compose exec -T redis redis-cli ping"
else
    echo -e "${RED}✗ Redis container not running${NC}"
fi

echo ""
echo -e "${YELLOW}System Resources:${NC}"

# Check disk space
echo "Disk Usage:"
df -h | grep -E '(Filesystem|/dev/)' | head -5

echo ""
echo "Memory Usage:"
free -h

echo ""
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2 $3}' | sed 's/%us,/% user,/' | sed 's/%sy/% system/'

echo ""
echo -e "${YELLOW}Container Resources:${NC}"
if command -v docker >/dev/null 2>&1; then
    echo "Container Stats:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "No containers running"
fi

echo ""
echo -e "${YELLOW}Log Analysis:${NC}"

# Check for recent errors in logs
echo "Recent errors (last 100 lines):"
if [ -d "logs" ]; then
    find logs -name "*.log" -type f -exec tail -100 {} \; | grep -i error | tail -10 || echo "No recent errors found"
else
    echo "No logs directory found"
fi

# Check Docker logs for errors
echo ""
echo "Recent Docker errors (last 50 lines):"
docker-compose logs --tail=50 2>/dev/null | grep -i error | tail -10 || echo "No recent Docker errors found"

echo ""
echo -e "${YELLOW}Network Connectivity:${NC}"

# Check external API connectivity
check_service "Binance API" "curl -s --max-time 5 https://api.binance.com/api/v3/ping"
check_service "Internet Connectivity" "curl -s --max-time 5 https://www.google.com"

echo ""
echo -e "${YELLOW}Security Checks:${NC}"

# Check for exposed ports
echo "Open ports:"
netstat -tuln 2>/dev/null | grep LISTEN | head -10 || ss -tuln | grep LISTEN | head -10 || echo "Could not check ports"

echo ""
echo -e "${GREEN}Health check completed!${NC}"
echo "For detailed monitoring, visit:"
echo "- Grafana: http://localhost:3001"
echo "- Prometheus: http://localhost:9090"
echo "- API Health: $API_URL/health"

# Exit with error code if any critical services are down
if ! curl -s -f --max-time $TIMEOUT "$API_URL/health" >/dev/null 2>&1; then
    echo -e "${RED}Critical: API is not responding${NC}"
    exit 1
fi

echo -e "${GREEN}All critical services are operational${NC}"
exit 0