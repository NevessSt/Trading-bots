# 🧪 Trading Bot Platform - Testing Guide

## Table of Contents

1. [Overview](#overview)
2. [Testing Strategy](#testing-strategy)
3. [Test Environment Setup](#test-environment-setup)
4. [Backend Testing](#backend-testing)
5. [Frontend Testing](#frontend-testing)
6. [Integration Testing](#integration-testing)
7. [End-to-End Testing](#end-to-end-testing)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [API Testing](#api-testing)
11. [Database Testing](#database-testing)
12. [Continuous Integration](#continuous-integration)
13. [Test Data Management](#test-data-management)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive testing strategies and procedures for the Trading Bot Platform. Our testing approach ensures reliability, security, and performance across all components.

### Testing Pyramid

```
        /\     E2E Tests (10%)
       /  \    - User workflows
      /    \   - Browser automation
     /______\  - Critical paths
    /        \
   /          \ Integration Tests (20%)
  /            \ - API endpoints
 /              \ - Database operations
/________________\ - Service interactions

     Unit Tests (70%)
     - Individual functions
     - Component logic
     - Business rules
```

### Test Types Coverage

| Test Type | Coverage | Tools | Frequency |
|-----------|----------|-------|----------|
| Unit Tests | 90%+ | pytest, Jest | Every commit |
| Integration Tests | 80%+ | pytest, Supertest | Every PR |
| E2E Tests | Critical paths | Playwright, Cypress | Daily/Release |
| Performance Tests | Key endpoints | Locust, k6 | Weekly |
| Security Tests | All endpoints | OWASP ZAP, Bandit | Weekly |

## Testing Strategy

### Test Categories

#### 1. Functional Testing
- **Unit Tests:** Individual component testing
- **Integration Tests:** Component interaction testing
- **System Tests:** End-to-end workflow testing
- **Acceptance Tests:** Business requirement validation

#### 2. Non-Functional Testing
- **Performance Tests:** Load, stress, and scalability testing
- **Security Tests:** Vulnerability and penetration testing
- **Usability Tests:** User experience validation
- **Compatibility Tests:** Browser and device testing

#### 3. Test Environments
- **Development:** Local testing during development
- **Staging:** Pre-production testing
- **Production:** Monitoring and smoke tests

## Test Environment Setup

### Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
npm install --save-dev cypress playwright @playwright/test
```

### Environment Configuration

#### Test Database Setup

```bash
# Create test database
psql -U postgres -c "CREATE DATABASE tradingbot_test;"
psql -U postgres -c "CREATE USER test_user WITH PASSWORD 'test_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE tradingbot_test TO test_user;"
```

#### Test Environment Variables

```bash
# .env.test
FLASK_ENV=testing
TESTING=true
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/tradingbot_test
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
ENCRYPTION_KEY=test-encryption-key

# Disable external services in tests
MAIL_SUPPRESS_SEND=true
STRIPE_PUBLISHABLE_KEY=pk_test_fake
STRIPE_SECRET_KEY=sk_test_fake

# Test-specific settings
WTF_CSRF_ENABLED=false
BCRYPT_LOG_ROUNDS=4
```

### Docker Test Environment

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres-test:
    image: postgres:14
    environment:
      POSTGRES_DB: tradingbot_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    tmpfs:
      - /data

  backend-test:
    build:
      context: ./backend
      dockerfile: Dockerfile.test
    environment:
      - TESTING=true
      - DATABASE_URL=postgresql://test_user:test_password@postgres-test:5432/tradingbot_test
      - REDIS_URL=redis://redis-test:6379/0
    depends_on:
      - postgres-test
      - redis-test
    volumes:
      - ./backend:/app
      - ./test-results:/app/test-results
```

## Backend Testing

### Unit Tests

#### Test Structure

```
backend/tests/
├── conftest.py              # Test configuration and fixtures
├── unit/
│   ├── test_models.py       # Model tests
│   ├── test_services.py     # Service layer tests
│   ├── test_utils.py        # Utility function tests
│   └── test_validators.py   # Validation tests
├── integration/
│   ├── test_api_routes.py   # API endpoint tests
│   ├── test_database.py     # Database operation tests
│   └── test_external_apis.py # External API integration tests
└── fixtures/
    ├── sample_data.json     # Test data
    └── mock_responses.py    # Mock API responses
```

#### Test Configuration (`conftest.py`)

```python
import pytest
import tempfile
import os
from app import create_app, db
from models.user import User
from models.bot import Bot
from models.subscription import Subscription

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        db.session.begin()
        yield db.session
        db.session.rollback()
        db.session.close()

@pytest.fixture
def sample_user(db_session):
    """Create sample user for testing."""
    user = User(
        email='test@example.com',
        username='testuser',
        password_hash='hashed_password',
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_bot(db_session, sample_user):
    """Create sample bot for testing."""
    bot = Bot(
        name='Test Bot',
        strategy='grid_trading',
        user_id=sample_user.id,
        is_active=True,
        config={'grid_size': 10, 'profit_target': 0.02}
    )
    db_session.add(bot)
    db_session.commit()
    return bot

@pytest.fixture
def auth_headers(sample_user):
    """Create authentication headers."""
    from services.auth_service import AuthService
    token = AuthService.generate_token(sample_user.id)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def mock_exchange_api(monkeypatch):
    """Mock exchange API responses."""
    class MockExchangeAPI:
        def get_ticker(self, symbol):
            return {'price': 50000.0, 'volume': 1000.0}
        
        def place_order(self, symbol, side, amount, price):
            return {
                'id': 'mock_order_123',
                'status': 'filled',
                'filled_amount': amount
            }
    
    monkeypatch.setattr('services.exchange_service.ExchangeAPI', MockExchangeAPI)
    return MockExchangeAPI()
```

#### Model Tests (`test_models.py`)

```python
import pytest
from models.user import User
from models.bot import Bot
from models.trade import Trade
from datetime import datetime, timedelta

class TestUserModel:
    def test_user_creation(self, db_session):
        """Test user model creation."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hashed_password'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.created_at is not None
        assert not user.is_verified
    
    def test_user_password_hashing(self):
        """Test password hashing functionality."""
        user = User(email='test@example.com', username='testuser')
        user.set_password('password123')
        
        assert user.password_hash != 'password123'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')
    
    def test_user_email_validation(self, db_session):
        """Test email validation."""
        with pytest.raises(ValueError):
            user = User(email='invalid-email', username='testuser')
            user.validate_email()
    
    def test_user_subscription_relationship(self, db_session, sample_user):
        """Test user-subscription relationship."""
        from models.subscription import Subscription
        
        subscription = Subscription(
            user_id=sample_user.id,
            plan_type='premium',
            status='active'
        )
        db_session.add(subscription)
        db_session.commit()
        
        assert sample_user.subscription is not None
        assert sample_user.subscription.plan_type == 'premium'

class TestBotModel:
    def test_bot_creation(self, db_session, sample_user):
        """Test bot model creation."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=sample_user.id,
            config={'grid_size': 10}
        )
        db_session.add(bot)
        db_session.commit()
        
        assert bot.id is not None
        assert bot.name == 'Test Bot'
        assert bot.strategy == 'grid_trading'
        assert not bot.is_active
    
    def test_bot_config_validation(self, sample_user):
        """Test bot configuration validation."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=sample_user.id,
            config={'invalid_param': 'value'}
        )
        
        with pytest.raises(ValueError):
            bot.validate_config()
    
    def test_bot_performance_calculation(self, db_session, sample_bot):
        """Test bot performance calculation."""
        # Add some trades
        trade1 = Trade(
            bot_id=sample_bot.id,
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            price=50000,
            profit_loss=100
        )
        trade2 = Trade(
            bot_id=sample_bot.id,
            symbol='BTC/USDT',
            side='sell',
            amount=0.1,
            price=51000,
            profit_loss=200
        )
        
        db_session.add_all([trade1, trade2])
        db_session.commit()
        
        performance = sample_bot.calculate_performance()
        assert performance['total_profit'] == 300
        assert performance['total_trades'] == 2
        assert performance['win_rate'] == 100.0

class TestTradeModel:
    def test_trade_creation(self, db_session, sample_bot):
        """Test trade model creation."""
        trade = Trade(
            bot_id=sample_bot.id,
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            price=50000,
            exchange_order_id='order_123'
        )
        db_session.add(trade)
        db_session.commit()
        
        assert trade.id is not None
        assert trade.symbol == 'BTC/USDT'
        assert trade.total_value == 5000  # 0.1 * 50000
    
    def test_trade_profit_calculation(self, db_session, sample_bot):
        """Test trade profit calculation."""
        buy_trade = Trade(
            bot_id=sample_bot.id,
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            price=50000
        )
        sell_trade = Trade(
            bot_id=sample_bot.id,
            symbol='BTC/USDT',
            side='sell',
            amount=0.1,
            price=51000
        )
        
        profit = sell_trade.calculate_profit(buy_trade)
        assert profit == 100  # (51000 - 50000) * 0.1
```

#### Service Tests (`test_services.py`)

```python
import pytest
from unittest.mock import Mock, patch
from services.trading_service import TradingService
from services.auth_service import AuthService
from services.notification_service import NotificationService

class TestTradingService:
    def test_create_bot(self, db_session, sample_user):
        """Test bot creation service."""
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'grid_trading',
            'config': {'grid_size': 10, 'profit_target': 0.02}
        }
        
        bot = TradingService.create_bot(sample_user.id, bot_data)
        
        assert bot.name == 'Test Bot'
        assert bot.user_id == sample_user.id
        assert not bot.is_active
    
    def test_start_bot(self, db_session, sample_bot, mock_exchange_api):
        """Test bot starting service."""
        result = TradingService.start_bot(sample_bot.id)
        
        assert result['success'] is True
        assert sample_bot.is_active
        assert sample_bot.started_at is not None
    
    def test_stop_bot(self, db_session, sample_bot):
        """Test bot stopping service."""
        # Start bot first
        sample_bot.is_active = True
        db_session.commit()
        
        result = TradingService.stop_bot(sample_bot.id)
        
        assert result['success'] is True
        assert not sample_bot.is_active
        assert sample_bot.stopped_at is not None
    
    @patch('services.trading_service.ExchangeAPI')
    def test_execute_trade(self, mock_exchange, db_session, sample_bot):
        """Test trade execution service."""
        mock_exchange.return_value.place_order.return_value = {
            'id': 'order_123',
            'status': 'filled',
            'filled_amount': 0.1
        }
        
        trade_data = {
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.1,
            'price': 50000
        }
        
        trade = TradingService.execute_trade(sample_bot.id, trade_data)
        
        assert trade.symbol == 'BTC/USDT'
        assert trade.exchange_order_id == 'order_123'
        assert trade.status == 'filled'

class TestAuthService:
    def test_generate_token(self, sample_user):
        """Test JWT token generation."""
        token = AuthService.generate_token(sample_user.id)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_token(self, sample_user):
        """Test JWT token verification."""
        token = AuthService.generate_token(sample_user.id)
        user_id = AuthService.verify_token(token)
        
        assert user_id == sample_user.id
    
    def test_invalid_token(self):
        """Test invalid token handling."""
        with pytest.raises(Exception):
            AuthService.verify_token('invalid_token')
    
    def test_expired_token(self, sample_user):
        """Test expired token handling."""
        with patch('services.auth_service.datetime') as mock_datetime:
            # Generate token
            token = AuthService.generate_token(sample_user.id)
            
            # Mock time to be in the future
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(hours=25)
            
            with pytest.raises(Exception):
                AuthService.verify_token(token)

class TestNotificationService:
    @patch('services.notification_service.send_email')
    def test_send_welcome_email(self, mock_send_email, sample_user):
        """Test welcome email sending."""
        NotificationService.send_welcome_email(sample_user)
        
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert sample_user.email in args
    
    @patch('services.notification_service.send_email')
    def test_send_trade_notification(self, mock_send_email, sample_user, sample_bot):
        """Test trade notification sending."""
        trade_data = {
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.1,
            'price': 50000,
            'profit': 100
        }
        
        NotificationService.send_trade_notification(sample_user, sample_bot, trade_data)
        
        mock_send_email.assert_called_once()
```

#### API Tests (`test_api_routes.py`)

```python
import pytest
import json
from flask import url_for

class TestAuthRoutes:
    def test_register_user(self, client):
        """Test user registration endpoint."""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        response = client.post('/api/v2/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert 'user_id' in response_data
        assert response_data['message'] == 'User registered successfully'
    
    def test_login_user(self, client, sample_user):
        """Test user login endpoint."""
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        # Set password for sample user
        sample_user.set_password('password123')
        
        response = client.post('/api/v2/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'access_token' in response_data
        assert 'user' in response_data
    
    def test_login_invalid_credentials(self, client, sample_user):
        """Test login with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/v2/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert 'error' in response_data

class TestBotRoutes:
    def test_create_bot(self, client, auth_headers):
        """Test bot creation endpoint."""
        data = {
            'name': 'Test Bot',
            'strategy': 'grid_trading',
            'config': {
                'grid_size': 10,
                'profit_target': 0.02,
                'symbol': 'BTC/USDT'
            }
        }
        
        response = client.post('/api/trading/bots',
                             data=json.dumps(data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['name'] == 'Test Bot'
        assert response_data['strategy'] == 'grid_trading'
    
    def test_get_user_bots(self, client, auth_headers, sample_bot):
        """Test getting user bots endpoint."""
        response = client.get('/api/trading/bots',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'bots' in response_data
        assert len(response_data['bots']) >= 1
    
    def test_start_bot(self, client, auth_headers, sample_bot, mock_exchange_api):
        """Test bot start endpoint."""
        response = client.post(f'/api/trading/bots/{sample_bot.id}/start',
                             headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    def test_stop_bot(self, client, auth_headers, sample_bot):
        """Test bot stop endpoint."""
        # Start bot first
        sample_bot.is_active = True
        
        response = client.post(f'/api/trading/bots/{sample_bot.id}/stop',
                             headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    def test_unauthorized_access(self, client, sample_bot):
        """Test unauthorized access to bot endpoints."""
        response = client.get('/api/trading/bots')
        
        assert response.status_code == 401

class TestTradeRoutes:
    def test_get_trade_history(self, client, auth_headers, sample_bot):
        """Test trade history endpoint."""
        response = client.get(f'/api/trading/bots/{sample_bot.id}/trades',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'trades' in response_data
        assert 'pagination' in response_data
    
    def test_get_trade_statistics(self, client, auth_headers, sample_bot):
        """Test trade statistics endpoint."""
        response = client.get(f'/api/trading/bots/{sample_bot.id}/stats',
                            headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'total_trades' in response_data
        assert 'total_profit' in response_data
        assert 'win_rate' in response_data
```

### Running Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestUserModel

# Run specific test method
pytest tests/unit/test_models.py::TestUserModel::test_user_creation

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto

# Run tests with specific markers
pytest -m "not slow"
```

## Frontend Testing

### Test Structure

```
frontend/src/tests/
├── setup.js                 # Test setup and configuration
├── __mocks__/              # Mock files
│   ├── api.js              # API mocks
│   └── localStorage.js     # LocalStorage mock
├── components/             # Component tests
│   ├── Dashboard.test.js
│   ├── BotCard.test.js
│   └── TradeHistory.test.js
├── pages/                  # Page tests
│   ├── Login.test.js
│   ├── Dashboard.test.js
│   └── BotManagement.test.js
├── hooks/                  # Custom hook tests
│   ├── useAuth.test.js
│   └── useBots.test.js
├── utils/                  # Utility tests
│   ├── formatters.test.js
│   └── validators.test.js
└── integration/            # Integration tests
    ├── auth-flow.test.js
    └── bot-management.test.js
```

### Test Setup (`setup.js`)

```javascript
import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { server } from './mocks/server';

// Configure testing library
configure({ testIdAttribute: 'data-testid' });

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() { return null; }
  disconnect() { return null; }
  unobserve() { return null; }
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() { return null; }
  disconnect() { return null; }
  unobserve() { return null; }
};

// Setup MSW
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
```

### Component Tests

#### Dashboard Component Test

```javascript
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../components/Dashboard';
import { AuthProvider } from '../contexts/AuthContext';

// Mock data
const mockUser = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  subscription: { plan_type: 'premium' }
};

const mockBots = [
  {
    id: 1,
    name: 'Test Bot 1',
    strategy: 'grid_trading',
    is_active: true,
    performance: { total_profit: 150.50, win_rate: 75.5 }
  },
  {
    id: 2,
    name: 'Test Bot 2',
    strategy: 'dca',
    is_active: false,
    performance: { total_profit: -25.30, win_rate: 45.2 }
  }
];

// Test wrapper
const TestWrapper = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider value={{ user: mockUser, isAuthenticated: true }}>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    // Mock API calls
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('renders dashboard with user information', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ bots: mockBots })
    });

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByText('Welcome back, testuser!')).toBeInTheDocument();
    expect(screen.getByText('Premium Plan')).toBeInTheDocument();
  });

  test('displays bot statistics correctly', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ bots: mockBots })
    });

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Total bots
      expect(screen.getByText('1')).toBeInTheDocument(); // Active bots
    });
  });

  test('handles bot creation', async () => {
    const user = userEvent.setup();
    
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bots: mockBots })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 3, name: 'New Bot' })
      });

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    const createButton = screen.getByText('Create New Bot');
    await user.click(createButton);

    expect(screen.getByText('Create Trading Bot')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    global.fetch.mockRejectedValueOnce(new Error('API Error'));

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error loading/i)).toBeInTheDocument();
    });
  });
});
```

#### Bot Card Component Test

```javascript
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BotCard from '../components/BotCard';

const mockBot = {
  id: 1,
  name: 'Test Bot',
  strategy: 'grid_trading',
  is_active: true,
  performance: {
    total_profit: 150.50,
    total_trades: 25,
    win_rate: 75.5
  },
  created_at: '2024-01-01T00:00:00Z'
};

const mockProps = {
  bot: mockBot,
  onStart: jest.fn(),
  onStop: jest.fn(),
  onEdit: jest.fn(),
  onDelete: jest.fn()
};

describe('BotCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders bot information correctly', () => {
    render(<BotCard {...mockProps} />);

    expect(screen.getByText('Test Bot')).toBeInTheDocument();
    expect(screen.getByText('Grid Trading')).toBeInTheDocument();
    expect(screen.getByText('$150.50')).toBeInTheDocument();
    expect(screen.getByText('75.5%')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  test('shows active status correctly', () => {
    render(<BotCard {...mockProps} />);

    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByTestId('status-indicator')).toHaveClass('bg-green-500');
  });

  test('shows inactive status correctly', () => {
    const inactiveBot = { ...mockBot, is_active: false };
    render(<BotCard {...mockProps} bot={inactiveBot} />);

    expect(screen.getByText('Inactive')).toBeInTheDocument();
    expect(screen.getByTestId('status-indicator')).toHaveClass('bg-gray-500');
  });

  test('handles start bot action', async () => {
    const user = userEvent.setup();
    const inactiveBot = { ...mockBot, is_active: false };
    
    render(<BotCard {...mockProps} bot={inactiveBot} />);

    const startButton = screen.getByText('Start');
    await user.click(startButton);

    expect(mockProps.onStart).toHaveBeenCalledWith(mockBot.id);
  });

  test('handles stop bot action', async () => {
    const user = userEvent.setup();
    
    render(<BotCard {...mockProps} />);

    const stopButton = screen.getByText('Stop');
    await user.click(stopButton);

    expect(mockProps.onStop).toHaveBeenCalledWith(mockBot.id);
  });

  test('handles edit bot action', async () => {
    const user = userEvent.setup();
    
    render(<BotCard {...mockProps} />);

    const editButton = screen.getByTestId('edit-button');
    await user.click(editButton);

    expect(mockProps.onEdit).toHaveBeenCalledWith(mockBot);
  });

  test('handles delete bot action with confirmation', async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => true);
    
    render(<BotCard {...mockProps} />);

    const deleteButton = screen.getByTestId('delete-button');
    await user.click(deleteButton);

    expect(window.confirm).toHaveBeenCalledWith(
      'Are you sure you want to delete this bot?'
    );
    expect(mockProps.onDelete).toHaveBeenCalledWith(mockBot.id);
  });

  test('cancels delete action when not confirmed', async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => false);
    
    render(<BotCard {...mockProps} />);

    const deleteButton = screen.getByTestId('delete-button');
    await user.click(deleteButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(mockProps.onDelete).not.toHaveBeenCalled();
  });
});
```

### Hook Tests

```javascript
// useAuth.test.js
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useAuth Hook', () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = jest.fn();
  });

  test('initializes with no user when no token exists', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  test('logs in user successfully', async () => {
    const mockUser = { id: 1, email: 'test@example.com' };
    const mockResponse = {
      access_token: 'mock-token',
      user: mockUser
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(localStorage.setItem).toHaveBeenCalledWith('token', 'mock-token');
  });

  test('handles login error', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'Invalid credentials' })
    });

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrong-password');
      } catch (error) {
        expect(error.message).toBe('Invalid credentials');
      }
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('logs out user', async () => {
    localStorage.setItem('token', 'mock-token');
    
    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.removeItem).toHaveBeenCalledWith('token');
  });
});
```

### Running Frontend Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test Dashboard.test.js

# Run tests matching pattern
npm test -- --testNamePattern="login"

# Run tests in CI mode
npm test -- --ci --coverage --watchAll=false
```

## Integration Testing

### API Integration Tests

```python
# tests/integration/test_api_integration.py
import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor

class TestAPIIntegration:
    base_url = 'http://localhost:5000/api'
    
    def test_user_registration_and_login_flow(self):
        """Test complete user registration and login flow."""
        # Register user
        register_data = {
            'email': f'test_{int(time.time())}@example.com',
            'username': f'testuser_{int(time.time())}',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        register_response = requests.post(
            f'{self.base_url}/v2/auth/register',
            json=register_data
        )
        assert register_response.status_code == 201
        
        # Login user
        login_data = {
            'email': register_data['email'],
            'password': register_data['password']
        }
        
        login_response = requests.post(
            f'{self.base_url}/v2/auth/login',
            json=login_data
        )
        assert login_response.status_code == 200
        
        login_result = login_response.json()
        assert 'access_token' in login_result
        assert 'user' in login_result
        
        return login_result['access_token']
    
    def test_bot_management_flow(self):
        """Test complete bot management flow."""
        # Get auth token
        token = self.test_user_registration_and_login_flow()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create bot
        bot_data = {
            'name': 'Integration Test Bot',
            'strategy': 'grid_trading',
            'config': {
                'grid_size': 10,
                'profit_target': 0.02,
                'symbol': 'BTC/USDT'
            }
        }
        
        create_response = requests.post(
            f'{self.base_url}/trading/bots',
            json=bot_data,
            headers=headers
        )
        assert create_response.status_code == 201
        
        bot = create_response.json()
        bot_id = bot['id']
        
        # Get bot details
        get_response = requests.get(
            f'{self.base_url}/trading/bots/{bot_id}',
            headers=headers
        )
        assert get_response.status_code == 200
        
        # Update bot
        update_data = {'name': 'Updated Integration Test Bot'}
        update_response = requests.put(
            f'{self.base_url}/trading/bots/{bot_id}',
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Start bot
        start_response = requests.post(
            f'{self.base_url}/trading/bots/{bot_id}/start',
            headers=headers
        )
        assert start_response.status_code == 200
        
        # Stop bot
        stop_response = requests.post(
            f'{self.base_url}/trading/bots/{bot_id}/stop',
            headers=headers
        )
        assert stop_response.status_code == 200
        
        # Delete bot
        delete_response = requests.delete(
            f'{self.base_url}/trading/bots/{bot_id}',
            headers=headers
        )
        assert delete_response.status_code == 200
    
    def test_concurrent_api_requests(self):
        """Test API under concurrent load."""
        token = self.test_user_registration_and_login_flow()
        headers = {'Authorization': f'Bearer {token}'}
        
        def make_request():
            response = requests.get(
                f'{self.base_url}/trading/bots',
                headers=headers
            )
            return response.status_code
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_rate_limiting(self):
        """Test API rate limiting."""
        # Make rapid requests to trigger rate limiting
        responses = []
        for _ in range(100):
            response = requests.get(f'{self.base_url}/health')
            responses.append(response.status_code)
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert 429 in responses
```

### Database Integration Tests

```python
# tests/integration/test_database_integration.py
import pytest
from sqlalchemy import text
from app import db
from models.user import User
from models.bot import Bot
from models.trade import Trade

class TestDatabaseIntegration:
    def test_database_constraints(self, db_session):
        """Test database constraints and relationships."""
        # Test unique email constraint
        user1 = User(email='test@example.com', username='user1')
        user2 = User(email='test@example.com', username='user2')
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
        
        db_session.rollback()
    
    def test_cascade_deletions(self, db_session):
        """Test cascade deletions work correctly."""
        # Create user with bot and trades
        user = User(email='test@example.com', username='testuser')
        db_session.add(user)
        db_session.commit()
        
        bot = Bot(name='Test Bot', strategy='grid_trading', user_id=user.id)
        db_session.add(bot)
        db_session.commit()
        
        trade = Trade(
            bot_id=bot.id,
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            price=50000
        )
        db_session.add(trade)
        db_session.commit()
        
        # Delete user should cascade to bots and trades
        db_session.delete(user)
        db_session.commit()
        
        # Verify cascaded deletions
        assert db_session.query(Bot).filter_by(user_id=user.id).count() == 0
        assert db_session.query(Trade).filter_by(bot_id=bot.id).count() == 0
    
    def test_database_performance(self, db_session):
        """Test database query performance."""
        import time
        
        # Create test data
        user = User(email='test@example.com', username='testuser')
        db_session.add(user)
        db_session.commit()
        
        # Create multiple bots
        bots = []
        for i in range(100):
            bot = Bot(
                name=f'Bot {i}',
                strategy='grid_trading',
                user_id=user.id
            )
            bots.append(bot)
        
        db_session.add_all(bots)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        result = db_session.query(Bot).filter_by(user_id=user.id).all()
        end_time = time.time()
        
        assert len(result) == 100
        assert end_time - start_time < 1.0  # Should complete within 1 second
    
    def test_transaction_rollback(self, db_session):
        """Test transaction rollback functionality."""
        user = User(email='test@example.com', username='testuser')
        db_session.add(user)
        
        try:
            # Simulate error during transaction
            db_session.commit()
            
            # Add invalid data
            invalid_bot = Bot(
                name='Test Bot',
                strategy='invalid_strategy',  # This should fail validation
                user_id=user.id
            )
            db_session.add(invalid_bot)
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # User should still exist, bot should not
        assert db_session.query(User).filter_by(email='test@example.com').first() is not None
        assert db_session.query(Bot).filter_by(name='Test Bot').first() is None
```

## End-to-End Testing

### Playwright E2E Tests

```javascript
// tests/e2e/auth-flow.spec.js
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('user can register and login', async ({ page }) => {
    // Navigate to register page
    await page.click('text=Sign Up');
    await expect(page).toHaveURL(/.*\/register/);

    // Fill registration form
    const timestamp = Date.now();
    await page.fill('[data-testid="email-input"]', `test${timestamp}@example.com`);
    await page.fill('[data-testid="username-input"]', `testuser${timestamp}`);
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.fill('[data-testid="confirm-password-input"]', 'password123');

    // Submit registration
    await page.click('[data-testid="register-button"]');

    // Should redirect to login or dashboard
    await expect(page).toHaveURL(/.*\/(login|dashboard)/);

    // If redirected to login, perform login
    if (page.url().includes('/login')) {
      await page.fill('[data-testid="email-input"]', `test${timestamp}@example.com`);
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-button"]');
    }

    // Should be on dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('text=Welcome back')).toBeVisible();
  });

  test('shows error for invalid login', async ({ page }) => {
    await page.click('text=Sign In');
    
    await page.fill('[data-testid="email-input"]', 'invalid@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="login-button"]');

    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });

  test('user can logout', async ({ page }) => {
    // Login first (assuming we have a test user)
    await page.goto('http://localhost:3000/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');

    // Should be on dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);

    // Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('text=Logout');

    // Should redirect to home
    await expect(page).toHaveURL('http://localhost:3000/');
    await expect(page.locator('text=Sign In')).toBeVisible();
  });
});
```

```javascript
// tests/e2e/bot-management.spec.js
import { test, expect } from '@playwright/test';

test.describe('Bot Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('http://localhost:3000/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('user can create a new bot', async ({ page }) => {
    // Navigate to bot creation
    await page.click('text=Create New Bot');
    await expect(page.locator('[data-testid="bot-creation-modal"]')).toBeVisible();

    // Fill bot creation form
    await page.fill('[data-testid="bot-name-input"]', 'E2E Test Bot');
    await page.selectOption('[data-testid="strategy-select"]', 'grid_trading');
    await page.fill('[data-testid="grid-size-input"]', '10');
    await page.fill('[data-testid="profit-target-input"]', '2');
    await page.selectOption('[data-testid="symbol-select"]', 'BTC/USDT');

    // Submit form
    await page.click('[data-testid="create-bot-button"]');

    // Should see success message and new bot in list
    await expect(page.locator('text=Bot created successfully')).toBeVisible();
    await expect(page.locator('text=E2E Test Bot')).toBeVisible();
  });

  test('user can start and stop a bot', async ({ page }) => {
    // Assuming we have a bot in the list
    const botCard = page.locator('[data-testid="bot-card"]').first();
    
    // Start bot
    await botCard.locator('[data-testid="start-bot-button"]').click();
    await expect(page.locator('text=Bot started successfully')).toBeVisible();
    await expect(botCard.locator('text=Active')).toBeVisible();

    // Stop bot
    await botCard.locator('[data-testid="stop-bot-button"]').click();
    await expect(page.locator('text=Bot stopped successfully')).toBeVisible();
    await expect(botCard.locator('text=Inactive')).toBeVisible();
  });

  test('user can view bot details and trade history', async ({ page }) => {
    // Click on a bot to view details
    await page.locator('[data-testid="bot-card"]').first().click();
    
    // Should navigate to bot details page
    await expect(page).toHaveURL(/.*\/bots\/\d+/);
    await expect(page.locator('[data-testid="bot-details"]')).toBeVisible();
    
    // Check trade history tab
    await page.click('text=Trade History');
    await expect(page.locator('[data-testid="trade-history-table"]')).toBeVisible();
    
    // Check performance tab
    await page.click('text=Performance');
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();
  });

  test('user can delete a bot', async ({ page }) => {
    const botCard = page.locator('[data-testid="bot-card"]').first();
    const botName = await botCard.locator('[data-testid="bot-name"]').textContent();
    
    // Click delete button
    await botCard.locator('[data-testid="delete-bot-button"]').click();
    
    // Confirm deletion in modal
    await expect(page.locator('[data-testid="delete-confirmation-modal"]')).toBeVisible();
    await page.click('[data-testid="confirm-delete-button"]');
    
    // Bot should be removed from list
    await expect(page.locator('text=Bot deleted successfully')).toBeVisible();
    await expect(page.locator(`text=${botName}`)).not.toBeVisible();
  });
});
```

### Running E2E Tests

```bash
# Install Playwright
npm install -D @playwright/test
npx playwright install

# Run E2E tests
npx playwright test

# Run tests in headed mode
npx playwright test --headed

# Run specific test file
npx playwright test auth-flow.spec.js

# Run tests with specific browser
npx playwright test --project=chromium

# Generate test report
npx playwright show-report
```

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json
import random

class TradingBotUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login user before starting tasks."""
        response = self.client.post('/api/v2/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        if response.status_code == 200:
            self.token = response.json()['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        """Simulate viewing dashboard."""
        self.client.get('/api/trading/bots', headers=self.headers)
    
    @task(2)
    def view_bot_details(self):
        """Simulate viewing bot details."""
        bot_id = random.randint(1, 10)
        self.client.get(f'/api/trading/bots/{bot_id}', headers=self.headers)
    
    @task(1)
    def create_bot(self):
        """Simulate creating a bot."""
        bot_data = {
            'name': f'Load Test Bot {random.randint(1, 1000)}',
            'strategy': 'grid_trading',
            'config': {
                'grid_size': random.randint(5, 20),
                'profit_target': random.uniform(0.01, 0.05),
                'symbol': random.choice(['BTC/USDT', 'ETH/USDT', 'ADA/USDT'])
            }
        }
        
        self.client.post('/api/trading/bots', 
                        json=bot_data, 
                        headers=self.headers)
    
    @task(1)
    def start_stop_bot(self):
        """Simulate starting/stopping bots."""
        bot_id = random.randint(1, 10)
        action = random.choice(['start', 'stop'])
        
        self.client.post(f'/api/trading/bots/{bot_id}/{action}', 
                        headers=self.headers)
    
    @task(2)
    def view_trade_history(self):
        """Simulate viewing trade history."""
        bot_id = random.randint(1, 10)
        self.client.get(f'/api/trading/bots/{bot_id}/trades', 
                       headers=self.headers)

class AdminUser(HttpUser):
    wait_time = between(2, 5)
    weight = 1  # Lower weight for admin users
    
    def on_start(self):
        """Login admin user."""
        response = self.client.post('/api/v2/auth/login', json={
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        
        if response.status_code == 200:
            self.token = response.json()['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
    
    @task
    def view_admin_dashboard(self):
        """Simulate admin dashboard access."""
        self.client.get('/api/admin/dashboard', headers=self.headers)
    
    @task
    def view_user_management(self):
        """Simulate user management access."""
        self.client.get('/api/admin/users', headers=self.headers)
```

### Running Performance Tests

```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:5000

# Run headless load test
locust -f tests/performance/locustfile.py --host=http://localhost:5000 \
       --users 100 --spawn-rate 10 --run-time 300s --headless

# Generate performance report
locust -f tests/performance/locustfile.py --host=http://localhost:5000 \
       --users 50 --spawn-rate 5 --run-time 180s --html performance_report.html
```

### Database Performance Testing

```python
# tests/performance/test_database_performance.py
import pytest
import time
from sqlalchemy import text
from app import db
from models.user import User
from models.bot import Bot
from models.trade import Trade

class TestDatabasePerformance:
    def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance."""
        users = []
        for i in range(1000):
            user = User(
                email=f'user{i}@example.com',
                username=f'user{i}',
                password_hash='hashed_password'
            )
            users.append(user)
        
        start_time = time.time()
        db_session.add_all(users)
        db_session.commit()
        end_time = time.time()
        
        insert_time = end_time - start_time
        assert insert_time < 5.0  # Should complete within 5 seconds
        print(f"Bulk insert of 1000 users took {insert_time:.2f} seconds")
    
    def test_complex_query_performance(self, db_session):
        """Test complex query performance."""
        # Create test data
        user = User(email='test@example.com', username='testuser')
        db_session.add(user)
        db_session.commit()
        
        bots = []
        for i in range(100):
            bot = Bot(
                name=f'Bot {i}',
                strategy='grid_trading',
                user_id=user.id
            )
            bots.append(bot)
        
        db_session.add_all(bots)
        db_session.commit()
        
        # Add trades for each bot
        trades = []
        for bot in bots:
            for j in range(50):
                trade = Trade(
                    bot_id=bot.id,
                    symbol='BTC/USDT',
                    side='buy' if j % 2 == 0 else 'sell',
                    amount=0.1,
                    price=50000 + j * 100
                )
                trades.append(trade)
        
        db_session.add_all(trades)
        db_session.commit()
        
        # Test complex query
        start_time = time.time()
        result = db_session.execute(text("""
            SELECT 
                b.name,
                COUNT(t.id) as trade_count,
                AVG(t.price) as avg_price,
                SUM(CASE WHEN t.side = 'buy' THEN t.amount ELSE 0 END) as total_bought,
                SUM(CASE WHEN t.side = 'sell' THEN t.amount ELSE 0 END) as total_sold
            FROM bots b
            LEFT JOIN trades t ON b.id = t.bot_id
            WHERE b.user_id = :user_id
            GROUP BY b.id, b.name
            ORDER BY trade_count DESC
        """), {'user_id': user.id}).fetchall()
        end_time = time.time()
        
        query_time = end_time - start_time
        assert query_time < 2.0  # Should complete within 2 seconds
        assert len(result) == 100
        print(f"Complex query took {query_time:.2f} seconds")
```

## Security Testing

### OWASP ZAP Integration

```python
# tests/security/test_security.py
import pytest
import requests
from zapv2 import ZAPv2

class TestSecurityScanning:
    def setup_class(self):
        """Setup ZAP proxy."""
        self.zap = ZAPv2(proxies={'http': 'http://127.0.0.1:8080', 
                                 'https': 'http://127.0.0.1:8080'})
    
    def test_passive_security_scan(self):
        """Run passive security scan."""
        target_url = 'http://localhost:3000'
        
        # Spider the application
        self.zap.spider.scan(target_url)
        
        # Wait for spider to complete
        while int(self.zap.spider.status()) < 100:
            time.sleep(1)
        
        # Get passive scan results
        alerts = self.zap.core.alerts()
        
        # Check for high-risk vulnerabilities
        high_risk_alerts = [alert for alert in alerts 
                           if alert['risk'] == 'High']
        
        assert len(high_risk_alerts) == 0, f"High risk vulnerabilities found: {high_risk_alerts}"
    
    def test_active_security_scan(self):
        """Run active security scan."""
        target_url = 'http://localhost:3000'
        
        # Start active scan
        scan_id = self.zap.ascan.scan(target_url)
        
        # Wait for scan to complete
        while int(self.zap.ascan.status(scan_id)) < 100:
            time.sleep(5)
        
        # Get scan results
        alerts = self.zap.core.alerts()
        
        # Filter critical vulnerabilities
        critical_alerts = [alert for alert in alerts 
                          if alert['risk'] in ['High', 'Medium']]
        
        # Generate report
        report = self.zap.core.htmlreport()
        with open('security_report.html', 'w') as f:
            f.write(report)
        
        assert len(critical_alerts) == 0, f"Critical vulnerabilities found: {critical_alerts}"
```

### Manual Security Tests

```python
# tests/security/test_manual_security.py
import pytest
import requests
import jwt
from datetime import datetime, timedelta

class TestManualSecurity:
    base_url = 'http://localhost:5000/api'
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        # Test SQL injection in login
        malicious_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in malicious_payloads:
            response = requests.post(f'{self.base_url}/v2/auth/login', json={
                'email': payload,
                'password': 'password'
            })
            
            # Should not return 200 or expose database errors
            assert response.status_code in [400, 401, 422]
            assert 'error' not in response.text.lower() or 'sql' not in response.text.lower()
    
    def test_xss_protection(self):
        """Test XSS protection."""
        # Get auth token first
        login_response = requests.post(f'{self.base_url}/v2/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            response = requests.post(f'{self.base_url}/trading/bots', 
                                   json={'name': payload, 'strategy': 'grid_trading'},
                                   headers=headers)
            
            if response.status_code == 201:
                # Check that payload is properly escaped
                bot_data = response.json()
                assert '<script>' not in bot_data.get('name', '')
                assert 'javascript:' not in bot_data.get('name', '')
    
    def test_jwt_token_security(self):
        """Test JWT token security."""
        # Test with invalid token
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        response = requests.get(f'{self.base_url}/trading/bots', headers=invalid_headers)
        assert response.status_code == 401
        
        # Test with expired token
        expired_payload = {
            'user_id': 1,
            'exp': datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, 'secret', algorithm='HS256')
        expired_headers = {'Authorization': f'Bearer {expired_token}'}
        
        response = requests.get(f'{self.base_url}/trading/bots', headers=expired_headers)
        assert response.status_code == 401
    
    def test_rate_limiting(self):
        """Test rate limiting protection."""
        # Make rapid requests to trigger rate limiting
        responses = []
        for i in range(100):
            response = requests.post(f'{self.base_url}/v2/auth/login', json={
                'email': 'test@example.com',
                'password': 'wrong_password'
            })
            responses.append(response.status_code)
            
            if response.status_code == 429:
                break
        
        # Should eventually hit rate limit
        assert 429 in responses
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        # Test preflight request
        response = requests.options(f'{self.base_url}/trading/bots', 
                                  headers={
                                      'Origin': 'http://malicious-site.com',
                                      'Access-Control-Request-Method': 'POST'
                                  })
        
        # Should not allow arbitrary origins
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        assert cors_origin != '*' or cors_origin != 'http://malicious-site.com'
```

## API Testing

### Postman Collection

```json
{
  "info": {
    "name": "Trading Bot Platform API",
    "description": "Comprehensive API test collection",
    "version": "2.0.0"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "event": [
    {
      "listen": "prerequest",
      "script": {
        "exec": [
          "// Auto-login if no token exists",
          "if (!pm.environment.get('access_token')) {",
          "  pm.sendRequest({",
          "    url: pm.environment.get('base_url') + '/api/v2/auth/login',",
          "    method: 'POST',",
          "    header: {",
          "      'Content-Type': 'application/json'",
          "    },",
          "    body: {",
          "      mode: 'raw',",
          "      raw: JSON.stringify({",
          "        email: pm.environment.get('test_email'),",
          "        password: pm.environment.get('test_password')",
          "      })",
          "    }",
          "  }, function (err, response) {",
          "    if (response.code === 200) {",
          "      const data = response.json();",
          "      pm.environment.set('access_token', data.access_token);",
          "    }",
          "  });",
          "}"
        ]
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:5000"
    },
    {
      "key": "test_email",
      "value": "test@example.com"
    },
    {
      "key": "test_password",
      "value": "password123"
    }
  ]
}
```

### Newman CLI Testing

```bash
# Install Newman
npm install -g newman

# Run Postman collection
newman run trading-bot-api.postman_collection.json \
       -e production.postman_environment.json \
       --reporters cli,html \
       --reporter-html-export api-test-report.html

# Run with data file
newman run trading-bot-api.postman_collection.json \
       -d test-data.csv \
       --iteration-count 10
```

## Test Data Management

### Test Data Factory

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from models.user import User
from models.bot import Bot
from models.trade import Trade
from app import db

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    password_hash = 'hashed_password'
    is_verified = True
    subscription_plan = 'basic'

class BotFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Bot
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    name = factory.Sequence(lambda n: f'Bot {n}')
    strategy = factory.Iterator(['grid_trading', 'dca', 'arbitrage'])
    user = factory.SubFactory(UserFactory)
    is_active = False
    config = factory.LazyFunction(lambda: {
        'grid_size': 10,
        'profit_target': 0.02,
        'symbol': 'BTC/USDT'
    })

class TradeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Trade
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    bot = factory.SubFactory(BotFactory)
    symbol = factory.Iterator(['BTC/USDT', 'ETH/USDT', 'ADA/USDT'])
    side = factory.Iterator(['buy', 'sell'])
    amount = factory.Faker('pydecimal', left_digits=1, right_digits=4, positive=True)
    price = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    exchange_order_id = factory.Sequence(lambda n: f'order_{n}')
    status = 'filled'

# Usage in tests
def test_with_factory_data():
    user = UserFactory()
    bot = BotFactory(user=user)
    trades = TradeFactory.create_batch(10, bot=bot)
    
    assert len(trades) == 10
    assert all(trade.bot_id == bot.id for trade in trades)
```

### Test Database Seeding

```python
# tests/seed_data.py
from factories import UserFactory, BotFactory, TradeFactory
from app import db

def seed_test_database():
    """Seed database with test data."""
    # Create test users
    admin_user = UserFactory(
        email='admin@example.com',
        username='admin',
        role='admin',
        is_verified=True
    )
    
    regular_users = UserFactory.create_batch(10)
    
    # Create bots for users
    for user in regular_users:
        bots = BotFactory.create_batch(3, user=user)
        
        # Create trades for each bot
        for bot in bots:
            TradeFactory.create_batch(20, bot=bot)
    
    db.session.commit()
    print("Test database seeded successfully!")

if __name__ == '__main__':
    seed_test_database()
```

## Best Practices

### Test Organization

1. **Follow AAA Pattern**
   - **Arrange:** Set up test data and conditions
   - **Act:** Execute the code being tested
   - **Assert:** Verify the results

2. **Use Descriptive Test Names**
   ```python
   # Good
   def test_user_can_create_bot_with_valid_config()
   def test_bot_creation_fails_with_invalid_strategy()
   
   # Bad
   def test_bot_creation()
   def test_create()
   ```

3. **Keep Tests Independent**
   - Each test should be able to run in isolation
   - Use fixtures and factories for test data
   - Clean up after each test

4. **Test Edge Cases**
   - Boundary values
   - Error conditions
   - Invalid inputs
   - Network failures

### Test Coverage

```bash
# Backend coverage
pytest --cov=app --cov-report=html --cov-report=term

# Frontend coverage
npm test -- --coverage --watchAll=false

# Coverage thresholds in pytest.ini
[tool:pytest]
addopts = --cov=app --cov-fail-under=90
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        TESTING: true
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Playwright
      run: |
        npm install -g @playwright/test
        npx playwright install
    
    - name: Start application
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30
    
    - name: Run E2E tests
      run: |
        npx playwright test
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # Check database logs
   docker-compose logs postgres
   
   # Reset test database
   docker-compose down
   docker-compose up -d postgres
   ```

2. **Frontend Test Failures**
   ```bash
   # Clear Jest cache
   npm test -- --clearCache
   
   # Update snapshots
   npm test -- --updateSnapshot
   
   # Run tests in debug mode
   npm test -- --verbose
   ```

3. **E2E Test Failures**
   ```bash
   # Run in headed mode for debugging
   npx playwright test --headed
   
   # Generate trace for failed tests
   npx playwright test --trace on
   
   # View test report
   npx playwright show-report
   ```

4. **Performance Test Issues**
   ```bash
   # Check system resources
   htop
   docker stats
   
   # Reduce load test intensity
   locust -f locustfile.py --users 10 --spawn-rate 1
   ```

### Debugging Tips

1. **Use Test Debugging Tools**
   ```python
   # Add breakpoints in tests
   import pdb; pdb.set_trace()
   
   # Use pytest debugging
   pytest --pdb
   
   # Capture output
   pytest -s
   ```

2. **Mock External Services**
   ```python
   # Mock API calls
   @patch('services.exchange_api.get_ticker')
   def test_with_mocked_api(mock_get_ticker):
       mock_get_ticker.return_value = {'price': 50000}
       # Test code here
   ```

3. **Test Data Isolation**
   ```python
   # Use transactions for test isolation
   @pytest.fixture
   def db_session():
       connection = db.engine.connect()
       transaction = connection.begin()
       session = db.create_scoped_session(
           options={"bind": connection, "binds": {}}
       )
       yield session
       session.close()
       transaction.rollback()
       connection.close()
   ```

---

**Testing Resources:**
- 📚 [Pytest Documentation](https://docs.pytest.org/)
- 🧪 [Jest Testing Framework](https://jestjs.io/)
- 🎭 [Playwright Documentation](https://playwright.dev/)
- 🦗 [Locust Performance Testing](https://locust.io/)
- 🔒 [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

**Last Updated:** January 2024  
**Version:** 2.0.0