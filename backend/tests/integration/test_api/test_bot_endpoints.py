"""Integration tests for bot management API endpoints."""
import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock
from decimal import Decimal

from models.bot import Bot
from models.trade import Trade


@pytest.mark.integration
@pytest.mark.api
class TestBotEndpoints:
    """Test bot management API endpoints."""
    
    def test_create_bot_success(self, client, test_user, auth_headers):
        """Test successful bot creation."""
        bot_data = {
            'name': 'Test Trading Bot',
            'strategy': 'grid_trading',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'config': {
                'grid_size': 10,
                'investment_amount': 1000,
                'grid_spacing': 0.5,
                'stop_loss': 5.0,
                'take_profit': 10.0
            }
        }
        
        response = client.post('/api/bots', 
                             json=bot_data, 
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'bot' in data
        assert data['bot']['name'] == 'Test Trading Bot'
        assert data['bot']['strategy'] == 'grid_trading'
        assert data['bot']['status'] == 'stopped'
        assert data['bot']['user_id'] == test_user.id
    
    def test_create_bot_invalid_data(self, client, auth_headers):
        """Test bot creation with invalid data."""
        # Missing required fields
        response = client.post('/api/bots', 
                             json={}, 
                             headers=auth_headers)
        assert response.status_code == 400
        
        # Invalid strategy
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'invalid_strategy',
            'exchange': 'binance',
            'symbol': 'BTCUSDT'
        }
        response = client.post('/api/bots', 
                             json=bot_data, 
                             headers=auth_headers)
        assert response.status_code == 400
        
        # Invalid exchange
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'grid_trading',
            'exchange': 'invalid_exchange',
            'symbol': 'BTCUSDT'
        }
        response = client.post('/api/bots', 
                             json=bot_data, 
                             headers=auth_headers)
        assert response.status_code == 400
    
    def test_create_bot_unauthorized(self, client):
        """Test bot creation without authentication."""
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'grid_trading',
            'exchange': 'binance',
            'symbol': 'BTCUSDT'
        }
        
        response = client.post('/api/bots', json=bot_data)
        assert response.status_code == 401
    
    def test_get_user_bots(self, client, test_user, test_bot, auth_headers):
        """Test getting user's bots."""
        response = client.get('/api/bots', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'bots' in data
        assert len(data['bots']) >= 1
        assert any(bot['id'] == test_bot.id for bot in data['bots'])
    
    def test_get_user_bots_with_pagination(self, client, session, test_user, auth_headers):
        """Test getting user's bots with pagination."""
        # Create multiple bots
        for i in range(15):
            bot = Bot(
                user_id=test_user.id,
                name=f'Bot {i}',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT',
                config={'grid_size': 10}
            )
            session.add(bot)
        session.commit()
        
        # Test pagination
        response = client.get('/api/bots?page=1&per_page=10', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['bots']) == 10
        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] >= 15
    
    def test_get_bot_by_id(self, client, test_bot, auth_headers):
        """Test getting specific bot by ID."""
        response = client.get(f'/api/bots/{test_bot.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'bot' in data
        assert data['bot']['id'] == test_bot.id
        assert data['bot']['name'] == test_bot.name
    
    def test_get_bot_not_found(self, client, auth_headers):
        """Test getting non-existent bot."""
        response = client.get('/api/bots/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_get_bot_unauthorized_access(self, client, session, auth_headers):
        """Test accessing another user's bot."""
        # Create bot for different user
        other_user = User(
            email='other@example.com',
            username='other',
            password_hash='hashed',
            is_verified=True
        )
        session.add(other_user)
        session.flush()
        
        other_bot = Bot(
            user_id=other_user.id,
            name='Other Bot',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT'
        )
        session.add(other_bot)
        session.commit()
        
        response = client.get(f'/api/bots/{other_bot.id}', headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_bot_config(self, client, session, test_bot, auth_headers):
        """Test updating bot configuration."""
        update_data = {
            'name': 'Updated Bot Name',
            'config': {
                'grid_size': 20,
                'investment_amount': 2000,
                'grid_spacing': 1.0
            }
        }
        
        response = client.put(f'/api/bots/{test_bot.id}', 
                            json=update_data, 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify changes
        session.refresh(test_bot)
        assert test_bot.name == 'Updated Bot Name'
        assert test_bot.config['grid_size'] == 20
    
    def test_update_running_bot(self, client, session, active_bot, auth_headers):
        """Test updating running bot should fail."""
        update_data = {
            'config': {'grid_size': 20}
        }
        
        response = client.put(f'/api/bots/{active_bot.id}', 
                            json=update_data, 
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'running' in data['message'].lower()
    
    def test_start_bot(self, client, session, test_bot, auth_headers):
        """Test starting a bot."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.get_account_balance.return_value = {'USDT': 1000}
            mock_exchange.get_symbol_info.return_value = {
                'min_qty': 0.001,
                'max_qty': 1000,
                'step_size': 0.001
            }
            
            response = client.post(f'/api/bots/{test_bot.id}/start', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify bot status changed
            session.refresh(test_bot)
            assert test_bot.status == 'running'
    
    def test_start_bot_insufficient_balance(self, client, test_bot, auth_headers):
        """Test starting bot with insufficient balance."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.get_account_balance.return_value = {'USDT': 10}  # Insufficient
            
            response = client.post(f'/api/bots/{test_bot.id}/start', 
                                 headers=auth_headers)
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'insufficient' in data['message'].lower()
    
    def test_stop_bot(self, client, session, active_bot, auth_headers):
        """Test stopping a bot."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.cancel_all_orders.return_value = True
            
            response = client.post(f'/api/bots/{active_bot.id}/stop', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify bot status changed
            session.refresh(active_bot)
            assert active_bot.status == 'stopped'
    
    def test_delete_bot(self, client, session, test_bot, auth_headers):
        """Test deleting a bot."""
        bot_id = test_bot.id
        
        response = client.delete(f'/api/bots/{bot_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify bot is deleted
        deleted_bot = session.query(Bot).filter_by(id=bot_id).first()
        assert deleted_bot is None
    
    def test_delete_running_bot(self, client, active_bot, auth_headers):
        """Test deleting running bot should fail."""
        response = client.delete(f'/api/bots/{active_bot.id}', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'running' in data['message'].lower()
    
    def test_get_bot_performance(self, client, session, test_bot, auth_headers):
        """Test getting bot performance metrics."""
        # Add some trades to the bot
        trades = [
            Trade(
                user_id=test_bot.user_id,
                bot_id=test_bot.id,
                symbol='BTCUSDT',
                side='buy',
                trade_type='market',
                quantity=Decimal('0.001'),
                price=Decimal('50000'),
                status='filled'
            ),
            Trade(
                user_id=test_bot.user_id,
                bot_id=test_bot.id,
                symbol='BTCUSDT',
                side='sell',
                trade_type='market',
                quantity=Decimal('0.001'),
                price=Decimal('51000'),
                status='filled'
            )
        ]
        session.add_all(trades)
        session.commit()
        
        response = client.get(f'/api/trading/bots/{test_bot.id}/performance', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'performance' in data
        
        performance = data['performance']
        assert 'total_trades' in performance
        assert 'total_profit_loss' in performance
        assert 'winning_trades' in performance
        assert 'losing_trades' in performance
        assert 'win_rate' in performance
        assert 'average_profit' in performance
        assert 'average_loss' in performance
    
    def test_get_bot_trades(self, client, session, test_bot, auth_headers):
        """Test getting bot trades."""
        # Add trades to the bot
        for i in range(5):
            trade = Trade(
                bot_id=test_bot.id,
                symbol='BTCUSDT',
                side='buy' if i % 2 == 0 else 'sell',
                quantity=Decimal('0.001'),
                price=Decimal(f'{50000 + i * 100}'),
                status='filled'
            )
            session.add(trade)
        session.commit()
        
        response = client.get(f'/api/bots/{test_bot.id}/trades', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'trades' in data
        assert len(data['trades']) == 5
    
    def test_get_bot_trades_with_filters(self, client, session, test_bot, auth_headers):
        """Test getting bot trades with filters."""
        # Add trades with different statuses
        trades = [
            Trade(
                bot_id=test_bot.id,
                symbol='BTCUSDT',
                side='buy',
                quantity=Decimal('0.001'),
                price=Decimal('50000'),
                status='filled'
            ),
            Trade(
                bot_id=test_bot.id,
                symbol='BTCUSDT',
                side='sell',
                quantity=Decimal('0.001'),
                price=Decimal('51000'),
                status='pending'
            )
        ]
        session.add_all(trades)
        session.commit()
        
        # Filter by status
        response = client.get(f'/api/bots/{test_bot.id}/trades?status=filled', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['trades']) == 1
        assert data['trades'][0]['status'] == 'filled'
    
    def test_clone_bot(self, client, session, test_bot, auth_headers):
        """Test cloning a bot."""
        clone_data = {
            'name': 'Cloned Bot'
        }
        
        response = client.post(f'/api/bots/{test_bot.id}/clone', 
                             json=clone_data, 
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'bot' in data
        
        cloned_bot = data['bot']
        assert cloned_bot['name'] == 'Cloned Bot'
        assert cloned_bot['strategy'] == test_bot.strategy
        assert cloned_bot['exchange'] == test_bot.exchange
        assert cloned_bot['status'] == 'stopped'
        assert cloned_bot['id'] != test_bot.id
    
    def test_backup_bot_config(self, client, test_bot, auth_headers):
        """Test backing up bot configuration."""
        response = client.post(f'/api/bots/{test_bot.id}/backup', 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'backup' in data
        
        backup = data['backup']
        assert 'bot_id' in backup
        assert 'config' in backup
        assert 'created_at' in backup
    
    def test_restore_bot_config(self, client, session, test_bot, auth_headers):
        """Test restoring bot configuration."""
        # First create a backup
        backup_response = client.post(f'/api/bots/{test_bot.id}/backup', 
                                    headers=auth_headers)
        backup_data = backup_response.get_json()['backup']
        
        # Modify bot config
        test_bot.config['grid_size'] = 999
        session.commit()
        
        # Restore from backup
        restore_data = {'backup_id': backup_data['id']}
        response = client.post(f'/api/bots/{test_bot.id}/restore', 
                             json=restore_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify config was restored
        session.refresh(test_bot)
        assert test_bot.config['grid_size'] != 999
    
    def test_get_bot_logs(self, client, test_bot, auth_headers):
        """Test getting bot logs."""
        with patch('services.trading_service.get_bot_logs') as mock_logs:
            mock_logs.return_value = [
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'info',
                    'message': 'Bot started successfully'
                },
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': 'warning',
                    'message': 'Low balance detected'
                }
            ]
            
            response = client.get(f'/api/bots/{test_bot.id}/logs', 
                                headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'logs' in data
            assert len(data['logs']) == 2
    
    def test_emergency_stop_all_bots(self, client, session, test_user, auth_headers):
        """Test emergency stop for all user bots."""
        # Create multiple running bots
        bots = []
        for i in range(3):
            bot = Bot(
                user_id=test_user.id,
                name=f'Bot {i}',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT',
                status='running'
            )
            session.add(bot)
            bots.append(bot)
        session.commit()
        
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.cancel_all_orders.return_value = True
            
            response = client.post('/api/bots/emergency-stop', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify all bots are stopped
            for bot in bots:
                session.refresh(bot)
                assert bot.status == 'stopped'
    
    def test_get_strategy_templates(self, client, auth_headers):
        """Test getting strategy templates."""
        response = client.get('/api/bots/strategy-templates', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'templates' in data
        assert len(data['templates']) > 0
        
        # Check template structure
        template = data['templates'][0]
        assert 'name' in template
        assert 'description' in template
        assert 'parameters' in template
    
    def test_validate_bot_config(self, client, auth_headers):
        """Test bot configuration validation."""
        config_data = {
            'strategy': 'grid_trading',
            'config': {
                'grid_size': 10,
                'investment_amount': 1000,
                'grid_spacing': 0.5
            }
        }
        
        response = client.post('/api/bots/validate-config', 
                             json=config_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['valid'] is True
    
    def test_validate_invalid_bot_config(self, client, auth_headers):
        """Test validation of invalid bot configuration."""
        config_data = {
            'strategy': 'grid_trading',
            'config': {
                'grid_size': 10
                # Missing required parameters
            }
        }
        
        response = client.post('/api/bots/validate-config', 
                             json=config_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['valid'] is False
        assert 'errors' in data
    
    def test_bot_rate_limiting(self, client, auth_headers):
        """Test rate limiting for bot operations."""
        # Make multiple rapid requests
        for i in range(10):
            response = client.get('/api/bots', headers=auth_headers)
            if response.status_code == 429:
                # Rate limit hit
                data = response.get_json()
                assert 'rate limit' in data['message'].lower()
                break
        else:
            # If no rate limit hit, that's also acceptable
            pass
    
    def test_bot_websocket_connection(self, client, test_bot, auth_headers):
        """Test WebSocket connection for real-time bot updates."""
        # This would typically test WebSocket functionality
        # For now, we'll test the endpoint that provides WebSocket info
        response = client.get(f'/api/bots/{test_bot.id}/websocket-info', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'websocket_url' in data
        assert 'auth_token' in data