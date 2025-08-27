import pytest
from unittest.mock import patch, MagicMock, Mock
from bot_engine.trading_engine import TradingEngine
from models.user import User
from models.api_key import APIKey


class TestTradingEngineCore:
    """Test core TradingEngine functionality and initialization."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock()
        user.id = 1
        user.username = "testuser"
        return user
    
    @pytest.fixture
    def mock_api_key(self):
        """Create a mock API key for testing."""
        api_key = Mock()
        api_key.api_key = "test_api_key"
        api_key.api_secret = "test_api_secret"
        api_key.exchange = "binance"
        return api_key
    
    def test_trading_engine_initialization_success(self, mock_user, mock_api_key):
        """Test successful TradingEngine initialization with valid API keys."""
        with patch('bot_engine.trading_engine.APIKeyService') as mock_service:
            mock_service.return_value.get_api_keys.return_value = mock_api_key
            
            with patch('bot_engine.trading_engine.ExchangeFactory') as mock_factory:
                mock_exchange = Mock()
                mock_factory.create_exchange.return_value = mock_exchange
                
                # Should not raise exception
                engine = TradingEngine(mock_user)
                assert engine is not None
    
    def test_trading_engine_initialization_missing_api_keys(self, mock_user):
        """Test TradingEngine initialization fails with missing API keys."""
        with patch('bot_engine.trading_engine.APIKeyService') as mock_service:
            mock_service.return_value.get_api_keys.return_value = None
            
            with pytest.raises(ValueError, match="MISSING_API_KEYS"):
                TradingEngine(mock_user)
    
    def test_trading_engine_initialization_invalid_api_keys(self, mock_user, mock_api_key):
        """Test TradingEngine initialization fails with invalid API keys."""
        with patch('bot_engine.trading_engine.APIKeyService') as mock_service:
            mock_service.return_value.get_api_keys.return_value = mock_api_key
            
            with patch('bot_engine.trading_engine.ExchangeFactory') as mock_factory:
                mock_factory.create_exchange.side_effect = Exception("Invalid API credentials")
                
                with pytest.raises(ValueError, match="INVALID_API_KEYS"):
                    TradingEngine(mock_user)
    
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_get_account_balance(self, mock_factory, mock_service, mock_user, mock_api_key):
        """Test getting account balance through trading engine."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            'USDT': {'free': 1000.0, 'used': 0.0, 'total': 1000.0},
            'BTC': {'free': 0.5, 'used': 0.0, 'total': 0.5}
        }
        mock_factory.create_exchange.return_value = mock_exchange
        
        engine = TradingEngine(mock_user)
        balance = engine.get_account_balance()
        
        assert 'USDT' in balance
        assert balance['USDT']['free'] == 1000.0
        mock_exchange.fetch_balance.assert_called_once()
    
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_get_market_data(self, mock_factory, mock_service, mock_user, mock_api_key):
        """Test getting market data through trading engine."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 45000.0,
            'bid': 44999.0,
            'ask': 45001.0,
            'volume': 1234.56
        }
        mock_factory.create_exchange.return_value = mock_exchange
        
        engine = TradingEngine(mock_user)
        market_data = engine.get_market_data('BTCUSDT')
        
        assert market_data['symbol'] == 'BTC/USDT'
        assert market_data['last'] == 45000.0
        mock_exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
    
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_place_order_success(self, mock_factory, mock_service, mock_user, mock_api_key):
        """Test successful order placement through trading engine."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_exchange.create_market_buy_order.return_value = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'amount': 0.001,
            'price': 45000.0,
            'status': 'closed'
        }
        mock_factory.create_exchange.return_value = mock_exchange
        
        engine = TradingEngine(mock_user)
        order = engine.place_market_order('BTCUSDT', 'buy', 0.001)
        
        assert order['id'] == '12345'
        assert order['status'] == 'closed'
        mock_exchange.create_market_buy_order.assert_called_once()
    
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_place_order_insufficient_balance(self, mock_factory, mock_service, mock_user, mock_api_key):
        """Test order placement fails with insufficient balance."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_exchange.create_market_buy_order.side_effect = Exception("Insufficient balance")
        mock_factory.create_exchange.return_value = mock_exchange
        
        engine = TradingEngine(mock_user)
        
        with pytest.raises(Exception, match="Insufficient balance"):
            engine.place_market_order('BTCUSDT', 'buy', 10.0)  # Large amount
    
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_get_available_symbols(self, mock_factory, mock_service, mock_user, mock_api_key):
        """Test getting available trading symbols."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_exchange.load_markets.return_value = {
            'BTC/USDT': {'symbol': 'BTC/USDT', 'active': True},
            'ETH/USDT': {'symbol': 'ETH/USDT', 'active': True},
            'ADA/USDT': {'symbol': 'ADA/USDT', 'active': False}
        }
        mock_factory.create_exchange.return_value = mock_exchange
        
        engine = TradingEngine(mock_user)
        symbols = engine.get_available_symbols()
        
        # Should only return active symbols
        assert 'BTC/USDT' in symbols
        assert 'ETH/USDT' in symbols
        assert 'ADA/USDT' not in symbols  # Inactive
        mock_exchange.load_markets.assert_called_once()