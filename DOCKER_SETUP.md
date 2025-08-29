# 🐳 Docker Setup Guide - One-Command Deployment

This guide will help you deploy the entire Trading Bot system using Docker Compose with a single command.

## 🚀 Quick Start (5 Minutes Setup)

### Prerequisites
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop/))
- Git (to clone the repository)
- 8GB+ RAM recommended

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd trading-bot

# Copy environment file
cp .env.example .env
```

### 2. One-Command Launch
```bash
# Launch everything (Database, Backend, Frontend, License Server)
docker-compose up -d
```

### 3. Access Your Trading Bot
- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:5000/docs
- **License Server**: http://localhost:8080
- **Database**: localhost:5432 (postgres/postgres123)

## 🎯 What Gets Deployed

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | React web dashboard |
| **Backend API** | 5000 | Flask trading engine |
| **License Server** | 8080 | License validation |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Cache & sessions |
| **Nginx** | 80/443 | Reverse proxy (production) |

## 🔧 Configuration Options

### Demo Mode (Default)
Perfect for testing without real API keys:
```bash
# In .env file
DEMO_MODE=true
BINANCE_TESTNET=true
```

### Production Mode
For live trading:
```bash
# In .env file
DEMO_MODE=false
BINANCE_TESTNET=false
BINANCE_API_KEY=your_real_api_key
BINANCE_SECRET_KEY=your_real_secret_key

# Enable production profile
COMPOSE_PROFILES=production
```

### Demo Data Generation
To populate with fake trading data:
```bash
# Enable demo profile
COMPOSE_PROFILES=demo

# Launch with demo data
docker-compose --profile demo up -d
```

## 📋 Common Commands

### Start Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d backend

# Start with demo data
docker-compose --profile demo up -d
```

### Monitor Services
```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Check service status
docker-compose ps
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Update Services
```bash
# Rebuild and restart
docker-compose up -d --build

# Update specific service
docker-compose up -d --build backend
```

## 🔐 License Activation

The system includes a built-in license server for easy activation:

### Automatic Demo License
A demo license is automatically generated on first startup:
- **Duration**: 30 days
- **Features**: All premium features enabled
- **No external dependencies**

### Manual License Activation
```bash
# Generate a new demo license
docker-compose exec license-server python -c "
from license_server import LicenseServer
server = LicenseServer()
key = server.generate_license_key('demo_user', 'premium', 30)
print(f'Demo License Key: {key}')
"
```

### License Management
```bash
# Check license status
curl http://localhost:8080/stats

# Validate a license
curl -X POST http://localhost:8080/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "your-license-key", "machine_id": "demo-machine"}'
```

## 🗄️ Database Management

### Access Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d trading_bot

# View tables
\dt

# Exit
\q
```

### Backup Database
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres trading_bot > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres trading_bot < backup.sql
```

## 🔍 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
netstat -tulpn | grep :3000

# Kill the process or change port in docker-compose.yml
```

**Services Won't Start**
```bash
# Check logs for errors
docker-compose logs backend

# Restart specific service
docker-compose restart backend
```

**Database Connection Issues**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**License Server Issues**
```bash
# Check license server logs
docker-compose logs license-server

# Test license server
curl http://localhost:8080/health
```

### Performance Optimization

**Increase Resources**
```yaml
# In docker-compose.yml, add to services:
backend:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
```

**Enable Production Mode**
```bash
# Use production profile
COMPOSE_PROFILES=production docker-compose up -d
```

## 🔧 Advanced Configuration

### Custom Environment Variables
Edit `.env` file to customize:
```bash
# Database settings
POSTGRES_DB=my_trading_bot
POSTGRES_USER=trader
POSTGRES_PASSWORD=secure_password

# Trading settings
DEFAULT_TRADING_PAIR=ETHUSDT
MAX_CONCURRENT_BOTS=5

# License settings
LICENSE_SERVER_SECRET=my-secret-key
```

### SSL/HTTPS Setup
```bash
# Enable production profile with nginx
COMPOSE_PROFILES=production docker-compose up -d

# Add SSL certificates to nginx/ssl/ directory
```

### Scaling Services
```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale with load balancer
docker-compose --profile production up -d --scale backend=3
```

## 📊 Monitoring

### Health Checks
```bash
# Check all services health
docker-compose ps

# Individual health checks
curl http://localhost:5000/health    # Backend
curl http://localhost:3000/health    # Frontend
curl http://localhost:8080/health    # License Server
```

### Resource Usage
```bash
# Monitor resource usage
docker stats

# View container details
docker-compose top
```

## 🚀 Production Deployment

### Minimum Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB recommended)
- **Storage**: 20GB+ SSD
- **Network**: Stable internet connection

### Production Checklist
- [ ] Change all default passwords in `.env`
- [ ] Use real SSL certificates
- [ ] Enable backup strategy
- [ ] Set up monitoring and alerts
- [ ] Configure firewall rules
- [ ] Use production database (not SQLite)
- [ ] Enable log rotation
- [ ] Set up reverse proxy (nginx)

### Security Best Practices
```bash
# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)

# Restrict network access
# Only expose necessary ports
# Use VPN for admin access
```

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify all services are running: `docker-compose ps`
3. Test connectivity: `curl http://localhost:5000/health`
4. Reset everything: `docker-compose down -v && docker-compose up -d`

## 📝 Next Steps

After successful deployment:
1. **Configure Trading Strategies**: Access the web dashboard
2. **Set Up API Keys**: Add your exchange credentials
3. **Enable Notifications**: Configure email/SMS alerts
4. **Monitor Performance**: Check logs and metrics
5. **Backup Data**: Set up automated backups

---

**🎉 Congratulations!** Your trading bot is now running with Docker!

Access your dashboard at: **http://localhost:3000**