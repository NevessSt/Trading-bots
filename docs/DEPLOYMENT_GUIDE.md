# 🚀 Trading Bot Platform - Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Development Deployment](#development-deployment)
5. [Staging Deployment](#staging-deployment)
6. [Production Deployment](#production-deployment)
7. [Docker Deployment](#docker-deployment)
8. [Cloud Deployment](#cloud-deployment)
9. [Database Setup](#database-setup)
10. [SSL Configuration](#ssl-configuration)
11. [Monitoring Setup](#monitoring-setup)
12. [Backup & Recovery](#backup--recovery)
13. [Troubleshooting](#troubleshooting)
14. [Maintenance](#maintenance)

## Overview

This guide covers deploying the Trading Bot Platform across different environments. The platform consists of:

- **Frontend:** React application (served by Nginx)
- **Backend:** Flask API server
- **Database:** PostgreSQL
- **Cache:** Redis
- **Reverse Proxy:** Nginx
- **Monitoring:** Prometheus + Grafana (optional)

### Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Internet  │───►│    Nginx    │───►│   Frontend  │
│             │    │ (Port 80/443)│    │ (Port 3000) │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐    ┌─────────────┐
                   │   Backend   │───►│ PostgreSQL  │
                   │ (Port 5000) │    │ (Port 5432) │
                   └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │    Redis    │
                   │ (Port 6379) │
                   └─────────────┘
```

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 20GB SSD
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+

#### Recommended Requirements
- **CPU:** 4 cores
- **RAM:** 8GB
- **Storage:** 50GB SSD
- **OS:** Ubuntu 22.04 LTS

### Software Dependencies

```bash
# Required software
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)
- PostgreSQL 14+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Nginx 1.20+ (if not using Docker)
```

### External Services

- **Domain & SSL:** Domain name with SSL certificate
- **Email Service:** SMTP server (Gmail, SendGrid, etc.)
- **Payment Processing:** Stripe account
- **Exchange APIs:** Binance, Coinbase Pro, etc.
- **Monitoring:** Optional (Prometheus, Grafana)

## Environment Setup

### Environment Variables

Create environment files for each deployment stage:

#### `.env.development`
```bash
# Application
FLASK_ENV=development
DEBUG=true
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:5000

# Database
DATABASE_URL=postgresql://tradingbot:password@localhost:5432/tradingbot_dev
REDIS_URL=redis://localhost:6379/0

# Security (use weak keys for development)
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret
ENCRYPTION_KEY=dev-encryption-key

# Email (use console backend for development)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_USERNAME=
MAIL_PASSWORD=

# External APIs (use testnet)
BINANCE_API_URL=https://testnet.binance.vision
COINBASE_API_URL=https://api-public.sandbox.pro.coinbase.com

# Stripe (use test keys)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...
```

#### `.env.staging`
```bash
# Application
FLASK_ENV=staging
DEBUG=false
FRONTEND_URL=https://staging.yourdomain.com
BACKEND_URL=https://api-staging.yourdomain.com

# Database
DATABASE_URL=postgresql://tradingbot:secure_password@db:5432/tradingbot_staging
REDIS_URL=redis://redis:6379/0

# Security (use strong keys)
SECRET_KEY=your-strong-secret-key-here
JWT_SECRET_KEY=your-strong-jwt-secret-here
ENCRYPTION_KEY=your-strong-encryption-key-here

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# External APIs (use testnet for staging)
BINANCE_API_URL=https://testnet.binance.vision
COINBASE_API_URL=https://api-public.sandbox.pro.coinbase.com

# Stripe (use test keys for staging)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...
```

#### `.env.production`
```bash
# Application
FLASK_ENV=production
DEBUG=false
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com

# Database
DATABASE_URL=postgresql://tradingbot:very_secure_password@db:5432/tradingbot_prod
REDIS_URL=redis://redis:6379/0

# Security (use very strong keys)
SECRET_KEY=your-very-strong-secret-key-here
JWT_SECRET_KEY=your-very-strong-jwt-secret-here
ENCRYPTION_KEY=your-very-strong-encryption-key-here

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# External APIs (use production)
BINANCE_API_URL=https://api.binance.com
COINBASE_API_URL=https://api.pro.coinbase.com

# Stripe (use live keys)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_live_...

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Security Key Generation

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"  # SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"  # JWT_SECRET_KEY

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Development Deployment

### Local Development Setup

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/trading-bot-platform.git
cd trading-bot-platform
```

2. **Setup Backend**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env.development
# Edit .env.development with your settings

# Start services with Docker
docker-compose up -d postgres redis

# Initialize database
flask db upgrade

# Create admin user
python scripts/create_admin.py

# Start development server
flask run --debug --host=0.0.0.0 --port=5000
```

3. **Setup Frontend**
```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

4. **Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Documentation: http://localhost:5000/docs

### Development with Docker

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## Staging Deployment

### Staging Environment Setup

1. **Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply docker group
```

2. **Deploy Application**
```bash
# Clone repository
git clone https://github.com/yourusername/trading-bot-platform.git
cd trading-bot-platform

# Checkout staging branch
git checkout staging

# Setup environment
cp .env.example .env.staging
# Edit .env.staging with staging configuration

# Deploy with Docker Compose
docker-compose -f docker-compose.staging.yml up -d

# Run database migrations
docker-compose -f docker-compose.staging.yml exec backend flask db upgrade

# Create admin user
docker-compose -f docker-compose.staging.yml exec backend python scripts/create_admin.py
```

3. **Configure Nginx**
```nginx
# /etc/nginx/sites-available/staging.yourdomain.com
server {
    listen 80;
    server_name staging.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/staging.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://staging.yourdomain.com";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
    }
}
```

4. **Enable Site**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/staging.yourdomain.com /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Production Deployment

### Production Server Setup

1. **Server Hardening**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

2. **Install Dependencies**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

3. **Deploy Application**
```bash
# Create application directory
sudo mkdir -p /opt/trading-bot
sudo chown $USER:$USER /opt/trading-bot
cd /opt/trading-bot

# Clone repository
git clone https://github.com/yourusername/trading-bot-platform.git .

# Checkout production branch
git checkout main

# Setup environment
cp .env.example .env.production
# Edit .env.production with production configuration

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend flask db upgrade

# Create admin user
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py
```

4. **Configure Production Nginx**
```nginx
# /etc/nginx/sites-available/yourdomain.com
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://yourdomain.com$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.yourdomain.com;
    return 301 https://yourdomain.com$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.stripe.com;";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=trading:10m rate=10r/m;
    
    location /api/v2/auth/ {
        limit_req zone=auth burst=10 nodelay;
        proxy_pass http://localhost:5000;
    }
    
    location /api/trading/ {
        limit_req zone=trading burst=20 nodelay;
        proxy_pass http://localhost:5000;
    }
    
    location /api/ {
        limit_req zone=api burst=30 nodelay;
    }
}
```

5. **Enable Production Site**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Docker Deployment

### Docker Compose Files

#### `docker-compose.yml` (Development)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: tradingbot_dev
      POSTGRES_USER: tradingbot
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://tradingbot:password@postgres:5432/tradingbot_dev
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    command: flask run --host=0.0.0.0 --debug

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:5000
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

#### `docker-compose.prod.yml` (Production)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: tradingbot_prod
      POSTGRES_USER: tradingbot
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    networks:
      - backend

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - backend
    command: redis-server --appendonly yes

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://tradingbot:${POSTGRES_PASSWORD}@postgres:5432/tradingbot_prod
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - backend
    ports:
      - "5000:5000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    restart: unless-stopped
    networks:
      - frontend
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/sites:/etc/nginx/conf.d
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - frontend
      - backend

  # Optional: Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - backend

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped
    networks:
      - backend

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  frontend:
  backend:
```

### Dockerfile Examples

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile.prod
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile.prod
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS Cluster**
```bash
# Install AWS CLI
aws configure

# Create cluster
aws ecs create-cluster --cluster-name trading-bot-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
    --cluster trading-bot-cluster \
    --service-name trading-bot-service \
    --task-definition trading-bot:1 \
    --desired-count 2
```

2. **Task Definition Example**
```json
{
  "family": "trading-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/trading-bot-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/trading-bot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Using AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize application
eb init trading-bot-platform

# Create environment
eb create production

# Deploy
eb deploy
```

### Google Cloud Platform

#### Using Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/trading-bot-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/trading-bot-frontend

# Deploy to Cloud Run
gcloud run deploy trading-bot-backend \
    --image gcr.io/PROJECT_ID/trading-bot-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

gcloud run deploy trading-bot-frontend \
    --image gcr.io/PROJECT_ID/trading-bot-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

### DigitalOcean App Platform

```yaml
# .do/app.yaml
name: trading-bot-platform
services:
- name: backend
  source_dir: /backend
  github:
    repo: your-username/trading-bot-platform
    branch: main
  run_command: gunicorn --bind 0.0.0.0:5000 app:app
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: FLASK_ENV
    value: production
  - key: DATABASE_URL
    type: SECRET
    value: your-database-url

- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/trading-bot-platform
    branch: main
  build_command: npm run build
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs

databases:
- name: postgres
  engine: PG
  version: "14"
  size: basic-xs
```

## Database Setup

### PostgreSQL Configuration

#### Production PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

```sql
-- Create database
CREATE DATABASE tradingbot_prod;

-- Create user
CREATE USER tradingbot WITH PASSWORD 'very_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tradingbot_prod TO tradingbot;

-- Exit
\q
```

#### Performance Tuning

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/postgresql.conf
```

```ini
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 4MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Connection settings
max_connections = 100

# Logging
log_statement = 'mod'
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

#### Backup Configuration

```bash
# Create backup script
sudo nano /usr/local/bin/backup-db.sh
```

```bash
#!/bin/bash

# Database backup script
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/opt/backups/postgres"
DB_NAME="tradingbot_prod"
DB_USER="tradingbot"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Remove backups older than 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

```bash
# Make script executable
sudo chmod +x /usr/local/bin/backup-db.sh

# Add to crontab (daily backup at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-db.sh
```

### Redis Configuration

#### Production Redis Setup

```bash
# Install Redis
sudo apt install redis-server -y

# Configure Redis
sudo nano /etc/redis/redis.conf
```

```ini
# Security
bind 127.0.0.1
requirepass your_secure_redis_password

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

```bash
# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## SSL Configuration

### Let's Encrypt SSL

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run

# Setup automatic renewal
sudo crontab -e
0 12 * * * /usr/bin/certbot renew --quiet
```

### Custom SSL Certificate

```bash
# Create SSL directory
sudo mkdir -p /etc/ssl/private
sudo mkdir -p /etc/ssl/certs

# Copy certificate files
sudo cp yourdomain.com.crt /etc/ssl/certs/
sudo cp yourdomain.com.key /etc/ssl/private/

# Set permissions
sudo chmod 644 /etc/ssl/certs/yourdomain.com.crt
sudo chmod 600 /etc/ssl/private/yourdomain.com.key
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'trading-bot-backend'
    static_configs:
      - targets: ['backend:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Alert Rules

```yaml
# monitoring/alert_rules.yml
groups:
- name: trading-bot-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      description: "Error rate is {{ $value }} errors per second"

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Database is down
      description: "PostgreSQL database is not responding"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High memory usage
      description: "Memory usage is above 90%"

  - alert: DiskSpaceLow
    expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Low disk space
      description: "Disk usage is above 80%"
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Trading Bot Platform",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Bots",
        "type": "singlestat",
        "targets": [
          {
            "expr": "active_trading_bots_total",
            "legendFormat": "Active Bots"
          }
        ]
      }
    ]
  }
}
```

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# /usr/local/bin/backup-system.sh

set -e

# Configuration
BACKUP_DIR="/opt/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR/{database,files,configs}

echo "Starting backup process..."

# Database backup
echo "Backing up database..."
docker-compose exec -T postgres pg_dump -U tradingbot tradingbot_prod | gzip > $BACKUP_DIR/database/db_backup_$DATE.sql.gz

# Application files backup
echo "Backing up application files..."
tar -czf $BACKUP_DIR/files/app_backup_$DATE.tar.gz /opt/trading-bot --exclude='*.log' --exclude='node_modules'

# Configuration backup
echo "Backing up configurations..."
cp /etc/nginx/sites-available/* $BACKUP_DIR/configs/
cp /opt/trading-bot/.env.production $BACKUP_DIR/configs/env_backup_$DATE

# Upload to cloud storage (optional)
if [ "$CLOUD_BACKUP" = "true" ]; then
    echo "Uploading to cloud storage..."
    aws s3 sync $BACKUP_DIR s3://your-backup-bucket/trading-bot-backups/
fi

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*backup_*" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully!"
```

### Recovery Procedures

#### Database Recovery

```bash
# Stop application
docker-compose down

# Restore database
gunzip -c /opt/backups/database/db_backup_YYYYMMDD_HHMMSS.sql.gz | docker-compose exec -T postgres psql -U tradingbot -d tradingbot_prod

# Start application
docker-compose up -d
```

#### Full System Recovery

```bash
# Restore application files
cd /opt
sudo rm -rf trading-bot
sudo tar -xzf /opt/backups/files/app_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore configurations
sudo cp /opt/backups/configs/yourdomain.com /etc/nginx/sites-available/
sudo cp /opt/backups/configs/env_backup_YYYYMMDD_HHMMSS /opt/trading-bot/.env.production

# Restart services
sudo systemctl reload nginx
cd /opt/trading-bot
docker-compose up -d
```

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check Docker containers
docker-compose ps

# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check environment variables
docker-compose exec backend env | grep -E '(DATABASE|REDIS|SECRET)'

# Test database connection
docker-compose exec backend python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Test connection
psql -h localhost -U tradingbot -d tradingbot_prod

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

#### High Memory Usage

```bash
# Check memory usage
free -h
docker stats

# Check for memory leaks
docker-compose exec backend python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Restart services if needed
docker-compose restart backend
```

#### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Test SSL configuration
ssl-cert-check -c /etc/letsencrypt/live/yourdomain.com/fullchain.pem

# Renew certificate
sudo certbot renew --force-renewal
```

### Performance Issues

#### Slow API Responses

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s "https://api.yourdomain.com/health"

# Check database performance
docker-compose exec postgres psql -U tradingbot -d tradingbot_prod -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check Redis performance
docker-compose exec redis redis-cli info stats
```

#### High CPU Usage

```bash
# Check CPU usage
top
htop
docker stats

# Check for CPU-intensive processes
ps aux --sort=-%cpu | head -10

# Profile Python application
docker-compose exec backend python -m cProfile -s cumulative app.py
```

### Log Analysis

```bash
# Application logs
docker-compose logs -f --tail=100 backend

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -f -u docker

# Filter error logs
docker-compose logs backend | grep ERROR
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks

```bash
# Check system health
./scripts/health-check.sh

# Monitor disk space
df -h

# Check application logs for errors
docker-compose logs --since=24h backend | grep -i error

# Verify backups
ls -la /opt/backups/database/ | tail -5
```

#### Weekly Tasks

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services
docker-compose restart

# Clean up Docker
docker system prune -f

# Analyze database performance
docker-compose exec postgres psql -U tradingbot -d tradingbot_prod -c "SELECT * FROM pg_stat_user_tables;"
```

#### Monthly Tasks

```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Rotate logs
sudo logrotate -f /etc/logrotate.conf

# Security updates
sudo unattended-upgrades

# Certificate renewal check
sudo certbot certificates
```

### Update Procedures

#### Application Updates

```bash
# Backup before update
./scripts/backup-system.sh

# Pull latest code
git pull origin main

# Update dependencies
docker-compose build --no-cache

# Run database migrations
docker-compose exec backend flask db upgrade

# Deploy updates
docker-compose up -d

# Verify deployment
./scripts/health-check.sh
```

#### Security Updates

```bash
# Update system packages
sudo apt update && sudo apt list --upgradable
sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Check for security vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image trading-bot-backend:latest
```

### Monitoring Scripts

#### Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

set -e

echo "=== Trading Bot Platform Health Check ==="
echo "Date: $(date)"
echo

# Check services
echo "Checking services..."
docker-compose ps
echo

# Check API health
echo "Checking API health..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
if [ "$API_STATUS" = "200" ]; then
    echo "✓ API is healthy"
else
    echo "✗ API is unhealthy (Status: $API_STATUS)"
fi
echo

# Check database
echo "Checking database..."
DB_STATUS=$(docker-compose exec -T postgres pg_isready -U tradingbot)
if echo "$DB_STATUS" | grep -q "accepting connections"; then
    echo "✓ Database is healthy"
else
    echo "✗ Database is unhealthy"
fi
echo

# Check Redis
echo "Checking Redis..."
REDIS_STATUS=$(docker-compose exec -T redis redis-cli ping)
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo "✓ Redis is healthy"
else
    echo "✗ Redis is unhealthy"
fi
echo

# Check disk space
echo "Checking disk space..."
df -h | grep -E '(Filesystem|/dev/)'
echo

# Check memory usage
echo "Checking memory usage..."
free -h
echo

echo "Health check completed!"
```

---

**Support & Documentation:**
- 📧 Technical Support: devops@tradingbot.com
- 📚 Documentation: docs.tradingbot.com
- 🐛 Issues: github.com/tradingbot/issues
- 💬 Community: discord.gg/tradingbot

**Last Updated:** January 2024
**Version:** 2.0.0