#!/bin/bash

# TradingBot Pro - Environment Validation Script
# This script validates that all required environment variables are properly configured

set -e

echo "🔍 TradingBot Pro - Environment Validation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation results
ERRORS=0
WARNINGS=0

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

validate_required_var() {
    local var_name=$1
    local var_value=$2
    local description=$3
    
    if [ -z "$var_value" ]; then
        log_error "$var_name is required but not set ($description)"
        return 1
    else
        log_success "$var_name is configured"
        return 0
    fi
}

validate_optional_var() {
    local var_name=$1
    local var_value=$2
    local description=$3
    local default_value=$4
    
    if [ -z "$var_value" ]; then
        log_warning "$var_name not set, will use default: $default_value ($description)"
        return 1
    else
        log_success "$var_name is configured: $var_value"
        return 0
    fi
}

validate_url() {
    local var_name=$1
    local url=$2
    
    if [[ $url =~ ^https?://[a-zA-Z0-9.-]+:[0-9]+/?.*$ ]] || [[ $url =~ ^[a-zA-Z0-9.-]+:[0-9]+/?.*$ ]]; then
        log_success "$var_name URL format is valid: $url"
        return 0
    else
        log_error "$var_name URL format is invalid: $url"
        return 1
    fi
}

validate_boolean() {
    local var_name=$1
    local var_value=$2
    
    if [[ "$var_value" =~ ^(true|false|True|False|TRUE|FALSE|1|0)$ ]]; then
        log_success "$var_name boolean value is valid: $var_value"
        return 0
    else
        log_error "$var_name must be a boolean (true/false): $var_value"
        return 1
    fi
}

validate_api_key() {
    local var_name=$1
    local api_key=$2
    local min_length=$3
    
    if [ ${#api_key} -lt $min_length ]; then
        log_error "$var_name appears to be too short (${#api_key} chars, minimum $min_length)"
        return 1
    elif [[ "$api_key" =~ ^(your-|demo|test|example|placeholder) ]]; then
        log_error "$var_name appears to be a placeholder value: $api_key"
        return 1
    else
        log_success "$var_name format appears valid (${#api_key} characters)"
        return 0
    fi
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_error ".env file not found in project root"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Load environment variables
log_info "Loading environment variables from .env..."
source .env

echo ""
echo "🔐 Validating Core Security Settings..."
echo "======================================="

# JWT and Security
validate_required_var "SECRET_KEY" "$SECRET_KEY" "Flask secret key for session security"
validate_required_var "JWT_SECRET_KEY" "$JWT_SECRET_KEY" "JWT token signing key"

if [ -n "$SECRET_KEY" ] && [ ${#SECRET_KEY} -lt 32 ]; then
    log_warning "SECRET_KEY should be at least 32 characters long for security"
fi

if [ -n "$JWT_SECRET_KEY" ] && [ ${#JWT_SECRET_KEY} -lt 32 ]; then
    log_warning "JWT_SECRET_KEY should be at least 32 characters long for security"
fi

echo ""
echo "🗄️ Validating Database Configuration..."
echo "======================================="

# Database
validate_required_var "DATABASE_URL" "$DATABASE_URL" "Database connection string"
if [ -n "$DATABASE_URL" ]; then
    validate_url "DATABASE_URL" "$DATABASE_URL"
fi

# Redis
validate_optional_var "REDIS_URL" "$REDIS_URL" "Redis connection for caching" "redis://localhost:6379/0"
if [ -n "$REDIS_URL" ]; then
    validate_url "REDIS_URL" "$REDIS_URL"
fi

echo ""
echo "📈 Validating Trading Configuration..."
echo "====================================="

# Binance API
validate_required_var "BINANCE_API_KEY" "$BINANCE_API_KEY" "Binance API key for trading"
validate_required_var "BINANCE_SECRET_KEY" "$BINANCE_SECRET_KEY" "Binance secret key for trading"

if [ -n "$BINANCE_API_KEY" ]; then
    validate_api_key "BINANCE_API_KEY" "$BINANCE_API_KEY" 32
fi

if [ -n "$BINANCE_SECRET_KEY" ]; then
    validate_api_key "BINANCE_SECRET_KEY" "$BINANCE_SECRET_KEY" 32
fi

# Trading Mode
validate_optional_var "BINANCE_TESTNET" "$BINANCE_TESTNET" "Use testnet for safe testing" "true"
if [ -n "$BINANCE_TESTNET" ]; then
    validate_boolean "BINANCE_TESTNET" "$BINANCE_TESTNET"
fi

if [ "$BINANCE_TESTNET" != "true" ] && [ "$BINANCE_TESTNET" != "True" ] && [ "$BINANCE_TESTNET" != "TRUE" ]; then
    log_warning "BINANCE_TESTNET is not set to true - you will be trading with REAL MONEY!"
fi

echo ""
echo "🌐 Validating Application Configuration..."
echo "========================================="

# Flask Environment
validate_optional_var "FLASK_ENV" "$FLASK_ENV" "Flask environment mode" "production"
validate_optional_var "FLASK_DEBUG" "$FLASK_DEBUG" "Flask debug mode" "false"

if [ -n "$FLASK_DEBUG" ]; then
    validate_boolean "FLASK_DEBUG" "$FLASK_DEBUG"
fi

if [ "$FLASK_ENV" = "production" ] && [ "$FLASK_DEBUG" = "true" ]; then
    log_error "FLASK_DEBUG should not be true in production environment"
fi

# CORS
validate_optional_var "CORS_ORIGINS" "$CORS_ORIGINS" "Allowed CORS origins" "http://localhost:3000"

echo ""
echo "📊 Validating Monitoring Configuration..."
echo "======================================="

# Optional monitoring
validate_optional_var "SENTRY_DSN" "$SENTRY_DSN" "Sentry error tracking" "(disabled)"
validate_optional_var "PROMETHEUS_ENABLED" "$PROMETHEUS_ENABLED" "Prometheus metrics" "false"

if [ -n "$PROMETHEUS_ENABLED" ]; then
    validate_boolean "PROMETHEUS_ENABLED" "$PROMETHEUS_ENABLED"
fi

echo ""
echo "🔒 Validating License Configuration..."
echo "====================================="

# License
validate_optional_var "LICENSE_KEY" "$LICENSE_KEY" "Software license key" "(trial mode)"
validate_optional_var "LICENSE_SERVER_URL" "$LICENSE_SERVER_URL" "License validation server" "(local validation)"

echo ""
echo "⚙️ Validating Risk Management..."
echo "==============================="

# Risk Management
validate_optional_var "MAX_DAILY_LOSS" "$MAX_DAILY_LOSS" "Maximum daily loss limit" "1000"
validate_optional_var "POSITION_SIZE_PERCENT" "$POSITION_SIZE_PERCENT" "Position size as % of balance" "10"
validate_optional_var "MAX_OPEN_ORDERS" "$MAX_OPEN_ORDERS" "Maximum concurrent orders" "5"

# Validate numeric values
if [ -n "$MAX_DAILY_LOSS" ] && ! [[ "$MAX_DAILY_LOSS" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    log_error "MAX_DAILY_LOSS must be a positive number: $MAX_DAILY_LOSS"
fi

if [ -n "$POSITION_SIZE_PERCENT" ] && ! [[ "$POSITION_SIZE_PERCENT" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    log_error "POSITION_SIZE_PERCENT must be a positive number: $POSITION_SIZE_PERCENT"
fi

if [ -n "$MAX_OPEN_ORDERS" ] && ! [[ "$MAX_OPEN_ORDERS" =~ ^[0-9]+$ ]]; then
    log_error "MAX_OPEN_ORDERS must be a positive integer: $MAX_OPEN_ORDERS"
fi

echo ""
echo "📁 Validating File Permissions..."
echo "==============================="

# Check critical file permissions
if [ -f "backend/config/license_key.bin" ]; then
    perms=$(stat -c "%a" "backend/config/license_key.bin" 2>/dev/null || echo "unknown")
    if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
        log_success "License key file has secure permissions: $perms"
    else
        log_warning "License key file permissions should be 600 or 400, currently: $perms"
    fi
else
    log_info "License key file will be generated on first run"
fi

if [ -f ".env" ]; then
    perms=$(stat -c "%a" ".env" 2>/dev/null || echo "unknown")
    if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
        log_success ".env file has secure permissions: $perms"
    else
        log_warning ".env file should have restricted permissions (600 or 400), currently: $perms"
        log_info "Run: chmod 600 .env"
    fi
fi

echo ""
echo "📋 VALIDATION SUMMARY"
echo "===================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    log_success "✅ All environment variables are properly configured!"
    echo "Your application is ready for deployment."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    log_warning "⚠️ Environment validation completed with $WARNINGS warning(s)"
    echo "Your application should work, but consider addressing the warnings above."
    exit 0
else
    log_error "❌ Environment validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
    echo ""
    echo "Please fix the errors above before starting the application."
    echo "Common fixes:"
    echo "  • Copy .env.example to .env and configure your settings"
    echo "  • Set proper Binance API keys (get them from binance.com)"
    echo "  • Configure database connection string"
    echo "  • Set secure SECRET_KEY and JWT_SECRET_KEY (32+ characters)"
    echo ""
    echo "For help, see:"
    echo "  • README.md - Setup instructions"
    echo "  • API_INTEGRATION_GUIDE.md - API key setup"
    echo "  • docs/DEPLOYMENT.md - Production deployment guide"
    exit 1
fi