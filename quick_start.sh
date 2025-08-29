#!/bin/bash

# Trading Bot Pro - Quick Start Script
# This script sets up and runs Trading Bot Pro in demo mode

set -e  # Exit on any error

echo "========================================"
echo "    Trading Bot Pro - Quick Start"
echo "========================================"
echo
echo "Starting Trading Bot Pro in Demo Mode..."
echo "This will take about 2-3 minutes."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed!"
    echo "Please download and install Node.js from: https://nodejs.org"
    echo "Then run this script again."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python is not installed!"
    echo "Please download and install Python from: https://python.org"
    echo "Then run this script again."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

print_status "Node.js found: $(node --version)"
print_status "Python found: $($PYTHON_CMD --version)"
echo

# Function to cleanup on exit
cleanup() {
    echo
    print_info "Stopping all services..."
    
    # Kill background processes
    if [ ! -z "$LICENSE_PID" ]; then
        kill $LICENSE_PID 2>/dev/null || true
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on our ports
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    
    print_info "All services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Install backend dependencies
echo "[1/5] Installing backend dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements.txt > /dev/null 2>&1 || {
        print_warning "Some Python packages may have failed to install"
        print_warning "This might not affect demo mode functionality"
    }
else
    print_warning "requirements.txt not found in backend directory"
fi
cd ..

# Install frontend dependencies
echo "[2/5] Installing frontend dependencies..."
cd web-dashboard
if [ -f "package.json" ]; then
    npm install > /dev/null 2>&1 || {
        print_error "Failed to install frontend dependencies"
        echo "Please check your internet connection and try again"
        exit 1
    }
else
    print_error "package.json not found in web-dashboard directory"
    exit 1
fi
cd ..

# Build frontend for production
echo "[3/5] Building frontend..."
cd web-dashboard
npm run build > /dev/null 2>&1 || {
    print_warning "Frontend build failed, continuing with development mode"
}
cd ..

# Start license server
echo "[4/5] Starting license server..."
cd license-server
if [ -f "app.py" ]; then
    $PYTHON_CMD app.py &
    LICENSE_PID=$!
    print_status "License server started (PID: $LICENSE_PID)"
else
    print_warning "License server not found, continuing without it"
fi
cd ..

# Wait for license server to start
sleep 3

# Start backend with demo mode
echo "[5/5] Starting backend in demo mode..."
cd backend
if [ -f "app.py" ]; then
    export DEMO_MODE=true
    export LICENSE_SERVER_URL=http://localhost:8080
    $PYTHON_CMD app.py &
    BACKEND_PID=$!
    print_status "Backend started (PID: $BACKEND_PID)"
else
    print_error "Backend app.py not found"
    cleanup
    exit 1
fi
cd ..

# Wait for backend to start
sleep 5

# Start frontend development server
echo "Starting web dashboard..."
cd web-dashboard
npm run dev &
FRONTEND_PID=$!
print_status "Frontend started (PID: $FRONTEND_PID)"
cd ..

# Wait for frontend to start
sleep 10

echo
echo "========================================"
echo "🚀 Trading Bot Pro is ready!"
echo "========================================"
echo
echo "Demo Login Credentials:"
echo "  Username: demo"
echo "  Password: demo123"
echo
echo "Web Dashboard: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo "License Server: http://localhost:8080"
echo
echo "✨ Features enabled in Demo Mode:"
echo "  • Fake trading data"
echo "  • Paper trading"
echo "  • All strategies available"
echo "  • No API keys required"
echo "  • Risk-free testing"
echo
echo "Press Ctrl+C to stop all services"
echo

# Try to open browser automatically
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &> /dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &> /dev/null &
else
    print_info "Please open http://localhost:3000 in your browser"
fi

# Keep script running and wait for user to stop
echo "Waiting for services... (Press Ctrl+C to stop)"
while true; do
    sleep 1
    
    # Check if processes are still running
    if [ ! -z "$BACKEND_PID" ] && ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly"
        cleanup
        exit 1
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died unexpectedly"
        cleanup
        exit 1
    fi
done