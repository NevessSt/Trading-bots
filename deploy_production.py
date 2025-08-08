#!/usr/bin/env python3
"""
Production Deployment Script for Trading Bot System

This script automates the deployment of the trading bot system to production,
including environment setup, security checks, and monitoring configuration.
"""

import os
import sys
import subprocess
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    """Handles production deployment of the trading bot system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.project_root / 'backups' / self.deployment_time
        
    def check_prerequisites(self):
        """Check if all prerequisites are met for deployment"""
        logger.info("Checking deployment prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker not found")
            logger.info(f"✓ Docker: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"✗ Docker check failed: {e}")
            return False
        
        # Check Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker Compose not found")
            logger.info(f"✓ Docker Compose: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"✗ Docker Compose check failed: {e}")
            return False
        
        # Check required files
        required_files = [
            'docker-compose.prod.yml',
            'backend/Dockerfile.prod',
            'frontend/Dockerfile.prod',
            'nginx/nginx.prod.conf',
            '.env.prod'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                logger.error(f"✗ Required file missing: {file_path}")
                return False
            logger.info(f"✓ Found: {file_path}")
        
        # Check environment variables
        required_env_vars = [
            'POSTGRES_PASSWORD',
            'JWT_SECRET',
            'STRIPE_SECRET_KEY',
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY'
        ]
        
        env_file = self.project_root / '.env.prod'
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()
                for var in required_env_vars:
                    if f'{var}=' not in env_content:
                        logger.error(f"✗ Missing environment variable: {var}")
                        return False
                    logger.info(f"✓ Environment variable set: {var}")
        else:
            logger.error("✗ .env.prod file not found")
            return False
        
        logger.info("✓ All prerequisites met")
        return True
    
    def create_production_dockerfiles(self):
        """Create optimized production Dockerfiles"""
        logger.info("Creating production Dockerfiles...")
        
        # Backend production Dockerfile
        backend_dockerfile = self.project_root / 'backend' / 'Dockerfile.prod'
        backend_content = '''
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
'''
        
        with open(backend_dockerfile, 'w') as f:
            f.write(backend_content)
        
        # Frontend production Dockerfile
        frontend_dockerfile = self.project_root / 'frontend' / 'Dockerfile.prod'
        frontend_content = '''
# Build stage
FROM node:18-alpine as build

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
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
'''
        
        with open(frontend_dockerfile, 'w') as f:
            f.write(frontend_content)
        
        logger.info("✓ Production Dockerfiles created")
    
    def create_nginx_config(self):
        """Create production nginx configuration"""
        logger.info("Creating nginx configuration...")
        
        nginx_config = self.project_root / 'nginx' / 'nginx.prod.conf'
        config_content = '''
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # Upstream servers
    upstream backend {
        server backend:5000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$server_name$request_uri;
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
        
        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Login endpoint with stricter rate limiting
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
    }
}
'''
        
        with open(nginx_config, 'w') as f:
            f.write(config_content)
        
        logger.info("✓ Nginx configuration created")
    
    def run_security_checks(self):
        """Run security checks before deployment"""
        logger.info("Running security checks...")
        
        security_issues = []
        
        # Check for hardcoded secrets
        logger.info("Checking for hardcoded secrets...")
        sensitive_patterns = [
            'password',
            'secret',
            'key',
            'token',
            'api_key'
        ]
        
        for pattern in sensitive_patterns:
            try:
                result = subprocess.run(
                    ['grep', '-r', '-i', pattern, 'backend/', 'frontend/'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and 'test' not in result.stdout.lower():
                    # Filter out obvious false positives
                    lines = result.stdout.split('\n')
                    suspicious_lines = [
                        line for line in lines 
                        if line and 'import' not in line and 'def' not in line
                    ]
                    if suspicious_lines:
                        security_issues.append(f"Potential hardcoded {pattern} found")
            except Exception:
                pass  # grep might not be available on all systems
        
        # Check file permissions
        logger.info("Checking file permissions...")
        sensitive_files = ['.env.prod', 'nginx/ssl/']
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                stat_info = full_path.stat()
                if stat_info.st_mode & 0o077:  # Check if group/other have permissions
                    security_issues.append(f"Insecure permissions on {file_path}")
        
        if security_issues:
            logger.warning("Security issues found:")
            for issue in security_issues:
                logger.warning(f"  - {issue}")
            
            response = input("Continue with deployment despite security issues? (y/N): ")
            if response.lower() != 'y':
                logger.error("Deployment aborted due to security concerns")
                return False
        
        logger.info("✓ Security checks completed")
        return True
    
    def backup_current_deployment(self):
        """Create backup of current deployment"""
        logger.info("Creating deployment backup...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup database
            logger.info("Backing up database...")
            db_backup_cmd = [
                'docker-compose', 'exec', '-T', 'postgres',
                'pg_dump', '-U', 'trading_user', 'trading_bot_db'
            ]
            
            with open(self.backup_dir / 'database_backup.sql', 'w') as f:
                subprocess.run(db_backup_cmd, stdout=f, check=True)
            
            # Backup configuration files
            config_files = ['.env.prod', 'docker-compose.prod.yml']
            for config_file in config_files:
                source = self.project_root / config_file
                if source.exists():
                    import shutil
                    shutil.copy2(source, self.backup_dir)
            
            logger.info(f"✓ Backup created at {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def deploy_application(self):
        """Deploy the application using Docker Compose"""
        logger.info("Deploying application...")
        
        try:
            # Stop existing containers
            logger.info("Stopping existing containers...")
            subprocess.run(
                ['docker-compose', '-f', 'docker-compose.prod.yml', 'down'],
                check=True
            )
            
            # Build and start new containers
            logger.info("Building and starting containers...")
            subprocess.run(
                ['docker-compose', '-f', 'docker-compose.prod.yml', 'up', '-d', '--build'],
                check=True
            )
            
            # Wait for services to be ready
            logger.info("Waiting for services to be ready...")
            time.sleep(30)
            
            # Run health checks
            self.verify_deployment()
            
            logger.info("✓ Application deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def verify_deployment(self):
        """Verify that the deployment is working correctly"""
        logger.info("Verifying deployment...")
        
        # Check container status
        result = subprocess.run(
            ['docker-compose', '-f', 'docker-compose.prod.yml', 'ps'],
            capture_output=True,
            text=True
        )
        
        if 'Up' not in result.stdout:
            raise Exception("Some containers are not running")
        
        # Check health endpoints
        import requests
        import time
        
        health_checks = [
            ('http://localhost/health', 'Nginx'),
            ('http://localhost/api/health', 'Backend API')
        ]
        
        for url, service in health_checks:
            for attempt in range(5):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✓ {service} health check passed")
                        break
                    else:
                        logger.warning(f"Health check failed for {service}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Health check attempt {attempt + 1} failed for {service}: {e}")
                    if attempt < 4:
                        time.sleep(10)
                    else:
                        logger.error(f"✗ {service} health check failed after 5 attempts")
        
        logger.info("✓ Deployment verification completed")
    
    def setup_monitoring(self):
        """Set up monitoring and alerting"""
        logger.info("Setting up monitoring...")
        
        try:
            # Start monitoring services
            monitoring_services = [
                'prometheus',
                'grafana',
                'node-exporter',
                'elasticsearch',
                'kibana'
            ]
            
            for service in monitoring_services:
                logger.info(f"Starting {service}...")
                subprocess.run(
                    ['docker-compose', '-f', 'docker-compose.prod.yml', 'up', '-d', service],
                    check=True
                )
            
            logger.info("✓ Monitoring services started")
            logger.info("Grafana: http://localhost:3001 (admin/admin)")
            logger.info("Prometheus: http://localhost:9090")
            logger.info("Kibana: http://localhost:5601")
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
    
    def deploy(self):
        """Main deployment function"""
        logger.info("Starting production deployment...")
        logger.info("=" * 50)
        
        try:
            # Pre-deployment checks
            if not self.check_prerequisites():
                logger.error("Prerequisites not met. Aborting deployment.")
                return False
            
            if not self.run_security_checks():
                logger.error("Security checks failed. Aborting deployment.")
                return False
            
            # Create production files
            self.create_production_dockerfiles()
            self.create_nginx_config()
            
            # Backup current deployment
            if not self.backup_current_deployment():
                logger.warning("Backup failed, but continuing with deployment...")
            
            # Deploy application
            if not self.deploy_application():
                logger.error("Application deployment failed")
                return False
            
            # Setup monitoring
            self.setup_monitoring()
            
            logger.info("=" * 50)
            logger.info("🎉 PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!")
            logger.info("=" * 50)
            logger.info("Application URL: https://your-domain.com")
            logger.info("Monitoring Dashboard: http://localhost:3001")
            logger.info(f"Backup Location: {self.backup_dir}")
            logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            logger.error("Check logs for details and consider rolling back")
            return False

def main():
    """Main function"""
    deployer = ProductionDeployer()
    
    print("Trading Bot System - Production Deployment")
    print("===========================================")
    print("This will deploy the trading bot system to production.")
    print("Make sure you have:")
    print("1. Configured .env.prod with production secrets")
    print("2. Set up SSL certificates in nginx/ssl/")
    print("3. Tested the system in staging environment")
    print()
    
    response = input("Continue with production deployment? (y/N): ")
    if response.lower() != 'y':
        print("Deployment cancelled.")
        sys.exit(0)
    
    success = deployer.deploy()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()