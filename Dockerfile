# TradingBot Pro - Docker Configuration
# Multi-stage build for optimized production image

# Build stage
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Python base stage
FROM python:3.11-slim AS python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.6.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Development stage
FROM python-base AS development

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov black flake8 mypy

# Copy application code
COPY . .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create non-root user
RUN groupadd -r tradingbot && useradd -r -g tradingbot tradingbot
RUN chown -R tradingbot:tradingbot /app
USER tradingbot

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["python", "main.py"]

# Production stage
FROM python-base AS production

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/

# Install Python dependencies (production only)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install production server
RUN pip install --no-cache-dir gunicorn gevent

# Copy application code
COPY backend/ ./backend/
COPY templates/ ./templates/
COPY config.py ./
COPY main.py ./
COPY cli.py ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create necessary directories
RUN mkdir -p logs data backups

# Create non-root user
RUN groupadd -r tradingbot && useradd -r -g tradingbot tradingbot
RUN chown -R tradingbot:tradingbot /app
USER tradingbot

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production command with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "30", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "50", "--preload", "main:app"]

# Testing stage
FROM development AS testing

# Install additional testing dependencies
RUN pip install --no-cache-dir \
    pytest-xdist \
    pytest-mock \
    pytest-asyncio \
    coverage \
    bandit \
    safety

# Run tests
RUN python -m pytest backend/tests/ -v --cov=backend --cov-report=html --cov-report=term

# Run security checks
RUN bandit -r backend/ -f json -o security-report.json || true
RUN safety check --json --output safety-report.json || true

# Linting stage
FROM development AS linting

# Install linting tools
RUN pip install --no-cache-dir \
    black \
    flake8 \
    mypy \
    isort \
    pylint

# Run linting
RUN black --check backend/
RUN flake8 backend/
RUN isort --check-only backend/
RUN mypy backend/ --ignore-missing-imports
RUN pylint backend/ --disable=all --enable=E,W,C,R --output-format=json > pylint-report.json || true