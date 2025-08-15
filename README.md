# TradingBot Pro - Professional Cryptocurrency Trading Bot

[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)]()

## 🚀 Overview

TradingBot Pro is a professional-grade cryptocurrency trading bot designed for serious traders and institutions. Built with advanced risk management, portfolio optimization, and multi-exchange support, it provides everything you need for automated cryptocurrency trading.

### ✨ Key Features

- **Multi-Exchange Support**: Binance, Coinbase Pro, Kraken
- **Advanced Strategies**: Grid Trading, DCA, Scalping, RSI, MACD, EMA Crossover
- **Risk Management**: Dynamic position sizing, stop-loss, take-profit, portfolio optimization
- **Real-time Data**: WebSocket streaming, market data caching
- **Backtesting Engine**: Comprehensive strategy testing with optimization
- **Portfolio Management**: Advanced analytics, performance tracking
- **Web Interface**: Modern React-based dashboard
- **API Integration**: RESTful API with comprehensive documentation
- **Monitoring**: Real-time alerts, performance metrics, health checks
- **Security**: Enterprise-grade security with license management

## 📋 Requirements

- Python 3.8 or higher
- Redis server
- PostgreSQL (recommended) or SQLite
- Valid exchange API credentials
- License key (for commercial use)

## 🚀 Features

### Core Trading Features
- **Multiple Trading Strategies**: SMA Crossover, RSI, Bollinger Bands, MACD, and custom strategies
- **Real-time Trading**: Live trading with Binance integration
- **Backtesting Engine**: Historical strategy testing with performance metrics
- **Risk Management**: Stop-loss, take-profit, and position sizing controls
- **Portfolio Management**: Multi-asset portfolio tracking and rebalancing

### Real-time Data & Monitoring
- **WebSocket Streams**: Real-time price feeds from Binance
- **Live Dashboard**: Real-time portfolio and bot performance monitoring
- **Market Data**: Historical OHLCV data and technical indicators
- **Account Balance**: Real-time balance tracking across multiple assets

### Web Interface
- **Modern React Frontend**: Responsive design with Material-UI components
- **Interactive Charts**: Real-time price charts and performance visualization
- **Bot Management**: Create, configure, start/stop trading bots
- **Trade History**: Detailed trade logs with filtering and pagination
- **Performance Analytics**: Profit/loss tracking and strategy analysis

### Infrastructure & Monitoring
- **Docker Containerization**: Easy deployment with Docker Compose
- **Production Monitoring**: Prometheus, Grafana, and ELK stack integration
- **Health Checks**: Automated service monitoring and alerting
- **Security**: JWT authentication, rate limiting, and SSL/TLS encryption
- **Database**: PostgreSQL for data persistence with Redis caching

## 📸 Screenshots

*Screenshots of the trading dashboard, bot management interface, and analytics will be added here. The application features:*

- **Modern React Dashboard**: Real-time portfolio and bot performance monitoring
- **Bot Management Interface**: Create, configure, and manage trading bots
- **Trading Analytics**: Comprehensive trade history and performance metrics
- **Settings Panel**: API key management and configuration options
- **License Management**: Activation and feature access control

## 📋 Prerequisites

- **Docker & Docker Compose**: For containerized deployment
- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **Binance Account**: For live trading (testnet supported)
- **PostgreSQL**: Database (included in Docker setup)
- **Redis**: Caching layer (included in Docker setup)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trading-bot-system
```

### 2. Paper Trading Configuration

**For Development (Testnet/Sandbox)**:
- Set `BINANCE_TESTNET=True` for Binance testnet
- Set `COINBASE_SANDBOX=True` for Coinbase Pro sandbox
- Set `PAPER_TRADING_MODE=True` for simulated trading
- Set `TRADING_ENABLED=False` to disable live trading

**For Live Trading (Production)**:
- Set `BINANCE_TESTNET=False` for live Binance
- Set `COINBASE_SANDBOX=False` for live Coinbase Pro
- Set `PAPER_TRADING_MODE=False` for real trading
- Set `TRADING_ENABLED=True` to enable live trading
- **WARNING**: Only enable live trading with proper risk management!

### 2. Environment Configuration

**IMPORTANT**: Copy `.env.example` to `.env` before running:

```bash
# Copy environment template
cp .env.example .env
cp backend/.env.example backend/.env
```

Then edit `.env` and `backend/.env` with your actual values:

#### Required Environment Variables
```env
# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production-make-it-long-and-random-32chars
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-make-it-long-and-random

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/trading_bot
# Or for development: sqlite:///trading_bot.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Exchange API Credentials (TESTNET/SANDBOX for development)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=True

COINBASE_API_KEY=your_coinbase_api_key_here
COINBASE_SECRET_KEY=your_coinbase_secret_key_here
COINBASE_PASSPHRASE=your_coinbase_passphrase_here
COINBASE_SANDBOX=True

# Trading Configuration
PAPER_TRADING_MODE=True
TRADING_ENABLED=False
BINANCE_TESTNET=true

# Stripe (for subscription management)
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_SECRET_KEY=your_stripe_secret_key

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

## 🚀 Production Deployment

### 1. Environment Setup

Before deploying to production, make sure to set up your environment properly:

```bash
# Copy environment template if you haven't already
cp .env.example .env
```

Edit your `.env` file with production values, making sure to set:

```env
# Security (REQUIRED - use strong, unique values)
SECRET_KEY=your-very-secure-production-secret-key
JWT_SECRET_KEY=your-very-secure-production-jwt-key

# Database credentials
POSTGRES_PASSWORD=your-very-secure-production-db-password
POSTGRES_USER=tradingbot
POSTGRES_DB=tradingbot_prod

# Redis password
REDIS_PASSWORD=your-very-secure-production-redis-password

# Grafana admin credentials
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your-very-secure-production-grafana-password

# pgAdmin credentials
PGADMIN_DEFAULT_EMAIL=admin@yourdomain.com
PGADMIN_DEFAULT_PASSWORD=your-very-secure-production-pgadmin-password

# Set to false for real trading
BINANCE_TESTNET=false
COINBASE_SANDBOX=false
```

### 2. Start Production Environment

Use the production docker-compose configuration:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

This will:
- Build optimized production containers
- Configure proper networking and security
- Set up monitoring and health checks
- Enable SSL/TLS for secure connections

### 3. Verify Deployment

Check that all services are running properly:

```bash
docker compose ps
```

Access the application at:
- Frontend: https://your-domain.com (or http://localhost if testing locally)
- Backend API: https://your-domain.com/api (or http://localhost:5000 if testing locally)
- Monitoring: https://your-domain.com/grafana (or http://localhost:3000 if testing locally)

### 4. Production Maintenance

#### Updating the Application
```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

#### Backing Up Data
```bash
# Backup PostgreSQL database
docker exec tradingbot-postgres pg_dump -U tradingbot tradingbot_prod > backup_$(date +%Y%m%d).sql

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)
```

### 3. License Setup

**⚠️ IMPORTANT: This application requires a valid license to operate.**

#### Quick Start - Trial License
For immediate testing, create a 30-day trial license:

```bash
# Generate trial license for current machine
python create_trial_license.py
```

This will:
- Generate a unique machine ID for your system
- Create a trial license valid for 30 days
- Enable all features for evaluation

#### License Features by Type

| Feature | Trial | Standard | Premium | Enterprise |
|---------|-------|----------|---------|------------|
| Basic Trading | ✅ | ✅ | ✅ | ✅ |
| Advanced Strategies | ✅ | ✅ | ✅ | ✅ |
| Portfolio Management | ✅ | ❌ | ✅ | ✅ |
| Risk Management | ✅ | ✅ | ✅ | ✅ |
| Market Data Access | ✅ | ✅ | ✅ | ✅ |
| API Access | ❌ | ✅ | ✅ | ✅ |
| Multi-Exchange | ❌ | ❌ | ✅ | ✅ |
| Custom Indicators | ❌ | ❌ | ✅ | ✅ |
| White Label | ❌ | ❌ | ❌ | ✅ |

#### Manual License Installation
If you have a license file:

1. Place your `license_key.bin` file in the root directory
2. Ensure the license is bound to your machine ID
3. Start the application

#### License Validation
The application validates licenses on:
- Application startup
- Trading bot creation
- Feature access
- API endpoint access

To check your license status:
- Visit: `http://localhost:5000/license-status`
- Or check logs during application startup

#### Obtaining a License
For production licenses:
1. Generate your machine ID: `python tools/machine_id.py`
2. Contact support with your machine ID
3. Receive your licensed `license_key.bin` file
4. Place the file in the root directory

### 4. Development Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run development server
flask run
```

#### Frontend Setup
```bash
cd frontend
npm install

# Start development server
npm start
```

### 5. Docker Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🚀 Production Deployment

### Prerequisites
- Docker and Docker Compose installed
- Valid SSL certificates (for HTTPS)
- Production environment variables configured
- Exchange API keys (live, not testnet)

### 1. Production Environment Setup

**CRITICAL**: Create production `.env` file with secure values:

```bash
# Copy and customize environment files
cp .env.example .env
cp backend/.env.example backend/.env
```

**Required Production Environment Variables**:
```env
# Security (MUST be changed!)
SECRET_KEY=your-production-secret-key-32-chars-minimum
JWT_SECRET_KEY=your-production-jwt-secret-key-32-chars-minimum

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://username:password@localhost:5432/trading_bot_prod
POSTGRES_PASSWORD=your-secure-postgres-password

# Redis
REDIS_PASSWORD=your-secure-redis-password

# Live Exchange APIs (NOT testnet!)
BINANCE_API_KEY=your_live_binance_api_key
BINANCE_SECRET_KEY=your_live_binance_secret_key
BINANCE_TESTNET=False

COINBASE_API_KEY=your_live_coinbase_api_key
COINBASE_SECRET_KEY=your_live_coinbase_secret_key
COINBASE_PASSPHRASE=your_live_coinbase_passphrase
COINBASE_SANDBOX=False

# Trading Configuration
PAPER_TRADING_MODE=False
TRADING_ENABLED=True
ENVIRONMENT=production
DEBUG=False

# Frontend
REACT_APP_API_URL=https://yourdomain.com
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
```

### 2. Production Deployment Command

```bash
# Deploy with both development and production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check service status
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### 3. Post-Deployment Verification

```bash
# Run health checks
./scripts/health-check.sh

# Check API health
curl -f http://localhost:5000/health

# Verify database connection
docker-compose exec backend python -c "from database import db; print('DB OK' if db else 'DB FAIL')"
```

### 4. Monitoring & Maintenance

Access monitoring dashboards:
- **Application**: http://localhost:3000
- **API Health**: http://localhost:5000/health
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

**Regular Maintenance**:
```bash
# Weekly backup
docker-compose exec postgres pg_dump -U trading_user trading_bot_db > backup_$(date +%Y%m%d).sql

# Update containers
docker-compose pull
docker-compose up -d --build

# Clean up old images
docker system prune -f
```

## 📊 Usage

### Creating a Trading Bot

1. **Access the Web Interface**: Navigate to `http://localhost:3000`
2. **Register/Login**: Create an account or login
3. **Create Bot**: Click "Create New Bot"
4. **Configure Strategy**:
   - Select trading pair (e.g., BTCUSDT)
   - Choose strategy (SMA Crossover, RSI, etc.)
   - Set parameters (timeframe, indicators, etc.)
   - Configure risk management (stop-loss, take-profit)
5. **Backtest**: Test strategy with historical data
6. **Deploy**: Start live trading

### Available Strategies

#### 1. SMA Crossover
- **Description**: Buy when short SMA crosses above long SMA
- **Parameters**: Short period (default: 10), Long period (default: 30)
- **Best for**: Trending markets

#### 2. RSI Strategy
- **Description**: Buy when RSI < 30, sell when RSI > 70
- **Parameters**: RSI period (default: 14), Overbought/Oversold levels
- **Best for**: Range-bound markets

#### 3. Bollinger Bands
- **Description**: Buy at lower band, sell at upper band
- **Parameters**: Period (default: 20), Standard deviations (default: 2)
- **Best for**: Volatile markets

#### 4. MACD Strategy
- **Description**: Trade based on MACD line and signal line crossovers
- **Parameters**: Fast period (12), Slow period (26), Signal period (9)
- **Best for**: Trend identification

### API Endpoints

#### Authentication
```bash
# Register
POST /api/auth/register
{
  "username": "user",
  "email": "user@example.com",
  "password": "password"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password"
}
```

#### Bot Management
```bash
# Create bot
POST /api/bots
{
  "name": "My Bot",
  "symbol": "BTCUSDT",
  "strategy": "sma_crossover",
  "parameters": {
    "short_window": 10,
    "long_window": 30
  },
  "initial_balance": 1000
}

# Start bot
POST /api/bots/{bot_id}/start

# Stop bot
POST /api/bots/{bot_id}/stop

# Get bot status
GET /api/bots/{bot_id}
```

#### Real-time Data
```bash
# Get real-time price
GET /api/realtime/BTCUSDT

# Get all real-time data
GET /api/realtime

# Get market data
GET /api/market-data/BTCUSDT?interval=1h&limit=100

# Get account balance
GET /api/account/balance
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_trading_engine.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test

# Run with coverage
npm test -- --coverage
```

### Live Trading Tests
```bash
# Run live trading tests (testnet)
python tests/live_trading_test.py
```

## 📈 Monitoring & Alerts

### Prometheus Metrics
The system exposes various metrics:
- **Trading Metrics**: Active bots, trades executed, profit/loss
- **System Metrics**: API response times, error rates, resource usage
- **Exchange Metrics**: API call rates, WebSocket connections

### Grafana Dashboards
Pre-configured dashboards include:
- **System Overview**: Service health, resource usage
- **Trading Performance**: Bot performance, trade statistics
- **API Monitoring**: Request rates, response times, errors
- **Infrastructure**: Database, Redis, container metrics

### Alert Rules
Configured alerts for:
- Service downtime
- High error rates
- Resource exhaustion
- Trading anomalies
- Security incidents

## 🔒 Security

### Authentication & Authorization
- **JWT Tokens**: Secure API authentication
- **Role-based Access**: User permissions and restrictions
- **Rate Limiting**: API endpoint protection
- **CORS Configuration**: Cross-origin request security

### Data Protection
- **Encryption**: Sensitive data encryption at rest
- **SSL/TLS**: Encrypted communication
- **Input Validation**: SQL injection and XSS prevention
- **Secret Management**: Environment-based configuration

### API Security
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Input Sanitization**: Validate all user inputs
- **Error Handling**: Secure error messages
- **Audit Logging**: Track all user actions

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm trading-bots_postgres_data
docker-compose up -d
```

#### 2. Binance API Issues
```bash
# Check API credentials
echo $BINANCE_API_KEY
echo $BINANCE_SECRET_KEY

# Test API connection
curl -X GET "https://testnet.binance.vision/api/v3/ping"

# Check API permissions
# Ensure Spot Trading is enabled for your API key
```

#### 3. WebSocket Connection Issues
```bash
# Check WebSocket logs
docker-compose logs backend | grep websocket

# Test WebSocket connection
# Use browser dev tools or wscat to test connections
```

#### 4. Frontend Build Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for dependency conflicts
npm audit
npm audit fix
```

### Log Locations
- **Application Logs**: `docker-compose logs [service]`
- **Nginx Logs**: `/var/log/nginx/` (in container)
- **Database Logs**: PostgreSQL container logs
- **Trading Logs**: `backend/logs/trading.log`
- **Deployment Logs**: `deployment.log`

## 📚 API Documentation

Detailed API documentation is available at:
- **Development**: http://localhost:5000/docs
- **Production**: https://your-domain.com/api/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run tests: `npm test` and `pytest`
5. Commit changes: `git commit -am 'Add new feature'`
6. Push to branch: `git push origin feature/new-feature`
7. Submit a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript/React code
- Write tests for new features
- Update documentation for API changes
- Use semantic commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss and is not suitable for all investors. The authors and contributors are not responsible for any financial losses incurred through the use of this software.

**Risk Warning**:
- Past performance does not guarantee future results
- Automated trading can result in significant losses
- Always test strategies thoroughly before live trading
- Never invest more than you can afford to lose
- Consider consulting with a financial advisor

## 📞 Support

For support and questions:
- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check the wiki
- **Email**: danielmanji38@gmail.com

## 🗺️ Roadmap

### Version 2.0 (Planned)
- [ ] Machine Learning strategies
- [ ] Multi-exchange support
- [ ] Advanced portfolio optimization
- [ ] Mobile app
- [ ] Social trading features
- [ ] Advanced risk management
- [ ] Options and futures trading
- [ ] Algorithmic strategy marketplace

### Version 1.1 (In Progress)
- [x] Real-time WebSocket data
- [x] Production monitoring
- [x] Automated deployment
- [ ] Advanced backtesting
- [ ] Strategy optimization
- [ ] Paper trading mode

---

**Built with ❤️ for the crypto trading community**

## 🌟 Features

### ✅ Complete User System
- **User Registration & Authentication** with JWT tokens
- **Email Verification** for account security
- **Password Reset** functionality
- **Role-based Access Control** (Admin/User)
- **User Profiles** with trading preferences

### 💳 Subscription & Billing
- **Multiple Plans**: Free, Pro, Enterprise
- **Stripe Integration** for secure payments
- **Subscription Management** with automatic renewals
- **Usage Limits** based on subscription tier
- **Billing History** and invoice management

### 🎛️ Frontend Dashboard
- **Modern React UI** with Tailwind CSS
- **Real-time Trading Dashboard** with live updates
- **Strategy Management** - create, edit, and deploy strategies
- **Trade History** with detailed analytics
- **API Key Management** for broker connections
- **Subscription Status** and billing management
- **Admin Panel** for user and system management

### 🛡️ Security & Reliability
- **JWT Authentication** with secure token management
- **API Rate Limiting** to prevent abuse
- **Input Validation** and sanitization
- **Encrypted Storage** for sensitive data (API keys)
- **CORS Protection** and security headers
- **Error Logging** and monitoring

### 📈 Trading Features
- **Multiple Trading Strategies** (SMA, EMA, RSI, MACD)
- **Live Trading Integration** with major exchanges
- **Paper Trading Mode** for testing
- **Risk Management** with stop-loss and take-profit
- **Portfolio Management** and tracking
- **Real-time Market Data** integration

### 🐳 Production-Ready Deployment
- **Docker Containerization** for all services
- **Nginx Reverse Proxy** with SSL support
- **PostgreSQL Database** with Redis caching
- **Environment Configuration** management
- **Health Checks** and monitoring
- **Automated Deployment** scripts

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx         │    │   Backend       │
│   (React)       │◄──►│   (Reverse      │◄──►│   (Flask)       │
│   Port: 3000    │    │   Proxy)        │    │   Port: 5000    │
└─────────────────┘    │   Port: 80/443  │    └─────────────────┘
                       └─────────────────┘             │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis         │    │   PostgreSQL    │    │   External APIs │
│   (Cache)       │◄──►│   (Database)    │    │   (Exchanges)   │
│   Port: 6379    │    │   Port: 5432    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Recent Enhancements

### Security & Authentication
- **Enhanced JWT Authentication**: Secure token-based authentication with refresh tokens
- **Rate Limiting**: Protection against API abuse with configurable limits
- **Encrypted API Key Storage**: Exchange credentials stored with AES encryption
- **Input Validation**: Comprehensive validation for all API endpoints
- **Security Monitoring**: Login attempt tracking and suspicious activity detection

### Trading Engine Improvements
- **Multi-Exchange Support**: Integration with 100+ exchanges via CCXT library
- **Advanced Risk Management**: Daily loss limits, position exposure controls
- **Automated Position Monitoring**: Real-time stop-loss and take-profit execution
- **Enhanced Error Handling**: Robust error recovery and logging
- **Performance Optimization**: Improved trade execution speed and reliability

### Backtesting & Analytics
- **Comprehensive Backtesting Engine**: Test strategies against historical data
- **Strategy Comparison**: Compare multiple strategies side-by-side
- **Performance Metrics**: Detailed analytics including Sharpe ratio, drawdown, win rate
- **Risk Analysis**: Position sizing and exposure analysis
- **Historical Data Integration**: Support for multiple timeframes and symbols

### Notification System
- **Multi-Channel Notifications**: Email, Telegram, and in-app notifications
- **Customizable Alerts**: Configure notification preferences per event type
- **Real-time Delivery**: Instant notifications for trades and system events
- **Notification History**: Track and manage notification history
- **Test Notifications**: Verify notification setup with test messages

### API & Integration
- **RESTful API Design**: Clean, well-documented API endpoints
- **Comprehensive Error Responses**: Detailed error messages and status codes
- **API Documentation**: Complete endpoint documentation with examples
- **Webhook Support**: Real-time event notifications via webhooks
- **Third-party Integrations**: Stripe for payments, Redis for caching

## Tech Stack
- **Frontend**: React.js + Tailwind CSS + Zustand for state management
- **Backend**: Python (Flask) with comprehensive API endpoints
- **Bot Engine**: Python (Pandas, TA-Lib, CCXT for multi-exchange support)
- **Database**: MongoDB (PyMongo) with optimized queries
- **Authentication**: JWT + bcrypt with rate limiting and security features
- **Exchange APIs**: Multi-exchange support via CCXT (Binance, Coinbase Pro, Kraken, etc.)
- **Security**: Encrypted API key storage, input validation, CORS protection
- **Notifications**: SMTP email, Telegram Bot API, in-app notifications
- **Caching**: Redis for session management and rate limiting
- **Logging**: Structured logging with rotation and error tracking
- **Testing**: Comprehensive backtesting engine with performance metrics
- **Payment System**: Stripe integration for subscription management
- **Hosting/Deployment**: Docker-ready with environment configuration

## Project Structure
```
trading-bot/
├── backend/               # Python Flask backend
│   ├── api/              # API endpoints
│   │   ├── __init__.py   # Package initialization
│   │   ├── admin_routes.py # Admin management routes
│   │   ├── api_key_routes.py # API key management routes
│   │   ├── auth_routes.py # Authentication routes
│   │   ├── backtest_routes.py # Backtesting routes
│   │   ├── notification_routes.py # Notification management routes
│   │   ├── trading_routes.py # Trading routes
│   │   └── user_routes.py # User management routes
│   ├── auth/             # Authentication logic
│   ├── bot_engine/       # Trading bot core logic
│   │   ├── __init__.py   # Package initialization
│   │   ├── backtester.py # Backtesting engine
│   │   ├── risk_manager.py # Advanced risk management
│   │   ├── trading_engine.py # Enhanced trading engine
│   │   └── strategies/   # Trading strategies
│   │       ├── __init__.py # Package initialization
│   │       ├── base_strategy.py # Base strategy class
│   │       ├── ema_crossover_strategy.py # EMA crossover strategy
│   │       ├── macd_strategy.py # MACD strategy
│   │       ├── rsi_strategy.py # RSI strategy
│   │       └── strategy_factory.py # Strategy factory
│   ├── config/           # Configuration files
│   │   ├── __init__.py   # Package initialization
│   │   └── config.py     # Configuration settings
│   ├── models/           # Database models
│   │   ├── __init__.py   # Package initialization
│   │   ├── bot.py        # Bot model with enhanced features
│   │   ├── trade.py      # Trade model with position tracking
│   │   └── user.py       # User model with security features
│   └── utils/            # Utility functions
│       ├── __init__.py   # Package initialization
│       ├── logger.py     # Enhanced logging system
│       ├── notification.py # Multi-channel notification manager
│       └── security.py   # Security utilities and encryption
├── frontend/             # React.js frontend
│   ├── public/           # Static files
│   │   ├── index.html    # HTML template
│   │   └── manifest.json # Web app manifest
│   └── src/              # React source code
│       ├── components/   # UI components
│       │   ├── Bots/     # Bot components
│       │   │   ├── BotDetail.jsx    # Bot details component
│       │   │   ├── BotForm.jsx      # Bot creation/edit form
│       │   │   ├── BotList.jsx      # List of bots
│       │   │   └── index.js         # Bot components export
│       │   ├── Dashboard/ # Dashboard components
│       │   │   ├── AccountSummary.jsx # Account summary
│       │   │   ├── ActiveBotsList.jsx # Active bots list
│       │   │   ├── Dashboard.jsx    # Main dashboard
│       │   │   ├── PerformanceChart.jsx # Performance chart
│       │   │   ├── RecentTradesList.jsx # Recent trades
│       │   │   └── index.js         # Dashboard components export
│       │   ├── Layout/   # Layout components
│       │   │   ├── Layout.jsx       # Main layout with navigation
│       │   │   └── index.js         # Layout export
│       │   └── Trades/   # Trade components
│       │       ├── TradesList.jsx   # Trades list with filters
│       │       └── index.js         # Trades components export
│       ├── pages/        # Page components
│       │   ├── Login.jsx           # Login page
│       │   ├── NotFound.jsx        # 404 page
│       │   ├── Profile.jsx         # User profile
│       │   ├── Register.jsx        # Registration page
│       │   ├── Settings.jsx        # User settings
│       │   └── index.js            # Pages export
│       ├── services/     # API services
│       │   └── api.js              # API service with axios
│       ├── stores/       # State management
│       │   ├── index.js            # Stores export
│       │   ├── useAuthStore.js     # Authentication store
│       │   └── useTradingStore.js  # Trading data store
│       ├── App.js        # Main application component
│       ├── index.js      # Application entry point
│       ├── index.css     # Global styles
│       └── reportWebVitals.js # Performance monitoring
└── docs/                 # Documentation
```

## Getting Started

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

### Trading
- `GET /api/trading/bots` - List user's trading bots
- `POST /api/trading/bots` - Create new trading bot
- `PUT /api/trading/bots/{bot_id}` - Update trading bot
- `DELETE /api/trading/bots/{bot_id}` - Delete trading bot
- `POST /api/trading/bots/{bot_id}/start` - Start trading bot
- `POST /api/trading/bots/{bot_id}/stop` - Stop trading bot
- `GET /api/trading/trades` - Get trade history
- `GET /api/trading/performance` - Get trading performance metrics

### Backtesting
- `POST /api/backtest/run` - Run single strategy backtest
- `POST /api/backtest/compare` - Compare multiple strategies
- `GET /api/backtest/strategies` - List available strategies
- `GET /api/backtest/symbols` - List available trading symbols
- `GET /api/backtest/timeframes` - List available timeframes

### API Key Management
- `POST /api/keys/add` - Add exchange API key
- `GET /api/keys/list` - List user's API keys
- `DELETE /api/keys/remove/{key_id}` - Remove API key
- `POST /api/keys/test/{key_id}` - Test API key connection
- `PUT /api/keys/toggle/{key_id}` - Enable/disable API key
- `GET /api/keys/exchanges` - List supported exchanges

### Notifications
- `GET /api/notifications` - List user notifications
- `PUT /api/notifications/{notification_id}/read` - Mark notification as read
- `PUT /api/notifications/read-all` - Mark all notifications as read
- `GET /api/notifications/unread-count` - Get unread notification count
- `GET /api/notifications/settings` - Get notification settings
- `PUT /api/notifications/settings` - Update notification settings
- `POST /api/notifications/test` - Send test notification

### User Management
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile
- `PUT /api/users/password` - Change password
- `DELETE /api/users/account` - Delete user account
- `GET /api/users/subscription` - Get subscription status
- `POST /api/users/subscription/upgrade` - Upgrade subscription

### Admin (Admin only)
- `GET /api/admin/users` - List all users
- `GET /api/admin/stats` - Get system statistics
- `PUT /api/admin/users/{user_id}/status` - Update user status
- `GET /api/admin/trades` - Get all trades
- `GET /api/admin/logs` - Get system logs

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB
- Redis (for caching and rate limiting)
- Exchange account with API keys (Binance, Coinbase Pro, etc.)
- SMTP server for email notifications (optional)
- Telegram Bot Token (optional for notifications)

### Installation

#### Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trading-bot.git
   cd trading-bot/backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values including:
   # - MongoDB connection string
   # - Redis URL and password
   # - Exchange API credentials
   # - SMTP settings for email notifications
   # - Telegram bot token
   # - Encryption key for API key storage
   # - JWT secret key
   ```

5. Install and start Redis (required for caching and rate limiting):
   ```bash
   # On Ubuntu/Debian:
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # On macOS:
   brew install redis
   brew services start redis
   
   # On Windows:
   # Download and install Redis from https://redis.io/download
   ```

6. Run the Flask app:
   ```bash
   python app.py
   ```

#### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

4. The application will be available at `http://localhost:3000`

## License
This project is proprietary and confidential.

## Contact
For any inquiries, please contact the project maintainers.
## Email for help
danielmanji38@gmail.com
