# AI-Powered Crypto Trading Bot

## Project Overview
This is a production-grade AI-powered crypto trading bot designed to analyze market data in real-time, execute profitable trades automatically, and give users full control through a clean, modern dashboard. The bot connects to Binance's trading platform and supports both manual settings and AI-enhanced trading signals, making it suitable for beginners and advanced traders.

## Core Features
- 🔄 **Auto-Trading Engine**: Executes trades based on technical indicators (RSI, MACD, EMA)
- 🔗 **Binance Integration**: Uses official Binance Spot API (and later Futures) for live trading
- 📊 **Trading Dashboard**: View trades, profits, losses, balance, trade history
- 🤖 **AI Signal Module** (v2): Optional GPT/LLM layer that analyzes news or trend data
- ⚠️ **Risk Management**: Max loss per day, stop-loss, take-profit, trade size limits
- 🧑‍💻 **User Authentication**: Login system using JWT for secure access
- 💬 **Notifications**: Telegram or email alerts for each trade
- 💳 **Monetization Layer**: Stripe or Paystack for subscriptions or access sales

## Tech Stack
- **Frontend**: React.js + Tailwind CSS
- **Backend**: Python (Flask)
- **Bot Engine**: Python (Pandas, TA-Lib, ccxt for Binance)
- **Database**: MongoDB (PyMongo)
- **Authentication**: JWT + bcrypt
- **Exchange API**: Binance Spot (REST and WebSocket)
- **Hosting/Deployment**: Railway, Render, or DigitalOcean
- **Monitoring & Logs**: MongoDB + custom trade logs
- **Payment System**: Stripe or Paystack (for SaaS model)

## Project Structure
```
trading-bot/
├── backend/               # Python Flask backend
│   ├── api/              # API endpoints
│   │   ├── __init__.py   # Package initialization
│   │   ├── auth_routes.py # Authentication routes
│   │   └── trading_routes.py # Trading routes
│   ├── auth/             # Authentication logic
│   ├── bot_engine/       # Trading bot core logic
│   │   ├── __init__.py   # Package initialization
│   │   ├── risk_manager.py # Risk management
│   │   ├── trading_engine.py # Trading engine
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
│   │   ├── trade.py      # Trade model
│   │   └── user.py       # User model
│   └── utils/            # Utility functions
│       ├── __init__.py   # Package initialization
│       └── notification.py # Notification manager
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

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB
- Binance API keys

### Installation

#### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file based on `.env.example` and fill in your configuration details.

6. Start the backend server:
   ```
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