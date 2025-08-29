#!/bin/bash

# Trading Bot Pro - Start All Services
# This script starts all components of Trading Bot Pro

set -e

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
echo "   Trading Bot Pro - Start All Services"
echo "========================================"
echo

# Check if ports are already in use
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 3000 is already in use (Frontend may be running)"
fi

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 5000 is already in use (Backend may be running)"
fi

if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 8080 is already in use (License server may be running)"
fi

echo
echo "Starting all services..."
echo

# Determine Python command
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Start License Server
echo "[1/3] Starting License Server..."
if [ -d "license-server" ] && [ -f "license-server/app.py" ]; then
    cd license-server
    nohup $PYTHON_CMD app.py > ../logs/license-server.log 2>&1 &
    LICENSE_PID=$!
    echo $LICENSE_PID > ../pids/license-server.pid
    cd ..
    sleep 2
    print_status "License Server started on port 8080 (PID: $LICENSE_PID)"
else
    print_warning "License Server not found, skipping..."
fi

# Start Backend
echo "[2/3] Starting Backend API..."
if [ -d "backend" ] && [ -f "backend/app.py" ]; then
    cd backend
    nohup $PYTHON_CMD app.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../pids/backend.pid
    cd ..
    sleep 3
    print_status "Backend API started on port 5000 (PID: $BACKEND_PID)"
else
    print_error "Backend not found!"
    exit 1
fi

# Start Frontend
echo "[3/3] Starting Web Dashboard..."
if [ -d "web-dashboard" ] && [ -f "web-dashboard/package.json" ]; then
    cd web-dashboard
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../pids/frontend.pid
    cd ..
    sleep 5
    print_status "Web Dashboard started on port 3000 (PID: $FRONTEND_PID)"
else
    print_error "Web Dashboard not found!"
    exit 1
fi

echo
echo "========================================"
echo "🚀 All services are now running!"
echo "========================================"
echo
echo "📊 Web Dashboard: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000/health"
echo "🔑 License Server: http://localhost:8080/health"
echo
echo "📱 Mobile App Connection:"
echo "   Server URL: http://$(hostname -I | awk '{print $1}'):5000"
echo "   (Use your actual IP address for mobile connections)"
echo
echo "🛑 To stop all services, run: ./stop_all.sh"
echo "🔄 To restart all services, run: ./restart_all.sh"
echo
echo "📋 Process IDs saved in pids/ directory"
echo "📝 Logs available in logs/ directory"
echo

# Create directories for PIDs and logs if they don't exist
mkdir -p pids logs

# Try to open browser automatically
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &> /dev/null &
    print_info "Opening browser automatically..."
elif command -v open &> /dev/null; then
    open http://localhost:3000 &> /dev/null &
    print_info "Opening browser automatically..."
else
    print_info "Please open http://localhost:3000 in your browser"
fi

echo "Services are running in the background."
echo "You can close this terminal safely."
echo