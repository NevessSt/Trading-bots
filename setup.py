#!/usr/bin/env python3
"""
TradingBot Pro - Setup and Installation Script
Automated setup for development and production environments
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path
import secrets
import string

class TradingBotSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.env_file = self.project_root / ".env"
        
    def generate_secret_key(self, length=32):
        """Generate a secure random secret key"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            sys.exit(1)
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    def check_dependencies(self):
        """Check if required system dependencies are available"""
        dependencies = ['git', 'docker', 'docker-compose']
        missing = []
        
        for dep in dependencies:
            if not shutil.which(dep):
                missing.append(dep)
        
        if missing:
            print(f"❌ Missing dependencies: {', '.join(missing)}")
            print("Please install the missing dependencies and try again.")
            return False
        
        print("✅ All system dependencies found")
        return True
    
    def create_virtual_environment(self):
        """Create Python virtual environment"""
        if self.venv_path.exists():
            print("✅ Virtual environment already exists")
            return
        
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
        print("✅ Virtual environment created")
    
    def install_requirements(self):
        """Install Python requirements"""
        print("📦 Installing Python requirements...")
        
        # Determine pip executable path
        if os.name == 'nt':  # Windows
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:  # Unix-like
            pip_path = self.venv_path / "bin" / "pip"
        
        # Upgrade pip first
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
            print("✅ Requirements installed")
        else:
            print("❌ requirements.txt not found")
    
    def create_env_file(self):
        """Create .env file from template"""
        if self.env_file.exists():
            print("✅ .env file already exists")
            return
        
        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            print("❌ .env.example not found")
            return
        
        print("🔧 Creating .env file...")
        
        # Read template
        with open(env_example, 'r') as f:
            content = f.read()
        
        # Replace placeholders with generated values
        replacements = {
            'your-super-secret-key-change-in-production': self.generate_secret_key(),
            'your-jwt-secret-key-change-in-production': self.generate_secret_key(),
            'your-encryption-key-32-chars-long': self.generate_secret_key(32),
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        # Write .env file
        with open(self.env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created with secure random keys")
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'logs',
            'data',
            'backups',
            'database',
            'redis',
            'nginx',
            'monitoring/grafana/dashboards',
            'monitoring/grafana/datasources',
            'frontend/public',
            'frontend/src'
        ]
        
        print("📁 Creating project directories...")
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ Project directories created")
    
    def create_config_files(self):
        """Create additional configuration files"""
        # Create database init script
        db_init_path = self.project_root / "database" / "init.sql"
        if not db_init_path.exists():
            with open(db_init_path, 'w') as f:
                f.write("""
-- TradingBot Pro Database Initialization
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create additional databases for testing
CREATE DATABASE tradingbot_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE tradingbot_dev TO tradingbot;
GRANT ALL PRIVILEGES ON DATABASE tradingbot_test TO tradingbot;

-- Create indexes for better performance
-- These will be created by SQLAlchemy migrations, but we can prepare the database
""")
        
        # Create Redis config
        redis_config_path = self.project_root / "redis" / "redis.conf"
        if not redis_config_path.exists():
            with open(redis_config_path, 'w') as f:
                f.write("""
# Redis configuration for TradingBot Pro
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
""")
        
        # Create Prometheus config
        prometheus_config_path = self.project_root / "monitoring" / "prometheus.yml"
        if not prometheus_config_path.exists():
            with open(prometheus_config_path, 'w') as f:
                f.write("""
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tradingbot'
    static_configs:
      - targets: ['tradingbot:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
""")
        
        print("✅ Configuration files created")
    
    def setup_development(self):
        """Setup development environment"""
        print("🚀 Setting up development environment...")
        
        self.check_python_version()
        self.create_virtual_environment()
        self.install_requirements()
        self.create_env_file()
        self.create_directories()
        self.create_config_files()
        
        print("\n✅ Development environment setup complete!")
        print("\nNext steps:")
        print("1. Activate virtual environment:")
        if os.name == 'nt':
            print("   .\\venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Configure your .env file with API keys")
        print("3. Run: python main.py")
    
    def setup_docker(self):
        """Setup Docker environment"""
        print("🐳 Setting up Docker environment...")
        
        if not self.check_dependencies():
            return
        
        self.create_env_file()
        self.create_directories()
        self.create_config_files()
        
        print("\n✅ Docker environment setup complete!")
        print("\nNext steps:")
        print("1. Configure your .env file with API keys")
        print("2. Run: docker-compose up -d")
        print("3. Access the application at http://localhost:5000")
    
    def setup_production(self):
        """Setup production environment"""
        print("🏭 Setting up production environment...")
        
        if not self.check_dependencies():
            return
        
        self.create_env_file()
        self.create_directories()
        self.create_config_files()
        
        # Additional production setup
        print("⚠️  Production setup requires additional configuration:")
        print("1. Update .env file with production values")
        print("2. Configure SSL certificates in nginx/ssl/")
        print("3. Set up proper database backups")
        print("4. Configure monitoring and alerting")
        print("5. Set up log rotation")
        
        print("\n✅ Production environment prepared!")
    
    def clean(self):
        """Clean up generated files and directories"""
        print("🧹 Cleaning up...")
        
        items_to_remove = [
            self.venv_path,
            self.env_file,
            self.project_root / "logs",
            self.project_root / "data",
            self.project_root / "__pycache__",
        ]
        
        for item in items_to_remove:
            if item.exists():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                print(f"Removed: {item}")
        
        print("✅ Cleanup complete")

def main():
    parser = argparse.ArgumentParser(description='TradingBot Pro Setup Script')
    parser.add_argument('command', choices=['dev', 'docker', 'production', 'clean'],
                       help='Setup command to run')
    
    args = parser.parse_args()
    setup = TradingBotSetup()
    
    if args.command == 'dev':
        setup.setup_development()
    elif args.command == 'docker':
        setup.setup_docker()
    elif args.command == 'production':
        setup.setup_production()
    elif args.command == 'clean':
        setup.clean()

if __name__ == '__main__':
    main()