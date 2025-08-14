#!/usr/bin/env python3
"""
TradingBot Pro - Deployment Script
Automated deployment for production environments
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

class TradingBotDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_log = []
        
    def log(self, message, level="INFO"):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
    
    def run_command(self, command, description, critical=True):
        """Run a deployment command"""
        self.log(f"Executing: {description}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description} completed successfully")
                return True
            else:
                self.log(f"❌ {description} failed: {result.stderr}", "ERROR")
                if critical:
                    self.log("Deployment failed due to critical error", "ERROR")
                    sys.exit(1)
                return False
                
        except Exception as e:
            self.log(f"❌ {description} failed with exception: {str(e)}", "ERROR")
            if critical:
                sys.exit(1)
            return False
    
    def check_prerequisites(self):
        """Check deployment prerequisites"""
        self.log("Checking deployment prerequisites...")
        
        # Check if required files exist
        required_files = [
            '.env',
            'docker-compose.yml',
            'Dockerfile',
            'requirements.txt'
        ]
        
        for file_name in required_files:
            if not (self.project_root / file_name).exists():
                self.log(f"❌ Required file missing: {file_name}", "ERROR")
                return False
        
        # Check if Docker is available
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            subprocess.run(['docker-compose', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ Docker or Docker Compose not available", "ERROR")
            return False
        
        # Check environment variables
        env_file = self.project_root / '.env'
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        critical_vars = [
            'SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        for var in critical_vars:
            if f'{var}=' not in env_content or f'{var}=your-' in env_content:
                self.log(f"⚠️  Environment variable {var} may not be properly configured", "WARNING")
        
        self.log("✅ Prerequisites check completed")
        return True
    
    def backup_existing_deployment(self):
        """Backup existing deployment"""
        self.log("Creating backup of existing deployment...")
        
        backup_dir = self.project_root / "backups" / f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup database
        self.run_command(
            f"docker-compose exec -T postgres pg_dump -U tradingbot tradingbot_dev > {backup_dir}/database_backup.sql",
            "Database backup",
            critical=False
        )
        
        # Backup volumes
        self.run_command(
            f"docker run --rm -v tradingbot_postgres_data:/data -v {backup_dir}:/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .",
            "PostgreSQL data backup",
            critical=False
        )
        
        self.run_command(
            f"docker run --rm -v tradingbot_redis_data:/data -v {backup_dir}:/backup alpine tar czf /backup/redis_data.tar.gz -C /data .",
            "Redis data backup",
            critical=False
        )
        
        self.log(f"✅ Backup created at {backup_dir}")
        return backup_dir
    
    def build_images(self):
        """Build Docker images"""
        self.log("Building Docker images...")
        
        # Build production image
        self.run_command(
            "docker-compose build --no-cache tradingbot",
            "Building main application image"
        )
        
        # Build other services if needed
        self.run_command(
            "docker-compose pull postgres redis nginx",
            "Pulling base images"
        )
        
        self.log("✅ Docker images built successfully")
    
    def deploy_services(self, environment="production"):
        """Deploy services"""
        self.log(f"Deploying services for {environment} environment...")
        
        # Stop existing services
        self.run_command(
            "docker-compose down",
            "Stopping existing services",
            critical=False
        )
        
        # Start database and cache first
        self.run_command(
            "docker-compose up -d postgres redis",
            "Starting database and cache services"
        )
        
        # Wait for services to be ready
        self.log("Waiting for database and cache to be ready...")
        time.sleep(10)
        
        # Run database migrations
        self.run_command(
            "docker-compose run --rm tradingbot python -c 'from backend.database import db; db.create_all()'",
            "Running database migrations",
            critical=False
        )
        
        # Start main application
        self.run_command(
            "docker-compose up -d tradingbot",
            "Starting main application"
        )
        
        # Start additional services based on environment
        if environment == "production":
            self.run_command(
                "docker-compose --profile production up -d nginx",
                "Starting reverse proxy"
            )
            
            self.run_command(
                "docker-compose --profile monitoring up -d prometheus grafana",
                "Starting monitoring services"
            )
        
        self.log("✅ Services deployed successfully")
    
    def run_health_checks(self):
        """Run post-deployment health checks"""
        self.log("Running health checks...")
        
        # Wait for application to start
        self.log("Waiting for application to start...")
        time.sleep(15)
        
        # Check if containers are running
        result = subprocess.run(
            "docker-compose ps --services --filter status=running",
            shell=True,
            capture_output=True,
            text=True
        )
        
        running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
        expected_services = ['tradingbot', 'postgres', 'redis']
        
        for service in expected_services:
            if service in running_services:
                self.log(f"✅ {service} is running")
            else:
                self.log(f"❌ {service} is not running", "ERROR")
        
        # Check application health endpoint
        try:
            import requests
            response = requests.get('http://localhost:5000/health', timeout=10)
            if response.status_code == 200:
                self.log("✅ Application health check passed")
            else:
                self.log(f"❌ Application health check failed: {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"❌ Application health check failed: {str(e)}", "ERROR")
        
        self.log("✅ Health checks completed")
    
    def setup_monitoring(self):
        """Setup monitoring and alerting"""
        self.log("Setting up monitoring...")
        
        # Create monitoring configuration
        monitoring_dir = self.project_root / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        # Grafana dashboard configuration
        grafana_dashboards_dir = monitoring_dir / "grafana" / "dashboards"
        grafana_dashboards_dir.mkdir(parents=True, exist_ok=True)
        
        dashboard_config = {
            "dashboard": {
                "title": "TradingBot Pro Dashboard",
                "panels": [
                    {
                        "title": "Active Bots",
                        "type": "stat",
                        "targets": [{"expr": "tradingbot_active_bots_total"}]
                    },
                    {
                        "title": "Total Trades",
                        "type": "stat",
                        "targets": [{"expr": "tradingbot_trades_total"}]
                    },
                    {
                        "title": "Portfolio Value",
                        "type": "graph",
                        "targets": [{"expr": "tradingbot_portfolio_value"}]
                    }
                ]
            }
        }
        
        with open(grafana_dashboards_dir / "tradingbot.json", 'w') as f:
            json.dump(dashboard_config, f, indent=2)
        
        self.log("✅ Monitoring setup completed")
    
    def setup_ssl(self):
        """Setup SSL certificates"""
        self.log("Setting up SSL certificates...")
        
        ssl_dir = self.project_root / "nginx" / "ssl"
        ssl_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if SSL certificates exist
        cert_file = ssl_dir / "cert.pem"
        key_file = ssl_dir / "key.pem"
        
        if not cert_file.exists() or not key_file.exists():
            self.log("⚠️  SSL certificates not found. Generating self-signed certificates...", "WARNING")
            
            # Generate self-signed certificate for development
            self.run_command(
                f"openssl req -x509 -newkey rsa:4096 -keyout {key_file} -out {cert_file} -days 365 -nodes -subj '/CN=localhost'",
                "Generating self-signed SSL certificate",
                critical=False
            )
        else:
            self.log("✅ SSL certificates found")
    
    def create_nginx_config(self):
        """Create Nginx configuration"""
        nginx_dir = self.project_root / "nginx"
        nginx_dir.mkdir(exist_ok=True)
        
        nginx_config = """
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    upstream tradingbot_backend {
        server tradingbot:5000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name localhost;
        
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
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://tradingbot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # WebSocket connections
        location /socket.io/ {
            proxy_pass http://tradingbot_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static files
        location / {
            proxy_pass http://tradingbot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""
        
        with open(nginx_dir / "nginx.conf", 'w') as f:
            f.write(nginx_config)
        
        self.log("✅ Nginx configuration created")
    
    def save_deployment_log(self):
        """Save deployment log to file"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        with open(log_file, 'w') as f:
            f.write('\n'.join(self.deployment_log))
        
        self.log(f"Deployment log saved to {log_file}")
    
    def deploy_full(self, environment="production"):
        """Full deployment process"""
        self.log(f"Starting full deployment for {environment} environment")
        
        try:
            # Pre-deployment checks
            if not self.check_prerequisites():
                return False
            
            # Backup existing deployment
            self.backup_existing_deployment()
            
            # Setup configurations
            self.create_nginx_config()
            self.setup_ssl()
            self.setup_monitoring()
            
            # Build and deploy
            self.build_images()
            self.deploy_services(environment)
            
            # Post-deployment checks
            self.run_health_checks()
            
            self.log("🎉 Deployment completed successfully!")
            
            # Print access information
            print("\n" + "="*60)
            print("DEPLOYMENT COMPLETE")
            print("="*60)
            print("Application URLs:")
            print("  - Main App: https://localhost")
            print("  - API Docs: https://localhost/docs")
            print("  - Grafana: http://localhost:3000 (admin/admin123)")
            print("  - pgAdmin: http://localhost:8080 (admin@tradingbot.com/admin123)")
            print("\nNext Steps:")
            print("1. Update DNS records to point to your server")
            print("2. Replace self-signed SSL certificates with valid ones")
            print("3. Configure monitoring alerts")
            print("4. Set up automated backups")
            print("5. Review security settings")
            
            return True
            
        except Exception as e:
            self.log(f"Deployment failed: {str(e)}", "ERROR")
            return False
        
        finally:
            self.save_deployment_log()
    
    def rollback(self, backup_dir):
        """Rollback to previous deployment"""
        self.log(f"Rolling back to backup: {backup_dir}")
        
        # Stop current services
        self.run_command(
            "docker-compose down",
            "Stopping current services"
        )
        
        # Restore database backup
        if (Path(backup_dir) / "database_backup.sql").exists():
            self.run_command(
                f"docker-compose up -d postgres && sleep 10 && docker-compose exec -T postgres psql -U tradingbot -d tradingbot_dev < {backup_dir}/database_backup.sql",
                "Restoring database backup"
            )
        
        # Restart services
        self.run_command(
            "docker-compose up -d",
            "Restarting services"
        )
        
        self.log("✅ Rollback completed")

def main():
    parser = argparse.ArgumentParser(description='TradingBot Pro Deployment Script')
    parser.add_argument('command', choices=['deploy', 'rollback', 'health-check', 'backup'],
                       help='Deployment command')
    parser.add_argument('--environment', choices=['development', 'staging', 'production'],
                       default='production', help='Target environment')
    parser.add_argument('--backup-dir', help='Backup directory for rollback')
    
    args = parser.parse_args()
    deployer = TradingBotDeployer()
    
    if args.command == 'deploy':
        success = deployer.deploy_full(args.environment)
        sys.exit(0 if success else 1)
    
    elif args.command == 'rollback':
        if not args.backup_dir:
            print("❌ --backup-dir is required for rollback")
            sys.exit(1)
        deployer.rollback(args.backup_dir)
    
    elif args.command == 'health-check':
        deployer.run_health_checks()
    
    elif args.command == 'backup':
        deployer.backup_existing_deployment()

if __name__ == '__main__':
    main()