# AI-Powered Crypto Trading Bot

## Project Overview
This is a production-grade AI-powered crypto trading bot designed to analyze market data in real-time, execute profitable trades automatically, and give users full control through a clean, modern dashboard. The bot connects to Binance's trading platform and supports both manual settings and AI-enhanced trading signals, making it suitable for beginners and advanced traders.

## Core Features
- 🔄 **Auto-Trading Engine**: Executes trades based on technical indicators (RSI, MACD, EMA)
- 🔗 **Multi-Exchange Support**: Binance, Coinbase Pro, Kraken, and more via CCXT
- 📊 **Trading Dashboard**: Real-time view of trades, profits, losses, balance, trade history
- 🤖 **AI Signal Module**: Advanced signal generation with multiple strategy support
- ⚠️ **Advanced Risk Management**: Daily loss limits, position exposure, stop-loss/take-profit automation
- 🧑‍💻 **Secure Authentication**: JWT-based auth with rate limiting and security monitoring
- 💬 **Multi-Channel Notifications**: Email, Telegram, and in-app notifications
- 💳 **Monetization Layer**: Stripe integration for subscriptions and premium features
- 🔐 **API Key Management**: Encrypted storage and secure handling of exchange credentials
- 📈 **Backtesting Engine**: Test strategies against historical data before live trading
- 🎯 **Position Monitoring**: Automatic stop-loss and take-profit execution
- 📱 **Real-time Updates**: WebSocket connections for live market data and trade updates

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