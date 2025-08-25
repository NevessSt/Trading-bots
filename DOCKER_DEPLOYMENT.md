# 🐳 Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Trading Bot application using Docker containers for production-ready, scalable deployment.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Service Management](#service-management)
- [Monitoring & Logs](#monitoring--logs)
- [Backup & Restore](#backup--restore)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## 🔧 Prerequisites

### System Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 10GB free space
- **CPU**: 2+ cores recommended
- **Network**: Internet connection for Docker images and API access

### Software Requirements
- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Git** (for cloning the repository)

### Installation Links
- [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/)
- [Docker Desktop for macOS](https://docs.docker.com/desktop/mac/install/)
- [Docker Engine for Linux](https://docs.docker.com/engine/install/)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd trading-bot

# Copy environment template
cp .env.docker .env
```

### 2. Configure Environment
Edit the `.env` file with your settings:
```bash
# Required: Change these values
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password

# Trading API Keys
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret
```

### 3. Deploy

**Windows:**
```cmd
# Run the deployment script
deploy.bat
```

**Linux/macOS:**
```bash
# Make script executable and run
chmod +x deploy.sh
./deploy.sh
```

### 4. Access Your Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs

## ⚙️ Configuration

### Environment Variables

The `.env` file contains all configuration options:

#### Core Application
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DEBUG=false
```

#### Database Configuration
```env
POSTGRES_DB=trading_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-password
```

#### Trading APIs
```env
BINANCE_API_KEY=your-api-key
BINANCE_SECRET_KEY=your-secret-key
```

#### Email Notifications
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

#### Security Settings
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=http://localhost:3000
```

## 🏗️ Deployment Options

### Development Deployment
```bash
# Start with development settings
docker-compose up -d
```

### Production Deployment
```bash
# Start with production profile (includes Nginx)
docker-compose --profile production up -d
```

### Custom Configuration
```bash
# Use custom compose file
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ Service Management

### Using Management Scripts

**Windows:**
```cmd
# Start services
docker-manage.bat start

# Stop services
docker-manage.bat stop

# Restart services
docker-manage.bat restart

# View status
docker-manage.bat status

# Update services
docker-manage.bat update
```

**Linux/macOS:**
```bash
# Make management script executable
chmod +x docker-manage.sh

# Use similar commands
./docker-manage.sh start
./docker-manage.sh status
```

### Manual Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# View running containers
docker-compose ps

# Scale services
docker-compose up -d --scale backend=3
```

## 📊 Monitoring & Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Monitor Resources
```bash
# Real-time stats
docker stats

# Service health
docker-compose ps

# System resource usage
docker system df
```

### Health Checks
All services include health checks:
- **Database**: PostgreSQL connection test
- **Redis**: Redis ping test
- **Backend**: HTTP health endpoint
- **Frontend**: HTTP health endpoint

## 💾 Backup & Restore

### Automated Backup
```bash
# Create backup
docker-manage.bat backup  # Windows
./docker-manage.sh backup   # Linux/macOS
```

Backup includes:
- Database dump
- Application data
- Configuration files
- Log files

### Manual Backup
```bash
# Database backup
docker-compose exec postgres pg_dump -U postgres trading_bot > backup.sql

# Data backup
docker cp trading_bot_backend:/app/data ./backup_data
```

### Restore from Backup
```bash
# Restore using script
docker-manage.bat restore backup_folder  # Windows
./docker-manage.sh restore backup_folder   # Linux/macOS
```

### Manual Restore
```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d postgres
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS trading_bot;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE trading_bot;"
docker-compose exec postgres psql -U postgres trading_bot < backup.sql

# Start all services
docker-compose up -d
```

## 🔒 Security Considerations

### Essential Security Steps

1. **Change Default Passwords**
   ```env
   POSTGRES_PASSWORD=strong-unique-password
   REDIS_PASSWORD=strong-unique-password
   SECRET_KEY=long-random-secret-key
   JWT_SECRET_KEY=long-random-jwt-secret
   ```

2. **Secure API Keys**
   - Store API keys in environment variables
   - Never commit API keys to version control
   - Use encrypted storage for sensitive data

3. **Network Security**
   - Use custom Docker networks
   - Implement rate limiting
   - Configure CORS properly

4. **SSL/TLS Configuration**
   ```bash
   # Generate SSL certificates
   mkdir -p nginx/ssl
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem \
     -out nginx/ssl/cert.pem
   ```

5. **Regular Updates**
   ```bash
   # Update Docker images
   docker-compose pull
   docker-compose up -d
   ```

### Production Security Checklist

- [ ] Changed all default passwords
- [ ] Configured SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Enabled rate limiting
- [ ] Configured secure headers
- [ ] Set up log monitoring
- [ ] Implemented backup strategy
- [ ] Configured intrusion detection

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check compose file syntax
docker-compose config

# View detailed logs
docker-compose logs
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :3000
netstat -tulpn | grep :5000

# Change ports in docker-compose.yml
ports:
  - "3001:3000"  # Frontend
  - "5001:5000"  # Backend
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory
```

#### SSL Certificate Issues
```bash
# Verify certificate
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect localhost:443
```

### Performance Optimization

#### Database Optimization
```sql
-- Connect to database
docker-compose exec postgres psql -U postgres trading_bot

-- Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- Analyze table statistics
ANALYZE;
```

#### Application Optimization
```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## 🌐 Production Deployment

### Cloud Deployment

#### AWS ECS
```bash
# Install AWS CLI and ECS CLI
pip install awscli
ecs-cli configure --region us-west-2 --access-key $AWS_ACCESS_KEY_ID --secret-key $AWS_SECRET_ACCESS_KEY

# Deploy to ECS
ecs-cli compose --file docker-compose.yml up
```

#### Google Cloud Run
```bash
# Build and push images
docker build -t gcr.io/PROJECT_ID/trading-bot-backend ./backend
docker push gcr.io/PROJECT_ID/trading-bot-backend

# Deploy to Cloud Run
gcloud run deploy trading-bot --image gcr.io/PROJECT_ID/trading-bot-backend
```

#### DigitalOcean Droplets
```bash
# Create droplet with Docker
doctl compute droplet create trading-bot \
  --image docker-20-04 \
  --size s-2vcpu-4gb \
  --region nyc1

# Deploy using docker-compose
scp docker-compose.yml root@droplet-ip:/root/
ssh root@droplet-ip 'cd /root && docker-compose up -d'
```

### Load Balancing

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
    # ... other config
  
  nginx:
    depends_on:
      - backend
    # ... load balancer config
```

### Monitoring Stack

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Docker logs: `docker-compose logs`
3. Check system resources: `docker stats`
4. Verify configuration: `docker-compose config`
5. Create an issue with:
   - Error messages
   - System information
   - Docker version
   - Compose file configuration

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
- [Nginx Docker Hub](https://hub.docker.com/_/nginx)

---

**⚠️ Important**: Always test deployments in a staging environment before production use. Ensure all security measures are implemented for production deployments.