#!/bin/bash

# Trading Bot Pro - Restart All Services
# This script stops and then starts all components of Trading Bot Pro

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "========================================"
echo "  Trading Bot Pro - Restart All Services"
echo "========================================"
echo

echo "Restarting all Trading Bot Pro services..."
echo "This will stop all running services and start them again."
echo

# Check if scripts exist
if [ ! -f "stop_all.sh" ]; then
    print_error "stop_all.sh not found in current directory"
    exit 1
fi

if [ ! -f "start_all.sh" ]; then
    print_error "start_all.sh not found in current directory"
    exit 1
fi

# Make scripts executable if they aren't already
chmod +x stop_all.sh start_all.sh

# First, stop all services
echo "Step 1: Stopping existing services..."
echo "======================================"
./stop_all.sh

# Wait a moment for complete shutdown
echo
print_info "Waiting for complete shutdown..."
sleep 3

# Then start all services
echo
echo "Step 2: Starting all services..."
echo "================================"
./start_all.sh

echo
echo "========================================"
echo "🔄 Restart completed successfully!"
echo "========================================"
echo
echo "All services should now be running with fresh instances."
echo "Check the browser window that opened automatically."
echo
print_info "If you encounter any issues, check the logs in logs/ directory"
echo