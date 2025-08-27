import pytest
import time
import threading
from unittest.mock import patch, Mock
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.trading_service import TradingService
from bot_engine.trading_engine import TradingEngine


class TestPerformanceBenchmarks:
    """Performance and load testing for critical trading bot operations."""
    
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
    
    @pytest.mark.performance
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_trading_engine_initialization_performance(self, mock_factory, mock_service, 
                                                     mock_user, mock_api_key):
        """Test TradingEngine initialization performance under load."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_factory.create_exchange.return_value = mock_exchange
        
        # Measure initialization time
        start_time = time.time()
        
        # Initialize multiple engines concurrently
        engines = []
        for _ in range(10):
            engine = TradingEngine(mock_user)
            engines.append(engine)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should initialize 10 engines in less than 1 second
        assert total_time < 1.0
        assert len(engines) == 10
    
    @pytest.mark.performance
    @patch('bot_engine.trading_engine.APIKeyService')
    @patch('bot_engine.trading_engine.ExchangeFactory')
    def test_concurrent_market_data_requests(self, mock_factory, mock_service, 
                                           mock_user, mock_api_key):
        """Test concurrent market data requests performance."""
        # Setup mocks
        mock_service.return_value.get_api_keys.return_value = mock_api_key
        mock_exchange = Mock()
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 45000.0,
            'bid': 44999.0,
            'ask': 45001.0
        }
        mock_factory.create_exchange.return_value = mock_exchange
        
        engine = TradingEngine(mock_user)
        
        def fetch_market_data(symbol):
            """Fetch market data for a symbol."""
            start = time.time()
            data = engine.get_market_data(symbol)
            end = time.time()
            return end - start, data
        
        # Test concurrent requests
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT'] * 4
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_market_data, symbol) for symbol in symbols]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 20 requests in less than 2 seconds
        assert total_time < 2.0
        assert len(results) == 20
        
        # Each individual request should be fast
        for request_time, data in results:
            assert request_time < 0.1  # Each request under 100ms
            assert data['symbol'] == 'BTC/USDT'
    
    @pytest.mark.performance
    @patch('services.trading_service.db')
    def test_bot_creation_performance(self, mock_db):
        """Test bot creation performance under load."""
        trading_service = TradingService()
        
        # Mock database operations
        mock_db.session.add = Mock()
        mock_db.session.commit = Mock()
        
        def create_bot(bot_id):
            """Create a bot with given ID."""
            bot_data = {
                'name': f'Test Bot {bot_id}',
                'symbol': 'BTCUSDT',
                'strategy': 'moving_average',
                'parameters': {'period': 20, 'threshold': 0.02}
            }
            
            with patch('services.trading_service.Bot') as mock_bot_class:
                mock_bot_instance = Mock()
                mock_bot_instance.id = bot_id
                mock_bot_class.return_value = mock_bot_instance
                
                start = time.time()
                result = trading_service.create_bot(1, bot_data)
                end = time.time()
                
                return end - start, result
        
        # Create multiple bots concurrently
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_bot, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should create 20 bots in less than 1 second
        assert total_time < 1.0
        assert len(results) == 20
        
        # Each bot creation should be fast
        for creation_time, result in results:
            assert creation_time < 0.05  # Each creation under 50ms
    
    @pytest.mark.performance
    @pytest.mark.load
    def test_memory_usage_under_load(self, mock_user, mock_api_key):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate heavy load
        with patch('bot_engine.trading_engine.APIKeyService') as mock_service:
            with patch('bot_engine.trading_engine.ExchangeFactory') as mock_factory:
                mock_service.return_value.get_api_keys.return_value = mock_api_key
                mock_exchange = Mock()
                mock_factory.create_exchange.return_value = mock_exchange
                
                engines = []
                for i in range(50):
                    engine = TradingEngine(mock_user)
                    engines.append(engine)
                    
                    # Simulate some operations
                    mock_exchange.fetch_ticker.return_value = {'last': 45000.0}
                    engine.get_market_data('BTCUSDT')
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 50 engines)
        assert memory_increase < 100
    
    @pytest.mark.performance
    @pytest.mark.stress
    def test_error_handling_performance(self, mock_user, mock_api_key):
        """Test that error handling doesn't significantly impact performance."""
        with patch('bot_engine.trading_engine.APIKeyService') as mock_service:
            with patch('bot_engine.trading_engine.ExchangeFactory') as mock_factory:
                mock_service.return_value.get_api_keys.return_value = mock_api_key
                
                # Mock exchange that sometimes fails
                mock_exchange = Mock()
                call_count = 0
                
                def side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count % 3 == 0:  # Fail every 3rd call
                        raise Exception("Network error")
                    return {'last': 45000.0}
                
                mock_exchange.fetch_ticker.side_effect = side_effect
                mock_factory.create_exchange.return_value = mock_exchange
                
                engine = TradingEngine(mock_user)
                
                # Measure time with errors
                start_time = time.time()
                
                successful_calls = 0
                failed_calls = 0
                
                for _ in range(100):
                    try:
                        engine.get_market_data('BTCUSDT')
                        successful_calls += 1
                    except Exception:
                        failed_calls += 1
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Should handle 100 calls (with 33% failure rate) in reasonable time
                assert total_time < 1.0
                assert successful_calls > 60  # At least 60% success
                assert failed_calls > 30     # Some failures occurred
    
    @pytest.mark.performance
    def test_database_query_performance(self):
        """Test database query performance for bot operations."""
        with patch('services.trading_service.db') as mock_db:
            trading_service = TradingService()
            
            # Mock query that returns quickly
            mock_query = Mock()
            mock_query.filter_by.return_value.all.return_value = []
            mock_db.session.query.return_value = mock_query
            
            # Measure query time
            start_time = time.time()
            
            # Simulate multiple database queries
            for _ in range(100):
                trading_service.get_user_bots(1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 100 queries should complete quickly
            assert total_time < 0.5
    
    @pytest.mark.performance
    @pytest.mark.regression
    def test_performance_regression_baseline(self, mock_user, mock_api_key):
        """Baseline performance test to detect regressions."""
        with patch('bot_engine.trading_engine.APIKeyService') as mock_service:
            with patch('bot_engine.trading_engine.ExchangeFactory') as mock_factory:
                mock_service.return_value.get_api_keys.return_value = mock_api_key
                mock_exchange = Mock()
                mock_exchange.fetch_ticker.return_value = {'last': 45000.0}
                mock_factory.create_exchange.return_value = mock_exchange
                
                # Baseline operations
                operations = [
                    lambda: TradingEngine(mock_user),
                    lambda: TradingEngine(mock_user).get_market_data('BTCUSDT'),
                    lambda: TradingEngine(mock_user).get_account_balance()
                ]
                
                # Measure baseline times
                baseline_times = []
                
                for operation in operations:
                    times = []
                    for _ in range(10):
                        start = time.time()
                        try:
                            operation()
                        except:
                            pass
                        end = time.time()
                        times.append(end - start)
                    
                    avg_time = sum(times) / len(times)
                    baseline_times.append(avg_time)
                
                # Baseline expectations (adjust based on actual performance)
                assert baseline_times[0] < 0.01  # Engine init < 10ms
                assert baseline_times[1] < 0.01  # Market data < 10ms
                assert baseline_times[2] < 0.01  # Account balance < 10ms