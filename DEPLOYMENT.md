# Trading Bot Platform - Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Minimum 4GB RAM** and **10GB free disk space**
- **Windows PowerShell 5.1+** or **Bash** (Linux/Mac)

### One-Command Deployment

**Windows (PowerShell):**
```powershell
.\start-production.ps1 -Build -Monitor
```

**Linux/Mac (Bash):**
```bash
./deploy.sh deploy
```

## 📋 Detailed Setup Instructions

### Step 1: Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp .env.production .env
   ```

2. **Edit `.env` file with your actual values:**
   ```bash
   # Database Configuration
   POSTGRES_PASSWORD=your_secure_database_password
   REDIS_PASSWORD=your_secure_redis_password
   
   # Security Keys (Generate strong random keys)
   SECRET_KEY=your_flask_secret_key_here
   JWT_SECRET_KEY=your_jwt_secret_key_here
   
   # Exchange API Keys
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_SECRET_KEY=your_binance_secret_key
   
   # Email Configuration (for notifications)
   MAIL_SERVER=smtp.gmail.com
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```

### Step 2: SSL Configuration (Optional but Recommended)

1. **Generate SSL certificates:**
   ```bash
   mkdir -p nginx/ssl
   # Place your SSL certificate files:
   # nginx/ssl/cert.pem
   # nginx/ssl/key.pem
   ```

2. **For development/testing, create self-signed certificates:**
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem \
     -out nginx/ssl/cert.pem
   ```

### Step 3: Deploy the Application

**Option A: Using PowerShell Script (Windows)**
```powershell
# Full deployment with build and monitoring
.\start-production.ps1 -Build -Monitor

# Just start services
.\start-production.ps1

# Build and start without monitoring
.\start-production.ps1 -Build
```

**Option B: Using Bash Script (Linux/Mac)**
```bash
# Full deployment
./deploy.sh deploy

# Deploy without backup
./deploy.sh deploy --skip-backup

# Other commands
./deploy.sh status    # Check service status
./deploy.sh health    # Health check
./deploy.sh logs      # View logs
./deploy.sh restart   # Restart services
./deploy.sh stop      # Stop all services
```

**Option C: Manual Docker Compose**
```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🌐 Access Points

After successful deployment, access your application at:

- **Frontend Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **API Documentation:** http://localhost:5000/docs
- **Database:** localhost:5432
- **Redis Cache:** localhost:6379
- **License Server:** http://localhost:8080

## 🔧 Configuration Management

### Advanced Configuration

The platform supports flexible configuration through YAML files:

1. **Exchange Configuration:**
   ```bash
   cp config/exchanges.yaml.template config/exchanges.yaml
   # Edit with your exchange settings
   ```

2. **Trading Strategies:**
   ```bash
   cp config/strategies.yaml.template config/strategies.yaml
   # Configure your trading strategies
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `FLASK_ENV` | Flask environment | `production` |
| `TRADING_MODE` | Trading mode (live/paper) | `paper` |
| `MAX_POSITION_SIZE` | Maximum position size | `1000` |
| `RISK_LIMIT` | Risk limit percentage | `0.02` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 📊 Monitoring and Maintenance

### Health Checks

```bash
# Check all services
curl http://localhost:5000/health

# Database health
docker exec trading_bot_postgres pg_isready -U postgres

# Redis health
docker exec trading_bot_redis redis-cli ping
```

### Log Management

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# View last 100 lines
docker-compose logs --tail=100
```

### Backup and Recovery

**Automated Backup:**
```bash
# Create backup
./deploy.sh backup

# Backups are stored in ./backups/ directory
```

**Manual Database Backup:**
```bash
# Export database
docker exec trading_bot_postgres pg_dump -U postgres trading_bot > backup.sql

# Restore database
docker exec -i trading_bot_postgres psql -U postgres trading_bot < backup.sql
```

## 🔒 Security Best Practices

### 1. Environment Security
- ✅ Use strong, unique passwords for all services
- ✅ Generate random secret keys (32+ characters)
- ✅ Never commit `.env` files to version control
- ✅ Use SSL/TLS certificates in production
- ✅ Regularly rotate API keys and passwords

### 2. Network Security
- ✅ Use firewall rules to restrict access
- ✅ Consider VPN for remote access
- ✅ Monitor access logs regularly
- ✅ Use reverse proxy (Nginx) for additional security

### 3. API Security
- ✅ Enable API rate limiting
- ✅ Use API key authentication
- ✅ Implement proper CORS policies
- ✅ Monitor API usage and anomalies

## 🚨 Troubleshooting

### Common Issues

**1. Services won't start:**
```bash
# Check Docker daemon
docker info

# Check port conflicts
netstat -tulpn | grep :5000
netstat -tulpn | grep :3000

# Check logs for errors
docker-compose logs
```

**2. Database connection issues:**
```bash
# Check database status
docker exec trading_bot_postgres pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

**3. Frontend not loading:**
```bash
# Check frontend build
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
```

**4. API errors:**
```bash
# Check backend logs
docker-compose logs backend

# Check API health
curl -v http://localhost:5000/health
```

### Performance Optimization

**1. Resource Allocation:**
```yaml
# In docker-compose.yml, add resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

**2. Database Optimization:**
```bash
# Increase shared_buffers for PostgreSQL
# Add to docker-compose.yml postgres command:
command: postgres -c shared_buffers=256MB -c max_connections=200
```

## 📈 Scaling for Production

### Horizontal Scaling

```yaml
# Scale specific services
docker-compose up -d --scale backend=3
```

### Load Balancing

Use the included Nginx configuration for load balancing:

```bash
# Enable production profile with Nginx
docker-compose --profile production up -d
```

### External Database

For production, consider using managed database services:

```bash
# Update .env for external database
DATABASE_URL=postgresql://user:pass@external-db:5432/trading_bot
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Backup current data
./deploy.sh backup

# Deploy updates
./deploy.sh deploy
```

### Scheduled Maintenance

```bash
# Create maintenance script
#!/bin/bash
# maintenance.sh

# Backup data
./deploy.sh backup

# Update application
git pull
docker-compose pull
docker-compose up -d --build

# Health check
./deploy.sh health
```

## 📞 Support

For issues and support:

1. **Check logs:** `docker-compose logs`
2. **Review configuration:** Ensure `.env` file is properly configured
3. **Health checks:** Run `./deploy.sh health`
4. **Documentation:** Review this deployment guide
5. **Community:** Check GitHub issues and discussions

---

## 📝 Quick Reference

### Essential Commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart service
docker-compose restart backend

# Scale service
docker-compose up -d --scale backend=2

# Update and restart
docker-compose pull && docker-compose up -d
```

### File Structure
```
trading-bot/
├── backend/           # Python Flask API
├── frontend/          # React.js Dashboard
├── config/            # Configuration templates
├── nginx/             # Reverse proxy config
├── logs/              # Application logs
├── data/              # Persistent data
├── backups/           # Automated backups
├── docker-compose.yml # Service orchestration
├── .env               # Environment variables
├── deploy.sh          # Linux/Mac deployment
├── deploy.ps1         # Windows deployment
└── start-production.ps1 # Windows startup script
```

This deployment guide ensures your trading bot platform runs reliably in production with proper security, monitoring, and maintenance procedures.