"""Performance and load tests for the trading bot system."""
import pytest
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from app import create_app, db
from app.models import User, Bot, Trade, APIKey
from app.services.trading_service import TradingService
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService


class TestDatabasePerformance:
    """Test database performance under load."""
    
    def test_user_creation_performance(self, app_context):
        """Test user creation performance."""
        start_time = time.time()
        users_created = 0
        
        for i in range(100):
            user = User(
                username=f'perfuser_{i}',
                email=f'perfuser_{i}@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            users_created += 1
        
        db.session.commit()
        end_time = time.time()
        
        duration = end_time - start_time
        users_per_second = users_created / duration
        
        # Should be able to create at least 50 users per second
        assert users_per_second > 50
        assert duration < 2.0  # Should complete within 2 seconds
    
    def test_bot_query_performance(self, app_context):
        """Test bot query performance with large dataset."""
        # Create test user
        user = User(
            username='perfuser',
            email='perfuser@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create many bots
        bots = []
        for i in range(1000):
            bot = Bot(
                name=f'PerfBot_{i}',
                user_id=user.id,
                strategy='grid',
                trading_pair='BTCUSDT',
                config={'grid_size': 10}
            )
            bots.append(bot)
        
        db.session.add_all(bots)
        db.session.commit()
        
        # Test query performance
        start_time = time.time()
        
        # Query all user bots
        user_bots = Bot.query.filter_by(user_id=user.id).all()
        
        # Query active bots
        active_bots = Bot.query.filter_by(user_id=user.id, is_active=True).all()
        
        # Query bots by strategy
        grid_bots = Bot.query.filter_by(user_id=user.id, strategy='grid').all()
        
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert len(user_bots) == 1000
        assert duration < 0.5  # Should complete within 500ms
    
    def test_trade_insertion_performance(self, app_context, sample_user, sample_bot):
        """Test trade insertion performance."""
        trades = []
        
        # Prepare trade data
        for i in range(1000):
            trade = Trade(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='buy' if i % 2 == 0 else 'sell',
                quantity=Decimal('0.001'),
                price=Decimal(f'{50000 + i}'),
                total_value=Decimal(f'{50 + i * 0.001}'),
                fees=Decimal('0.05'),
                profit_loss=Decimal(f'{i * 0.1}')
            )
            trades.append(trade)
        
        # Test bulk insertion performance
        start_time = time.time()
        db.session.add_all(trades)
        db.session.commit()
        end_time = time.time()
        
        duration = end_time - start_time
        trades_per_second = 1000 / duration
        
        # Should be able to insert at least 500 trades per second
        assert trades_per_second > 500
        assert duration < 2.0
    
    def test_complex_query_performance(self, app_context, sample_user, sample_bot):
        """Test performance of complex queries."""
        # Create test data
        trades = []
        for i in range(500):
            trade = Trade(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='buy' if i % 2 == 0 else 'sell',
                quantity=Decimal('0.001'),
                price=Decimal(f'{50000 + i}'),
                total_value=Decimal(f'{50 + i * 0.001}'),
                profit_loss=Decimal(f'{(i % 10) - 5}'),  # Mix of profits and losses
                executed_at=datetime.utcnow() - timedelta(days=i % 30)
            )
            trades.append(trade)
        
        db.session.add_all(trades)
        db.session.commit()
        
        start_time = time.time()
        
        # Complex aggregation query
        from sqlalchemy import func
        
        result = db.session.query(
            func.count(Trade.id).label('total_trades'),
            func.sum(Trade.profit_loss).label('total_pnl'),
            func.avg(Trade.profit_loss).label('avg_pnl'),
            func.max(Trade.profit_loss).label('max_profit'),
            func.min(Trade.profit_loss).label('max_loss')
        ).filter(
            Trade.user_id == sample_user.id,
            Trade.executed_at >= datetime.utcnow() - timedelta(days=30)
        ).first()
        
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert result.total_trades > 0
        assert duration < 0.1  # Should complete within 100ms


class TestAPIPerformance:
    """Test API endpoint performance."""
    
    def test_authentication_performance(self, client):
        """Test authentication endpoint performance."""
        # Create test user
        user_data = {
            'username': 'perfuser',
            'email': 'perfuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        # Register user
        client.post('/api/auth/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        login_data = {
            'username': 'perfuser',
            'password': 'SecurePass123!'
        }
        
        # Test login performance
        response_times = []
        
        for _ in range(50):
            start_time = time.time()
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            
            assert response.status_code == 200
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Average response time should be under 100ms
        assert avg_response_time < 0.1
        # Maximum response time should be under 500ms
        assert max_response_time < 0.5
    
    def test_bot_listing_performance(self, client, auth_headers, sample_user):
        """Test bot listing endpoint performance with many bots."""
        # Create many bots
        bots = []
        for i in range(100):
            bot = Bot(
                name=f'PerfBot_{i}',
                user_id=sample_user.id,
                strategy='grid',
                trading_pair='BTCUSDT',
                config={'grid_size': 10}
            )
            bots.append(bot)
        
        db.session.add_all(bots)
        db.session.commit()
        
        # Test listing performance
        response_times = []
        
        for _ in range(20):
            start_time = time.time()
            
            response = client.get('/api/bots', headers=auth_headers)
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['bots']) == 100
        
        avg_response_time = statistics.mean(response_times)
        
        # Should handle 100 bots listing in under 200ms on average
        assert avg_response_time < 0.2
    
    def test_trade_history_performance(self, client, auth_headers, sample_user, sample_bot):
        """Test trade history endpoint performance with large dataset."""
        # Create many trades
        trades = []
        for i in range(1000):
            trade = Trade(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='buy' if i % 2 == 0 else 'sell',
                quantity=Decimal('0.001'),
                price=Decimal(f'{50000 + i}'),
                total_value=Decimal(f'{50 + i * 0.001}'),
                executed_at=datetime.utcnow() - timedelta(minutes=i)
            )
            trades.append(trade)
        
        db.session.add_all(trades)
        db.session.commit()
        
        # Test paginated trade history performance
        start_time = time.time()
        
        response = client.get('/api/trading/history?limit=50&page=1', headers=auth_headers)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['trades']) == 50
        
        # Should return paginated results in under 100ms
        assert duration < 0.1


class TestConcurrencyPerformance:
    """Test system performance under concurrent load."""
    
    def test_concurrent_user_registration(self, client):
        """Test concurrent user registration performance."""
        def register_user(user_id):
            user_data = {
                'username': f'concuser_{user_id}',
                'email': f'concuser_{user_id}@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            }
            
            start_time = time.time()
            response = client.post('/api/auth/register',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'duration': end_time - start_time,
                'user_id': user_id
            }
        
        # Test with 20 concurrent registrations
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(register_user, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All registrations should succeed
        successful_registrations = [r for r in results if r['status_code'] == 201]
        assert len(successful_registrations) == 20
        
        # Average response time should be reasonable
        avg_duration = statistics.mean([r['duration'] for r in results])
        assert avg_duration < 1.0  # Under 1 second average
    
    def test_concurrent_bot_operations(self, client, auth_headers, sample_user, sample_api_key):
        """Test concurrent bot operations performance."""
        def create_bot(bot_id):
            bot_data = {
                'name': f'ConcBot_{bot_id}',
                'strategy': 'grid',
                'trading_pair': 'BTCUSDT',
                'api_key_id': sample_api_key.id,
                'config': {
                    'grid_size': 10,
                    'price_range': [45000, 55000],
                    'investment_amount': 1000
                }
            }
            
            start_time = time.time()
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'duration': end_time - start_time,
                'bot_id': bot_id
            }
        
        # Test with 10 concurrent bot creations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_bot, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All bot creations should succeed
        successful_creations = [r for r in results if r['status_code'] == 201]
        assert len(successful_creations) == 10
        
        # Average response time should be reasonable
        avg_duration = statistics.mean([r['duration'] for r in results])
        assert avg_duration < 0.5  # Under 500ms average
    
    def test_concurrent_trade_execution(self, client, auth_headers, sample_bot):
        """Test concurrent trade execution performance."""
        def execute_trade(trade_id):
            trade_data = {
                'bot_id': sample_bot.id,
                'trading_pair': 'BTCUSDT',
                'side': 'buy' if trade_id % 2 == 0 else 'sell',
                'quantity': '0.001',
                'order_type': 'market'
            }
            
            with patch('app.services.trading_service.execute_trade') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'trade_id': f'trade_{trade_id}',
                    'executed_price': 50000,
                    'executed_quantity': 0.001,
                    'fees': 0.5
                }
                
                start_time = time.time()
                response = client.post('/api/trading/execute',
                                     data=json.dumps(trade_data),
                                     content_type='application/json',
                                     headers=auth_headers)
                end_time = time.time()
                
                return {
                    'status_code': response.status_code,
                    'duration': end_time - start_time,
                    'trade_id': trade_id
                }
        
        # Test with 15 concurrent trade executions
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(execute_trade, i) for i in range(15)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All trades should execute successfully
        successful_trades = [r for r in results if r['status_code'] == 200]
        assert len(successful_trades) == 15
        
        # Average response time should be reasonable
        avg_duration = statistics.mean([r['duration'] for r in results])
        assert avg_duration < 0.3  # Under 300ms average


class TestServicePerformance:
    """Test service layer performance."""
    
    def test_trading_service_performance(self, app_context, sample_user, sample_bot, sample_api_key):
        """Test trading service performance."""
        trading_service = TradingService()
        
        # Test bot management performance
        start_time = time.time()
        
        for _ in range(100):
            # Simulate bot status checks
            bot_status = trading_service.get_bot_status(sample_bot.id)
            
            # Simulate performance calculations
            performance = trading_service.calculate_bot_performance(sample_bot.id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle 100 operations in under 1 second
        assert duration < 1.0
    
    def test_market_service_performance(self, app_context):
        """Test market service performance."""
        market_service = MarketService()
        
        with patch('app.services.market_service.MarketService.fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'symbol': 'BTCUSDT',
                'price': 50000,
                'change_24h': 2.5,
                'volume_24h': 1000000
            }
            
            # Test market data retrieval performance
            start_time = time.time()
            
            for _ in range(50):
                market_data = market_service.get_market_data('BTCUSDT')
                assert market_data['symbol'] == 'BTCUSDT'
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should handle 50 market data requests in under 500ms
            assert duration < 0.5
    
    def test_portfolio_service_performance(self, app_context, sample_user, sample_trades):
        """Test portfolio service performance."""
        portfolio_service = PortfolioService()
        
        # Test portfolio calculation performance
        start_time = time.time()
        
        for _ in range(20):
            portfolio_summary = portfolio_service.get_portfolio_summary(sample_user.id)
            assert 'total_value' in portfolio_summary
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle 20 portfolio calculations in under 200ms
        assert duration < 0.2


class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    def test_memory_usage_during_bulk_operations(self, app_context, sample_user):
        """Test memory usage during bulk database operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of objects
        bots = []
        for i in range(1000):
            bot = Bot(
                name=f'MemBot_{i}',
                user_id=sample_user.id,
                strategy='grid',
                trading_pair='BTCUSDT',
                config={'grid_size': 10}
            )
            bots.append(bot)
        
        db.session.add_all(bots)
        db.session.commit()
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable (under 100MB for 1000 bots)
        assert memory_increase < 100
        
        # Clean up
        for bot in bots:
            db.session.delete(bot)
        db.session.commit()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory should be released after cleanup
        assert final_memory < peak_memory
    
    def test_query_result_memory_efficiency(self, app_context, sample_user, sample_bot):
        """Test memory efficiency of query results."""
        import sys
        
        # Create test trades
        trades = []
        for i in range(1000):
            trade = Trade(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='buy',
                quantity=Decimal('0.001'),
                price=Decimal(f'{50000 + i}'),
                total_value=Decimal(f'{50 + i * 0.001}')
            )
            trades.append(trade)
        
        db.session.add_all(trades)
        db.session.commit()
        
        # Test memory usage of query results
        query_result = Trade.query.filter_by(user_id=sample_user.id).all()
        result_size = sys.getsizeof(query_result)
        
        # Result size should be reasonable
        assert len(query_result) == 1000
        assert result_size < 1024 * 1024  # Under 1MB
        
        # Test pagination memory efficiency
        paginated_result = Trade.query.filter_by(user_id=sample_user.id).limit(50).all()
        paginated_size = sys.getsizeof(paginated_result)
        
        # Paginated result should be much smaller
        assert len(paginated_result) == 50
        assert paginated_size < result_size / 10


class TestScalabilityPerformance:
    """Test system scalability performance."""
    
    def test_user_scalability(self, app_context):
        """Test system performance with increasing number of users."""
        user_counts = [10, 50, 100, 200]
        creation_times = []
        
        for count in user_counts:
            start_time = time.time()
            
            users = []
            for i in range(count):
                user = User(
                    username=f'scaleuser_{count}_{i}',
                    email=f'scaleuser_{count}_{i}@example.com',
                    password_hash='hashed_password'
                )
                users.append(user)
            
            db.session.add_all(users)
            db.session.commit()
            
            end_time = time.time()
            creation_times.append(end_time - start_time)
            
            # Clean up
            for user in users:
                db.session.delete(user)
            db.session.commit()
        
        # Performance should scale reasonably
        # Time per user should not increase dramatically
        time_per_user = [creation_times[i] / user_counts[i] for i in range(len(user_counts))]
        
        # Time per user should remain relatively stable
        assert max(time_per_user) / min(time_per_user) < 3  # Less than 3x difference
    
    def test_bot_scalability_per_user(self, app_context, sample_user):
        """Test bot performance scaling per user."""
        bot_counts = [10, 50, 100]
        query_times = []
        
        # Create bots incrementally and test query performance
        all_bots = []
        
        for count in bot_counts:
            # Add more bots to reach the target count
            current_count = len(all_bots)
            new_bots = []
            
            for i in range(current_count, count):
                bot = Bot(
                    name=f'ScaleBot_{i}',
                    user_id=sample_user.id,
                    strategy='grid',
                    trading_pair='BTCUSDT',
                    config={'grid_size': 10}
                )
                new_bots.append(bot)
                all_bots.append(bot)
            
            db.session.add_all(new_bots)
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            user_bots = Bot.query.filter_by(user_id=sample_user.id).all()
            end_time = time.time()
            
            query_times.append(end_time - start_time)
            assert len(user_bots) == count
        
        # Query time should scale reasonably
        # Should not increase exponentially
        assert query_times[-1] / query_times[0] < 5  # Less than 5x increase for 10x data
    
    def test_trade_volume_scalability(self, app_context, sample_user, sample_bot):
        """Test system performance with high trade volumes."""
        trade_volumes = [100, 500, 1000]
        insertion_times = []
        
        for volume in trade_volumes:
            trades = []
            for i in range(volume):
                trade = Trade(
                    bot_id=sample_bot.id,
                    user_id=sample_user.id,
                    trading_pair='BTCUSDT',
                    side='buy' if i % 2 == 0 else 'sell',
                    quantity=Decimal('0.001'),
                    price=Decimal(f'{50000 + i}'),
                    total_value=Decimal(f'{50 + i * 0.001}')
                )
                trades.append(trade)
            
            start_time = time.time()
            db.session.add_all(trades)
            db.session.commit()
            end_time = time.time()
            
            insertion_times.append(end_time - start_time)
            
            # Clean up
            for trade in trades:
                db.session.delete(trade)
            db.session.commit()
        
        # Insertion time should scale linearly or better
        trades_per_second = [trade_volumes[i] / insertion_times[i] for i in range(len(trade_volumes))]
        
        # Throughput should remain relatively stable
        assert min(trades_per_second) > 100  # At least 100 trades per second
        assert max(trades_per_second) / min(trades_per_second) < 2  # Less than 2x variation


class TestCachePerformance:
    """Test caching performance improvements."""
    
    def test_market_data_caching_performance(self, app_context):
        """Test market data caching performance."""
        market_service = MarketService()
        
        with patch('app.services.market_service.MarketService.fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'symbol': 'BTCUSDT',
                'price': 50000,
                'change_24h': 2.5,
                'volume_24h': 1000000
            }
            
            # First call (cache miss)
            start_time = time.time()
            data1 = market_service.get_market_data('BTCUSDT')
            first_call_time = time.time() - start_time
            
            # Second call (cache hit)
            start_time = time.time()
            data2 = market_service.get_market_data('BTCUSDT')
            second_call_time = time.time() - start_time
            
            # Cached call should be significantly faster
            assert second_call_time < first_call_time / 2
            assert data1 == data2
            
            # Mock should only be called once (first time)
            assert mock_fetch.call_count == 1
    
    def test_user_session_caching_performance(self, client, auth_headers):
        """Test user session caching performance."""
        response_times = []
        
        # Make multiple requests with same auth token
        for _ in range(10):
            start_time = time.time()
            response = client.get('/api/user/profile', headers=auth_headers)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            assert response.status_code == 200
        
        # Response times should be consistently fast (cached user data)
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 0.05  # Under 50ms average
        assert max_response_time < 0.1   # Under 100ms maximum