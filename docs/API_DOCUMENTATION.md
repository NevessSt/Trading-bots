# 📚 Trading Bot Platform API Documentation

## Overview

The Trading Bot Platform provides a comprehensive REST API for managing trading bots, user accounts, subscriptions, and trading operations. This API is built with Flask and uses JWT authentication for secure access.

**Base URL:** `http://localhost:5000/api`

## Authentication

All API endpoints (except registration and login) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

- **General API:** 60 requests per minute
- **Authentication endpoints:** 5 requests per minute
- **Trading operations:** 10 requests per minute

## Response Format

All API responses follow this standard format:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Authentication Endpoints

### Register User

**POST** `/api/v2/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully. Please verify your email.",
  "user_id": "uuid-string"
}
```

### Login

**POST** `/api/v2/auth/login`

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "subscription_plan": "free"
  }
}
```

### Refresh Token

**POST** `/api/v2/auth/refresh`

Refresh expired JWT token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "success": true,
  "access_token": "new_jwt_token"
}
```

## User Management

### Get User Profile

**GET** `/api/users/profile`

Retrieve current user's profile information.

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "subscription_plan": "pro",
    "created_at": "2024-01-01T12:00:00Z",
    "email_verified": true,
    "is_active": true
  }
}
```

### Update User Profile

**PUT** `/api/users/profile`

Update user profile information.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "username": "johnsmith"
}
```

### Change Password

**POST** `/api/users/change-password`

Change user password.

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

## Trading Bot Management

### Create Trading Bot

**POST** `/api/trading/bots`

Create a new trading bot.

**Request Body:**
```json
{
  "name": "My BTC Bot",
  "symbol": "BTC/USDT",
  "strategy": "sma_crossover",
  "amount": 100.0,
  "take_profit": 3.0,
  "stop_loss": 2.0,
  "strategy_params": {
    "short_period": 10,
    "long_period": 20
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bot created successfully",
  "bot_id": "bot_uuid"
}
```

### Get All Bots

**GET** `/api/trading/bots`

Retrieve all trading bots for the current user.

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `inactive`, `running`, `stopped`)
- `limit` (optional): Number of results (default: 10)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "bots": [
    {
      "id": "bot_uuid",
      "name": "My BTC Bot",
      "symbol": "BTC/USDT",
      "strategy": "sma_crossover",
      "status": "running",
      "is_active": true,
      "total_trades": 15,
      "winning_trades": 9,
      "total_profit_loss": 125.50,
      "win_rate": 60.0,
      "created_at": "2024-01-01T12:00:00Z",
      "last_run_at": "2024-01-01T15:30:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

### Get Bot Details

**GET** `/api/trading/bots/{bot_id}`

Retrieve detailed information about a specific bot.

**Response:**
```json
{
  "success": true,
  "bot": {
    "id": "bot_uuid",
    "name": "My BTC Bot",
    "description": "SMA crossover strategy for BTC",
    "symbol": "BTC/USDT",
    "strategy": "sma_crossover",
    "timeframe": "1h",
    "base_amount": 100.0,
    "stop_loss_percentage": 2.0,
    "take_profit_percentage": 3.0,
    "max_daily_trades": 5,
    "risk_per_trade": 2.0,
    "is_active": true,
    "is_running": true,
    "is_paper_trading": false,
    "total_trades": 15,
    "winning_trades": 9,
    "total_profit_loss": 125.50,
    "win_rate": 60.0,
    "strategy_config": {
      "short_period": 10,
      "long_period": 20
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T15:30:00Z",
    "last_run_at": "2024-01-01T15:30:00Z"
  }
}
```

### Start Bot

**POST** `/api/trading/bots/{bot_id}/start`

Start a trading bot.

**Response:**
```json
{
  "success": true,
  "message": "Bot started successfully"
}
```

### Stop Bot

**POST** `/api/trading/bots/{bot_id}/stop`

Stop a trading bot.

**Response:**
```json
{
  "success": true,
  "message": "Bot stopped successfully"
}
```

### Update Bot

**PUT** `/api/trading/bots/{bot_id}`

Update bot configuration.

**Request Body:**
```json
{
  "name": "Updated Bot Name",
  "take_profit": 4.0,
  "stop_loss": 1.5,
  "strategy_params": {
    "short_period": 12,
    "long_period": 26
  }
}
```

### Delete Bot

**DELETE** `/api/trading/bots/{bot_id}`

Delete a trading bot.

**Response:**
```json
{
  "success": true,
  "message": "Bot deleted successfully"
}
```

## Trading Operations

### Get Trading Status

**GET** `/api/trading/status`

Get current trading status for the user.

**Response:**
```json
{
  "success": true,
  "active_bots": 3,
  "recent_trades": [
    {
      "id": "trade_uuid",
      "bot_id": "bot_uuid",
      "symbol": "BTC/USDT",
      "type": "buy",
      "amount": 0.001,
      "price": 45000.0,
      "fee": 0.45,
      "profit_loss": 15.0,
      "timestamp": "2024-01-01T15:30:00Z",
      "status": "completed"
    }
  ],
  "balance": {
    "total_balance": 5000.0,
    "available_balance": 4500.0,
    "in_orders": 500.0
  },
  "is_trading_enabled": true
}
```

### Get Trade History

**GET** `/api/trading/trades`

Retrieve trade history for the user.

**Query Parameters:**
- `bot_id` (optional): Filter by specific bot
- `symbol` (optional): Filter by trading pair
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "trades": [
    {
      "id": "trade_uuid",
      "bot_id": "bot_uuid",
      "bot_name": "My BTC Bot",
      "symbol": "BTC/USDT",
      "type": "buy",
      "amount": 0.001,
      "price": 45000.0,
      "quantity": 0.001,
      "fee": 0.45,
      "profit_loss": 15.0,
      "timestamp": "2024-01-01T15:30:00Z",
      "status": "completed",
      "order_id": "exchange_order_id"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0,
  "summary": {
    "total_trades": 100,
    "winning_trades": 65,
    "losing_trades": 35,
    "win_rate": 65.0,
    "total_profit_loss": 1250.0,
    "total_fees": 45.0
  }
}
```

## API Key Management

### Add API Keys

**POST** `/api/keys/add`

Add exchange API keys for trading.

**Request Body:**
```json
{
  "exchange": "binance",
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "testnet": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "API keys for binance added successfully",
  "testnet": true
}
```

### Get API Keys

**GET** `/api/keys`

Retrieve configured API keys (secrets are masked).

**Response:**
```json
{
  "success": true,
  "api_keys": {
    "binance": {
      "api_key": "****key",
      "testnet": true,
      "created_at": "2024-01-01T12:00:00Z",
      "last_used": "2024-01-01T15:30:00Z",
      "is_active": true
    }
  }
}
```

### Test API Keys

**POST** `/api/keys/test/{exchange}`

Test API key connection for a specific exchange.

**Response:**
```json
{
  "success": true,
  "message": "API connection successful",
  "test_results": {
    "balance_check": "OK",
    "symbols_check": "OK",
    "testnet": true,
    "available_symbols_count": 500
  }
}
```

### Delete API Keys

**DELETE** `/api/keys/{exchange}`

Remove API keys for a specific exchange.

**Response:**
```json
{
  "success": true,
  "message": "API keys for binance removed successfully"
}
```

## Subscription Management

### Get Subscription Plans

**GET** `/api/billing/plans`

Retrieve available subscription plans.

**Response:**
```json
{
  "success": true,
  "plans": [
    {
      "id": "free",
      "name": "Free Plan",
      "price": 0,
      "currency": "USD",
      "interval": "month",
      "features": {
        "max_bots": 1,
        "max_strategies": 2,
        "paper_trading_only": true,
        "support": "community"
      }
    },
    {
      "id": "pro",
      "name": "Pro Plan",
      "price": 29.99,
      "currency": "USD",
      "interval": "month",
      "features": {
        "max_bots": 5,
        "max_strategies": 10,
        "live_trading": true,
        "support": "email"
      }
    }
  ]
}
```

### Get Current Subscription

**GET** `/api/billing/subscription`

Retrieve current user's subscription details.

**Response:**
```json
{
  "success": true,
  "subscription": {
    "id": "sub_uuid",
    "plan_id": "pro",
    "plan_name": "Pro Plan",
    "status": "active",
    "current_period_start": "2024-01-01T00:00:00Z",
    "current_period_end": "2024-02-01T00:00:00Z",
    "cancel_at_period_end": false,
    "usage": {
      "bots_used": 3,
      "bots_limit": 5,
      "strategies_used": 5,
      "strategies_limit": 10
    }
  }
}
```

### Create Subscription

**POST** `/api/billing/subscribe`

Subscribe to a plan.

**Request Body:**
```json
{
  "plan_id": "pro",
  "payment_method_id": "pm_stripe_payment_method_id"
}
```

**Response:**
```json
{
  "success": true,
  "subscription_id": "sub_uuid",
  "client_secret": "stripe_client_secret",
  "status": "active"
}
```

## Backtesting

### Run Backtest

**POST** `/api/backtest/run`

Run a backtest for a trading strategy.

**Request Body:**
```json
{
  "strategy": "sma_crossover",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_balance": 10000,
  "strategy_params": {
    "short_period": 10,
    "long_period": 20
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "total_trades": 25,
    "winning_trades": 15,
    "losing_trades": 10,
    "win_rate": 60.0,
    "total_return": 1250.0,
    "total_return_pct": 12.5,
    "max_drawdown": -5.2,
    "sharpe_ratio": 1.45,
    "profit_factor": 1.8,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "initial_balance": 10000,
    "final_balance": 11250
  }
}
```

## Notifications

### Get Notifications

**GET** `/api/notifications`

Retrieve user notifications.

**Query Parameters:**
- `unread_only` (optional): Show only unread notifications
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "notifications": [
    {
      "id": "notif_uuid",
      "type": "trade_executed",
      "title": "Trade Executed",
      "message": "Your bot executed a BUY order for BTC/USDT",
      "is_read": false,
      "created_at": "2024-01-01T15:30:00Z",
      "data": {
        "bot_id": "bot_uuid",
        "trade_id": "trade_uuid"
      }
    }
  ],
  "total": 10,
  "unread_count": 3
}
```

### Mark Notification as Read

**PUT** `/api/notifications/{notification_id}/read`

Mark a notification as read.

**Response:**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Token expired |
| `AUTH_003` | Insufficient permissions |
| `USER_001` | User not found |
| `USER_002` | Email already exists |
| `BOT_001` | Bot not found |
| `BOT_002` | Bot limit exceeded |
| `BOT_003` | Invalid strategy |
| `TRADE_001` | Insufficient balance |
| `TRADE_002` | Invalid trading pair |
| `API_001` | Rate limit exceeded |
| `API_002` | Invalid API keys |
| `SUB_001` | Subscription required |
| `SUB_002` | Payment failed |

## SDKs and Libraries

### Python SDK Example

```python
import requests

class TradingBotAPI:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
    
    def login(self, email, password):
        response = self.session.post(
            f'{self.base_url}/api/v2/auth/login',
            json={'email': email, 'password': password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            return data
        return None
    
    def create_bot(self, name, symbol, strategy, amount):
        return self.session.post(
            f'{self.base_url}/api/trading/bots',
            json={
                'name': name,
                'symbol': symbol,
                'strategy': strategy,
                'amount': amount
            }
        ).json()
    
    def get_bots(self):
        return self.session.get(
            f'{self.base_url}/api/trading/bots'
        ).json()

# Usage
api = TradingBotAPI('http://localhost:5000')
api.login('user@example.com', 'password')
bots = api.get_bots()
```

### JavaScript SDK Example

```javascript
class TradingBotAPI {
    constructor(baseUrl, token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            },
            ...options
        };
        
        const response = await fetch(url, config);
        return response.json();
    }
    
    async login(email, password) {
        const data = await this.request('/api/v2/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (data.success) {
            this.token = data.access_token;
        }
        
        return data;
    }
    
    async createBot(name, symbol, strategy, amount) {
        return this.request('/api/trading/bots', {
            method: 'POST',
            body: JSON.stringify({ name, symbol, strategy, amount })
        });
    }
    
    async getBots() {
        return this.request('/api/trading/bots');
    }
}

// Usage
const api = new TradingBotAPI('http://localhost:5000');
await api.login('user@example.com', 'password');
const bots = await api.getBots();
```

## Webhooks

The platform supports webhooks for real-time notifications:

### Webhook Events

- `bot.started` - Bot started trading
- `bot.stopped` - Bot stopped trading
- `trade.executed` - Trade was executed
- `subscription.updated` - Subscription status changed
- `payment.succeeded` - Payment processed successfully
- `payment.failed` - Payment failed

### Webhook Payload Example

```json
{
  "event": "trade.executed",
  "timestamp": "2024-01-01T15:30:00Z",
  "data": {
    "user_id": "user_uuid",
    "bot_id": "bot_uuid",
    "trade_id": "trade_uuid",
    "symbol": "BTC/USDT",
    "type": "buy",
    "amount": 0.001,
    "price": 45000.0,
    "profit_loss": 15.0
  }
}
```

---

**Last Updated:** January 2024
**API Version:** v2.0
**Support:** For API support, contact support@tradingbot.com