#!/bin/bash

# =============================================================================
# Trading Bot Docker Management Script for Linux/macOS
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

show_help() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Trading Bot Docker Management${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - Show logs (optional: service name)"
    echo "  status    - Show service status"
    echo "  update    - Update and restart services"
    echo "  backup    - Backup database and data"
    echo "  restore   - Restore from backup"
    echo "  clean     - Clean unused Docker resources"
    echo "  shell     - Access service shell (requires service name)"
    echo "  help      - Show this help"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs backend"
    echo "  $0 shell postgres"
    echo "  $0 backup"
    echo
}

start_services() {
    print_info "Starting Trading Bot services..."
    $COMPOSE_CMD up -d
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
        echo
        echo "Your Trading Bot is running:"
        echo "  Frontend: http://localhost:3000"
        echo "  Backend:  http://localhost:5000"
    else
        print_error "Failed to start services"
    fi
}

stop_services() {
    print_info "Stopping Trading Bot services..."
    $COMPOSE_CMD down
    if [ $? -eq 0 ]; then
        print_success "Services stopped successfully"
    else
        print_error "Failed to stop services"
    fi
}

restart_services() {
    print_info "Restarting Trading Bot services..."
    $COMPOSE_CMD restart
    if [ $? -eq 0 ]; then
        print_success "Services restarted successfully"
    else
        print_error "Failed to restart services"
    fi
}

show_logs() {
    if [ -z "$1" ]; then
        print_info "Showing logs for all services..."
        $COMPOSE_CMD logs -f
    else
        print_info "Showing logs for $1..."
        $COMPOSE_CMD logs -f "$1"
    fi
}

show_status() {
    echo "Trading Bot Service Status:"
    echo "========================================"
    $COMPOSE_CMD ps
    echo
    echo "Resource Usage:"
    echo "========================================"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

update_services() {
    print_info "Updating Trading Bot services..."
    print_info "Pulling latest images..."
    $COMPOSE_CMD pull
    print_info "Rebuilding and restarting services..."
    $COMPOSE_CMD up --build -d
    if [ $? -eq 0 ]; then
        print_success "Services updated successfully"
    else
        print_error "Failed to update services"
    fi
}

backup_data() {
    local backup_dir="backups/$(date +%Y-%m-%d_%H-%M-%S)"
    
    print_info "Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"
    
    # Backup database
    print_info "Backing up database..."
    $COMPOSE_CMD exec -T postgres pg_dump -U postgres trading_bot > "$backup_dir/database.sql"
    if [ $? -eq 0 ]; then
        print_success "Database backup completed"
    else
        print_error "Database backup failed"
    fi
    
    # Backup application data
    if [ -d "backend/data" ]; then
        print_info "Backing up application data..."
        cp -r "backend/data" "$backup_dir/"
        print_success "Application data backup completed"
    fi
    
    # Backup logs
    if [ -d "backend/logs" ]; then
        print_info "Backing up logs..."
        cp -r "backend/logs" "$backup_dir/"
        print_success "Logs backup completed"
    fi
    
    # Backup configuration
    print_info "Backing up configuration..."
    [ -f ".env" ] && cp ".env" "$backup_dir/"
    [ -f "docker-compose.yml" ] && cp "docker-compose.yml" "$backup_dir/"
    
    print_success "Backup completed: $backup_dir"
}

restore_data() {
    if [ -z "$1" ]; then
        print_error "Please specify backup directory"
        echo "Usage: $0 restore [backup_directory]"
        return 1
    fi
    
    local restore_dir="$1"
    if [ ! -d "$restore_dir" ]; then
        print_error "Backup directory not found: $restore_dir"
        return 1
    fi
    
    print_warning "Restoring from backup: $restore_dir"
    print_warning "This will overwrite current data!"
    read -p "Are you sure? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        return 0
    fi
    
    # Stop services
    print_info "Stopping services..."
    $COMPOSE_CMD down
    
    # Restore database
    if [ -f "$restore_dir/database.sql" ]; then
        print_info "Restoring database..."
        $COMPOSE_CMD up -d postgres
        sleep 10
        $COMPOSE_CMD exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS trading_bot;"
        $COMPOSE_CMD exec -T postgres psql -U postgres -c "CREATE DATABASE trading_bot;"
        $COMPOSE_CMD exec -T postgres psql -U postgres trading_bot < "$restore_dir/database.sql"
        print_success "Database restored"
    fi
    
    # Restore application data
    if [ -d "$restore_dir/data" ]; then
        print_info "Restoring application data..."
        rm -rf "backend/data"
        cp -r "$restore_dir/data" "backend/"
        print_success "Application data restored"
    fi
    
    # Restore configuration
    if [ -f "$restore_dir/.env" ]; then
        print_info "Restoring configuration..."
        cp "$restore_dir/.env" "."
        print_success "Configuration restored"
    fi
    
    # Start services
    print_info "Starting services..."
    $COMPOSE_CMD up -d
    print_success "Restore completed"
}

clean_system() {
    print_warning "Cleaning Docker system..."
    print_warning "This will remove unused containers, networks, images, and volumes"
    read -p "Are you sure? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Clean cancelled"
        return 0
    fi
    
    docker system prune -a --volumes -f
    print_success "Docker system cleaned"
}

shell_access() {
    if [ -z "$1" ]; then
        print_error "Please specify service name"
        echo "Available services: backend, frontend, postgres, redis, nginx"
        return 1
    fi
    
    local service="$1"
    print_info "Accessing $service shell..."
    
    case $service in
        "backend")
            $COMPOSE_CMD exec backend /bin/bash
            ;;
        "frontend")
            $COMPOSE_CMD exec frontend /bin/sh
            ;;
        "postgres")
            $COMPOSE_CMD exec postgres psql -U postgres trading_bot
            ;;
        "redis")
            $COMPOSE_CMD exec redis redis-cli
            ;;
        "nginx")
            $COMPOSE_CMD exec nginx /bin/sh
            ;;
        *)
            print_error "Unknown service: $service"
            echo "Available services: backend, frontend, postgres, redis, nginx"
            ;;
    esac
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

command="$1"
shift

case $command in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "logs")
        show_logs "$1"
        ;;
    "status")
        show_status
        ;;
    "update")
        update_services
        ;;
    "backup")
        backup_data
        ;;
    "restore")
        restore_data "$1"
        ;;
    "clean")
        clean_system
        ;;
    "shell")
        shell_access "$1"
        ;;
    "help")
        show_help
        ;;
    *)
        print_error "Unknown command: $command"
        show_help
        exit 1
        ;;
esac