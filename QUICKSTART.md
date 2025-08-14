# TradingBot Pro - Quick Start Guide

🚀 **Get your trading bot up and running in minutes!**

## Prerequisites

- Python 3.8+ installed
- Docker and Docker Compose (for containerized deployment)
- Git (for version control)
- 4GB+ RAM recommended
- Stable internet connection

## 🎯 Option 1: Quick Development Setup (Recommended for beginners)

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd trading-bots

# Run automated setup
python setup.py dev
```

### Step 2: Configure Environment
```bash
# Edit the .env file with your API keys
notepad .env  # Windows
# or
nano .env    # Linux/Mac
```

**Required configurations:**
- `BINANCE_API_KEY` and `BINANCE_SECRET_KEY`
- `DATABASE_URL` (SQLite is pre-configured)
- `REDIS_URL` (optional for development)

### Step 3: Start the Application
```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Start the application
python main.py
```

### Step 4: Access the Application
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **Admin Panel**: http://localhost:5000/admin

---

## 🐳 Option 2: Docker Deployment (Recommended for production)

### Step 1: Setup Docker Environment
```bash
# Run Docker setup
python setup.py docker

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Step 2: Deploy with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f tradingbot
```

### Step 3: Access Services
- **Main Application**: http://localhost:5000
- **Database Admin**: http://localhost:8080 (pgAdmin)
- **Monitoring**: http://localhost:3000 (Grafana)
- **Metrics**: http://localhost:9090 (Prometheus)

---

## 🔧 Configuration Guide

### Exchange API Setup

#### Binance
1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create new API key
3. Enable "Enable Trading" and "Enable Futures"
4. Add your IP address to restrictions
5. Copy API Key and Secret to `.env`

#### Coinbase Pro
1. Go to [Coinbase Pro API](https://pro.coinbase.com/profile/api)
2. Create new API key with trading permissions
3. Copy credentials to `.env`

### Database Configuration

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///data/trading_bot.db
```

#### PostgreSQL (Production)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/tradingbot
```

### Security Settings
```env
# Generate secure keys
SECRET_KEY=your-super-secret-key-32-chars-long
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-long
ENCRYPTION_KEY=your-encryption-key-32-chars-long
```

---

## 🤖 Your First Trading Bot

### Using Web Interface
1. Open http://localhost:5000
2. Register/Login
3. Go to "Bots" section
4. Click "Create New Bot"
5. Configure:
   - **Strategy**: RSI Strategy
   - **Symbol**: BTC/USDT
   - **Timeframe**: 1h
   - **Investment**: $100
6. Click "Start Bot"

### Using CLI
```bash
# Start a bot via command line
python cli.py start-bot --strategy rsi --symbol BTCUSDT --amount 100

# List active bots
python cli.py list-bots

# Stop a bot
python cli.py stop-bot --bot-id <bot-id>
```

### Using API
```python
import requests

# Start a bot via API
response = requests.post('http://localhost:5000/api/bots/start', json={
    'strategy': 'rsi',
    'symbol': 'BTCUSDT',
    'timeframe': '1h',
    'amount': 100,
    'parameters': {
        'rsi_period': 14,
        'oversold': 30,
        'overbought': 70
    }
})

print(response.json())
```

---

## 📊 Available Strategies

### 1. RSI Strategy
- **Best for**: Sideways markets
- **Parameters**: RSI period, oversold/overbought levels
- **Risk**: Medium

### 2. MACD Strategy
- **Best for**: Trending markets
- **Parameters**: Fast/slow periods, signal period
- **Risk**: Medium

### 3. EMA Crossover
- **Best for**: Strong trends
- **Parameters**: Fast/slow EMA periods
- **Risk**: Low-Medium

### 4. Grid Trading (Advanced)
- **Best for**: Range-bound markets
- **Parameters**: Grid size, number of levels
- **Risk**: High

### 5. DCA (Dollar Cost Averaging)
- **Best for**: Long-term accumulation
- **Parameters**: Interval, amount per buy
- **Risk**: Low

### 6. Scalping (Advanced)
- **Best for**: High-frequency trading
- **Parameters**: Profit target, stop loss
- **Risk**: Very High

---

## 🔍 Monitoring & Management

### Web Dashboard
- Real-time bot performance
- Portfolio overview
- Trade history
- Risk metrics

### Monitoring Tools
- **Grafana**: Visual dashboards
- **Prometheus**: Metrics collection
- **Logs**: Detailed application logs

### Alerts & Notifications
- Email notifications
- Slack integration
- Telegram bot
- SMS alerts (Twilio)

---

## 🧪 Testing & Backtesting

### Run Backtests
```bash
# Backtest a strategy
python cli.py backtest --strategy rsi --symbol BTCUSDT --start 2023-01-01 --end 2023-12-31

# Optimize parameters
python cli.py optimize --strategy rsi --symbol BTCUSDT
```

### Paper Trading
```bash
# Enable paper trading mode
export PAPER_TRADING=True
python main.py
```

### Run Tests
```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
```

---

## 🚀 Production Deployment

### Automated Deployment
```bash
# Deploy to production
python deploy.py deploy --environment production

# Health check
python deploy.py health-check

# Backup
python deploy.py backup
```

### Manual Deployment Steps
1. **Server Setup**: Ubuntu 20.04+ with Docker
2. **Domain & SSL**: Configure domain and SSL certificates
3. **Environment**: Set production environment variables
4. **Database**: Set up PostgreSQL with backups
5. **Monitoring**: Configure alerts and monitoring
6. **Security**: Firewall, fail2ban, security updates

---

## 🛠️ Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Reinstall requirements
pip install -r requirements.txt
```

#### Database connection errors
```bash
# Check database status
docker-compose ps postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### API connection errors
- Check API keys in `.env`
- Verify IP whitelist on exchange
- Check internet connection
- Verify exchange is not in maintenance

#### Bot not starting
- Check logs: `docker-compose logs tradingbot`
- Verify sufficient balance
- Check symbol format (e.g., BTCUSDT not BTC/USDT)

### Getting Help

1. **Check Logs**:
   ```bash
   # Application logs
   tail -f logs/app.log
   
   # Docker logs
   docker-compose logs -f
   ```

2. **Debug Mode**:
   ```bash
   export DEBUG=True
   python main.py
   ```

3. **Health Check**:
   ```bash
   curl http://localhost:5000/health
   ```

---

## 📚 Next Steps

### Learn More
- Read the full [README.md](README.md)
- Check [API Documentation](http://localhost:5000/docs)
- Review [Configuration Guide](config.py)

### Advanced Features
- Custom strategy development
- Portfolio optimization
- Risk management rules
- Multi-exchange arbitrage
- Machine learning integration

### Community
- Join our Discord server
- Follow on Twitter
- Contribute on GitHub
- Read the blog

---

## ⚠️ Important Disclaimers

1. **Financial Risk**: Trading cryptocurrencies involves substantial risk of loss
2. **No Guarantees**: Past performance does not guarantee future results
3. **Start Small**: Begin with small amounts and paper trading
4. **Education**: Learn about trading strategies and risk management
5. **Compliance**: Ensure compliance with local regulations

---

## 🎉 You're Ready!

Congratulations! You now have a fully functional trading bot. Start with paper trading, learn the strategies, and gradually increase your involvement as you gain experience.

**Happy Trading! 🚀📈**

---

*For detailed documentation, visit the [full README](README.md) or check the [API docs](http://localhost:5000/docs).*