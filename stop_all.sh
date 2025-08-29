#!/bin/bash

# Trading Bot Pro - Stop All Services
# This script stops all components of Trading Bot Pro

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
echo "   Trading Bot Pro - Stop All Services"
echo "========================================"
echo

echo "Stopping all Trading Bot Pro services..."
echo

# Function to stop process by PID file
stop_by_pid() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            sleep 2
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
            print_status "$service_name stopped (PID: $pid)"
        else
            print_warning "$service_name was not running"
        fi
        rm -f "$pid_file"
    else
        print_warning "No PID file found for $service_name"
    fi
}

# Function to stop process by port
stop_by_port() {
    local service_name=$1
    local port=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        kill $pid 2>/dev/null
        sleep 1
        # Force kill if still running
        local still_running=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$still_running" ]; then
            kill -9 $still_running 2>/dev/null
        fi
        print_status "$service_name stopped (port $port)"
    else
        print_warning "No process found on port $port"
    fi
}

# Stop services using PID files first
echo "[1/4] Stopping services using PID files..."
stop_by_pid "Web Dashboard" "pids/frontend.pid"
stop_by_pid "Backend API" "pids/backend.pid"
stop_by_pid "License Server" "pids/license-server.pid"

# Stop services by port as backup
echo "[2/4] Stopping services by port..."
stop_by_port "Web Dashboard" "3000"
stop_by_port "Backend API" "5000"
stop_by_port "License Server" "8080"

# Kill any remaining Node.js processes related to our app
echo "[3/4] Cleaning up Node.js processes..."
pkill -f "npm run dev" 2>/dev/null && print_status "Stopped npm dev processes" || print_warning "No npm dev processes found"
pkill -f "web-dashboard" 2>/dev/null && print_status "Stopped web-dashboard processes" || print_warning "No web-dashboard processes found"

# Kill any remaining Python processes related to our app
echo "[4/4] Cleaning up Python processes..."
pkill -f "app.py" 2>/dev/null && print_status "Stopped Python app processes" || print_warning "No Python app processes found"

# Wait a moment for processes to fully terminate
sleep 2

# Verify ports are free
echo
echo "Verifying services are stopped..."

if ! lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "Port 3000 is free"
else
    print_warning "Port 3000 is still in use"
fi

if ! lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "Port 5000 is free"
else
    print_warning "Port 5000 is still in use"
fi

if ! lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "Port 8080 is free"
else
    print_warning "Port 8080 is still in use"
fi

# Clean up PID directory
if [ -d "pids" ]; then
    rm -f pids/*.pid
    print_info "Cleaned up PID files"
fi

echo
echo "========================================"
echo "🛑 All services have been stopped!"
echo "========================================"
echo
echo "🚀 To start services again, run: ./start_all.sh"
echo "🔄 To restart services, run: ./restart_all.sh"
echo "⚡ For quick demo setup, run: ./quick_start.sh"
echo
echo "📝 Logs are preserved in logs/ directory"
echo