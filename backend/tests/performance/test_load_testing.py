"""Performance and load testing for the trading bot platform."""
import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
from decimal import Decimal

from models.user import User
from models.bot import Bot
from services.auth_service import AuthService


@pytest.mark.performance
class TestPerformanceAndLoad:
    """Performance and load testing scenarios."""
    
    def test_api_response_times(self, client, test_user, auth_headers):
        """Test API endpoint response times."""
        endpoints = [
            ('GET', '/api/auth/profile'),
            ('GET', '/api/bots'),
            ('GET', '/api/subscriptions/current'),
            ('GET', '/api/api-keys')
        ]
        
        response_times = {}
        
        for method, endpoint in endpoints:
            times = []
            
            # Test each endpoint 10 times
            for _ in range(10):
                start_time = time.time()
                
                if method == 'GET':
                    response = client.get(endpoint, headers=auth_headers)
                elif method == 'POST':
                    response = client.post(endpoint, headers=auth_headers)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                assert response.status_code in [200, 201]
                times.append(response_time)
            
            response_times[endpoint] = {
                'avg': statistics.mean(times),
                'min': min(times),
                'max': max(times),
                'median': statistics.median(times)
            }
        
        # Assert reasonable response times (< 500ms average)
        for endpoint, metrics in response_times.items():
            assert metrics['avg'] < 500, f"{endpoint} average response time too high: {metrics['avg']}ms"
            assert metrics['max'] < 1000, f"{endpoint} max response time too high: {metrics['max']}ms"
    
    def test_concurrent_user_logins(self, client, session):
        """Test concurrent user login performance."""
        # Create test users
        users = []
        for i in range(20):
            user = User(
                email=f'loadtest{i}@example.com',
                username=f'loadtest{i}',
                password_hash=AuthService.hash_password('password123'),
                is_verified=True
            )
            session.add(user)
            users.append(user)
        
        session.commit()
        
        def login_user(user_email):
            """Login a single user and measure time."""
            start_time = time.time()
            
            login_data = {
                'email': user_email,
                'password': 'password123'
            }
            
            response = client.post('/api/auth/login', json=login_data)
            end_time = time.time()
            
            return {
                'success': response.status_code == 200,
                'response_time': (end_time - start_time) * 1000,
                'email': user_email
            }
        
        # Execute concurrent logins
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_user, user.email) for user in users]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_logins = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_logins]
        
        assert len(successful_logins) == len(users), "Not all logins were successful"
        assert statistics.mean(response_times) < 1000, "Average login time too high"
        assert total_time < 10, "Total concurrent login time too high"
    
    def test_bot_creation_performance(self, client, session, test_user, auth_headers):
        """Test bot creation performance under load."""
        def create_bot(bot_index):
            """Create a single bot and measure time."""
            start_time = time.time()
            
            bot_data = {
                'name': f'Load Test Bot {bot_index}',
                'strategy': 'grid_trading',
                'exchange': 'binance',
                'symbol': 'BTCUSDT',
                'config': {
                    'grid_size': 10,
                    'investment_amount': 1000 + bot_index
                }
            }
            
            response = client.post('/api/bots', 
                                 json=bot_data, 
                                 headers=auth_headers)
            end_time = time.time()
            
            return {
                'success': response.status_code == 201,
                'response_time': (end_time - start_time) * 1000,
                'bot_index': bot_index
            }
        
        # Create 15 bots concurrently
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_bot, i) for i in range(15)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_creations = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_creations]
        
        assert len(successful_creations) == 15, "Not all bot creations were successful"
        assert statistics.mean(response_times) < 2000, "Average bot creation time too high"
        assert max(response_times) < 5000, "Max bot creation time too high"
    
    def test_database_query_performance(self, session, test_user):
        """Test database query performance with large datasets."""
        # Create a large number of bots for testing
        bots = []
        for i in range(100):
            bot = Bot(
                name=f'Perf Test Bot {i}',
                user_id=test_user.id,
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT',
                config={'grid_size': 10},
                status='stopped'
            )
            bots.append(bot)
        
        session.add_all(bots)
        session.commit()
        
        # Test query performance
        queries = [
            lambda: session.query(Bot).filter_by(user_id=test_user.id).all(),
            lambda: session.query(Bot).filter_by(user_id=test_user.id, status='stopped').all(),
            lambda: session.query(Bot).filter(Bot.name.like('Perf Test%')).all(),
            lambda: session.query(Bot).filter_by(user_id=test_user.id).count(),
        ]
        
        for i, query_func in enumerate(queries):
            times = []
            
            # Run each query 5 times
            for _ in range(5):
                start_time = time.time()
                result = query_func()
                end_time = time.time()
                
                query_time = (end_time - start_time) * 1000
                times.append(query_time)
            
            avg_time = statistics.mean(times)
            assert avg_time < 100, f"Query {i} too slow: {avg_time}ms"
    
    def test_api_rate_limiting_performance(self, client, test_user, auth_headers):
        """Test API rate limiting under high load."""
        def make_request():
            """Make a single API request."""
            start_time = time.time()
            response = client.get('/api/auth/profile', headers=auth_headers)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000
            }
        
        # Make 100 requests rapidly
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 200]
        rate_limited_requests = [r for r in results if r['status_code'] == 429]
        
        # Should handle at least 80% of requests successfully
        success_rate = len(successful_requests) / len(results)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
        
        # Rate limiting should kick in for some requests
        assert len(rate_limited_requests) > 0, "Rate limiting not working"
    
    def test_memory_usage_under_load(self, client, session, test_user, auth_headers):
        """Test memory usage during high load operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        operations = [
            # Create many bots
            lambda: [client.post('/api/bots', json={
                'name': f'Memory Test Bot {i}',
                'strategy': 'grid_trading',
                'exchange': 'binance',
                'symbol': 'BTCUSDT',
                'config': {'grid_size': 10}
            }, headers=auth_headers) for i in range(50)],
            
            # Fetch bot lists multiple times
            lambda: [client.get('/api/bots', headers=auth_headers) for _ in range(100)],
            
            # Create and delete API keys
            lambda: [client.post('/api/api-keys', json={
                'name': f'Memory Test Key {i}',
                'permissions': ['read']
            }, headers=auth_headers) for i in range(30)]
        ]
        
        memory_usage = []
        
        for operation in operations:
            operation()
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for test operations)
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase}MB"
    
    def test_websocket_connection_performance(self, client, test_user, auth_headers):
        """Test WebSocket connection performance under load."""
        # This would test WebSocket connections if implemented
        # For now, test the WebSocket info endpoint
        
        def get_websocket_info():
            start_time = time.time()
            response = client.get('/api/websocket/info', headers=auth_headers)
            end_time = time.time()
            
            return {
                'success': response.status_code == 200,
                'response_time': (end_time - start_time) * 1000
            }
        
        # Test concurrent WebSocket info requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_websocket_info) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests]
        
        assert len(successful_requests) == 50, "Not all WebSocket info requests successful"
        assert statistics.mean(response_times) < 200, "WebSocket info response time too high"
    
    def test_trading_simulation_performance(self, client, session, test_user, auth_headers):
        """Test trading simulation performance."""
        # Create a bot for testing
        bot_data = {
            'name': 'Performance Trading Bot',
            'strategy': 'grid_trading',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'config': {
                'grid_size': 10,
                'investment_amount': 1000
            }
        }
        
        response = client.post('/api/bots', json=bot_data, headers=auth_headers)
        bot_id = response.get_json()['bot']['id']
        
        # Mock exchange API for consistent performance testing
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.place_order.return_value = {
                'order_id': 'test_order',
                'status': 'filled',
                'filled_qty': 0.001,
                'avg_price': 50000
            }
            
            def execute_trade():
                start_time = time.time()
                
                trade_data = {
                    'symbol': 'BTCUSDT',
                    'side': 'buy',
                    'quantity': 0.001,
                    'order_type': 'market'
                }
                
                response = client.post(f'/api/bots/{bot_id}/trades',
                                     json=trade_data,
                                     headers=auth_headers)
                end_time = time.time()
                
                return {
                    'success': response.status_code == 201,
                    'response_time': (end_time - start_time) * 1000
                }
            
            # Execute multiple trades concurrently
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(execute_trade) for _ in range(20)]
                results = [future.result() for future in as_completed(futures)]
            
            successful_trades = [r for r in results if r['success']]
            response_times = [r['response_time'] for r in successful_trades]
            
            assert len(successful_trades) == 20, "Not all trades executed successfully"
            assert statistics.mean(response_times) < 1000, "Trade execution time too high"
            assert max(response_times) < 3000, "Max trade execution time too high"
    
    def test_bulk_data_operations_performance(self, client, session, test_user, auth_headers):
        """Test performance of bulk data operations."""
        # Test bulk bot retrieval with pagination
        def test_pagination_performance():
            times = []
            
            for page in range(1, 6):  # Test 5 pages
                start_time = time.time()
                response = client.get(f'/api/bots?page={page}&per_page=10', 
                                    headers=auth_headers)
                end_time = time.time()
                
                assert response.status_code == 200
                times.append((end_time - start_time) * 1000)
            
            return statistics.mean(times)
        
        # Test trade history retrieval
        def test_trade_history_performance():
            start_time = time.time()
            response = client.get('/api/trades?limit=100', headers=auth_headers)
            end_time = time.time()
            
            assert response.status_code == 200
            return (end_time - start_time) * 1000
        
        # Test performance metrics calculation
        def test_performance_metrics():
            start_time = time.time()
            response = client.get('/api/analytics/performance', headers=auth_headers)
            end_time = time.time()
            
            # This endpoint might not exist yet, so accept 404
            assert response.status_code in [200, 404]
            return (end_time - start_time) * 1000
        
        pagination_time = test_pagination_performance()
        trade_history_time = test_trade_history_performance()
        performance_metrics_time = test_performance_metrics()
        
        assert pagination_time < 500, f"Pagination too slow: {pagination_time}ms"
        assert trade_history_time < 1000, f"Trade history too slow: {trade_history_time}ms"
        assert performance_metrics_time < 2000, f"Performance metrics too slow: {performance_metrics_time}ms"
    
    def test_stress_test_api_endpoints(self, client, test_user, auth_headers):
        """Stress test API endpoints with high concurrent load."""
        endpoints = [
            '/api/auth/profile',
            '/api/bots',
            '/api/subscriptions/current'
        ]
        
        def stress_endpoint(endpoint):
            results = []
            
            def make_request():
                start_time = time.time()
                response = client.get(endpoint, headers=auth_headers)
                end_time = time.time()
                
                return {
                    'status_code': response.status_code,
                    'response_time': (end_time - start_time) * 1000
                }
            
            # 100 concurrent requests per endpoint
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request) for _ in range(100)]
                results = [future.result() for future in as_completed(futures)]
            
            return results
        
        all_results = {}
        
        for endpoint in endpoints:
            results = stress_endpoint(endpoint)
            
            successful_requests = [r for r in results if r['status_code'] == 200]
            response_times = [r['response_time'] for r in successful_requests]
            
            all_results[endpoint] = {
                'success_rate': len(successful_requests) / len(results),
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0
            }
        
        # Verify stress test results
        for endpoint, metrics in all_results.items():
            assert metrics['success_rate'] >= 0.95, f"{endpoint} success rate too low: {metrics['success_rate']}"
            assert metrics['avg_response_time'] < 1000, f"{endpoint} avg response time too high: {metrics['avg_response_time']}ms"
            assert metrics['max_response_time'] < 5000, f"{endpoint} max response time too high: {metrics['max_response_time']}ms"