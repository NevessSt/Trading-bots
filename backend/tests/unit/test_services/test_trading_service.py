"""Unit tests for TradingService."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from services.trading_service import TradingService
from models.bot import Bot
from models.trade import Trade
from models.user import User


@pytest.mark.unit
class TestTradingService:
    """Test TradingService functionality."""
    
    def test_create_bot(self, session, test_user):
        """Test bot creation."""
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'grid_trading',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'config': {
                'grid_size': 10,
                'investment_amount': 1000,
                'grid_spacing': 0.5
            }
        }
        
        bot = TradingService.create_bot(test_user.id, bot_data)
        
        assert bot is not None
        assert bot.name == 'Test Bot'
        assert bot.strategy == 'grid_trading'
        assert bot.exchange == 'binance'
        assert bot.symbol == 'BTCUSDT'
        assert bot.user_id == test_user.id
        assert bot.status == 'stopped'
        assert bot.config['grid_size'] == 10
    
    def test_create_bot_invalid_data(self, session, test_user):
        """Test bot creation with invalid data."""
        # Missing required fields
        with pytest.raises(ValueError, match="Missing required field"):
            TradingService.create_bot(test_user.id, {})
        
        # Invalid strategy
        with pytest.raises(ValueError, match="Invalid strategy"):
            TradingService.create_bot(test_user.id, {
                'name': 'Test Bot',
                'strategy': 'invalid_strategy',
                'exchange': 'binance',
                'symbol': 'BTCUSDT'
            })
        
        # Invalid exchange
        with pytest.raises(ValueError, match="Invalid exchange"):
            TradingService.create_bot(test_user.id, {
                'name': 'Test Bot',
                'strategy': 'grid_trading',
                'exchange': 'invalid_exchange',
                'symbol': 'BTCUSDT'
            })
    
    def test_start_bot(self, session, test_bot, mock_exchange_api):
        """Test starting a bot."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.get_account_balance.return_value = {'USDT': 1000}
            mock_exchange_api.get_symbol_info.return_value = {
                'min_qty': 0.001,
                'max_qty': 1000,
                'step_size': 0.001
            }
            
            result = TradingService.start_bot(test_bot.id)
            
            assert result is True
            assert test_bot.status == 'running'
            assert test_bot.started_at is not None
    
    def test_start_bot_insufficient_balance(self, session, test_bot, mock_exchange_api):
        """Test starting bot with insufficient balance."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.get_account_balance.return_value = {'USDT': 10}  # Insufficient
            
            with pytest.raises(ValueError, match="Insufficient balance"):
                TradingService.start_bot(test_bot.id)
    
    def test_stop_bot(self, session, active_bot, mock_exchange_api):
        """Test stopping a bot."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.cancel_all_orders.return_value = True
            
            result = TradingService.stop_bot(active_bot.id)
            
            assert result is True
            assert active_bot.status == 'stopped'
            assert active_bot.stopped_at is not None
    
    def test_delete_bot(self, session, test_bot):
        """Test deleting a bot."""
        bot_id = test_bot.id
        
        result = TradingService.delete_bot(bot_id)
        
        assert result is True
        
        # Verify bot is deleted
        deleted_bot = session.query(Bot).filter_by(id=bot_id).first()
        assert deleted_bot is None
    
    def test_delete_running_bot(self, session, active_bot):
        """Test deleting a running bot should fail."""
        with pytest.raises(ValueError, match="Cannot delete running bot"):
            TradingService.delete_bot(active_bot.id)
    
    def test_update_bot_config(self, session, test_bot):
        """Test updating bot configuration."""
        new_config = {
            'grid_size': 20,
            'investment_amount': 2000,
            'grid_spacing': 1.0
        }
        
        result = TradingService.update_bot_config(test_bot.id, new_config)
        
        assert result is True
        assert test_bot.config['grid_size'] == 20
        assert test_bot.config['investment_amount'] == 2000
        assert test_bot.config['grid_spacing'] == 1.0
    
    def test_update_running_bot_config(self, session, active_bot):
        """Test updating running bot config should fail."""
        new_config = {'grid_size': 20}
        
        with pytest.raises(ValueError, match="Cannot update running bot"):
            TradingService.update_bot_config(active_bot.id, new_config)
    
    def test_get_bot_performance(self, session, test_bot, sample_trades):
        """Test getting bot performance metrics."""
        # Add trades to bot
        for trade in sample_trades:
            trade.bot_id = test_bot.id
        session.commit()
        
        performance = TradingService.get_bot_performance(test_bot.id)
        
        assert 'total_trades' in performance
        assert 'winning_trades' in performance
        assert 'losing_trades' in performance
        assert 'total_profit' in performance
        assert 'win_rate' in performance
        assert 'avg_profit_per_trade' in performance
        assert 'max_drawdown' in performance
        assert 'sharpe_ratio' in performance
    
    def test_get_bot_trades(self, session, test_bot, sample_trades):
        """Test getting bot trades."""
        # Add trades to bot
        for trade in sample_trades:
            trade.bot_id = test_bot.id
        session.commit()
        
        trades = TradingService.get_bot_trades(test_bot.id)
        
        assert len(trades) == len(sample_trades)
        assert all(trade.bot_id == test_bot.id for trade in trades)
    
    def test_get_bot_trades_with_pagination(self, session, test_bot):
        """Test getting bot trades with pagination."""
        # Create multiple trades
        for i in range(25):
            trade = Trade(
                bot_id=test_bot.id,
                symbol='BTCUSDT',
                side='buy',
                quantity=Decimal('0.001'),
                price=Decimal('50000'),
                status='filled',
                created_at=datetime.utcnow()
            )
            session.add(trade)
        session.commit()
        
        # Test pagination
        trades_page1 = TradingService.get_bot_trades(test_bot.id, page=1, per_page=10)
        trades_page2 = TradingService.get_bot_trades(test_bot.id, page=2, per_page=10)
        
        assert len(trades_page1) == 10
        assert len(trades_page2) == 10
        assert trades_page1[0].id != trades_page2[0].id
    
    def test_execute_trade(self, session, active_bot, mock_exchange_api):
        """Test executing a trade."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.place_order.return_value = {
                'order_id': 'test_order_123',
                'status': 'filled',
                'filled_qty': 0.001,
                'avg_price': 50000
            }
            
            trade_data = {
                'symbol': 'BTCUSDT',
                'side': 'buy',
                'quantity': 0.001,
                'order_type': 'market'
            }
            
            trade = TradingService.execute_trade(active_bot.id, trade_data)
            
            assert trade is not None
            assert trade.bot_id == active_bot.id
            assert trade.symbol == 'BTCUSDT'
            assert trade.side == 'buy'
            assert trade.quantity == Decimal('0.001')
            assert trade.status == 'filled'
            assert trade.exchange_order_id == 'test_order_123'
    
    def test_execute_trade_failed(self, session, active_bot, mock_exchange_api):
        """Test failed trade execution."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.place_order.side_effect = Exception("Order failed")
            
            trade_data = {
                'symbol': 'BTCUSDT',
                'side': 'buy',
                'quantity': 0.001,
                'order_type': 'market'
            }
            
            with pytest.raises(Exception, match="Order failed"):
                TradingService.execute_trade(active_bot.id, trade_data)
    
    def test_cancel_trade(self, session, test_trade, mock_exchange_api):
        """Test canceling a trade."""
        test_trade.status = 'pending'
        session.commit()
        
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.cancel_order.return_value = True
            
            result = TradingService.cancel_trade(test_trade.id)
            
            assert result is True
            assert test_trade.status == 'cancelled'
    
    def test_cancel_filled_trade(self, session, test_trade):
        """Test canceling a filled trade should fail."""
        test_trade.status = 'filled'
        session.commit()
        
        with pytest.raises(ValueError, match="Cannot cancel filled trade"):
            TradingService.cancel_trade(test_trade.id)
    
    def test_get_market_data(self, mock_exchange_api):
        """Test getting market data."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.get_ticker.return_value = {
                'symbol': 'BTCUSDT',
                'price': 50000,
                'change_24h': 2.5,
                'volume_24h': 1000000
            }
            
            market_data = TradingService.get_market_data('BTCUSDT')
            
            assert market_data['symbol'] == 'BTCUSDT'
            assert market_data['price'] == 50000
            assert market_data['change_24h'] == 2.5
    
    def test_get_candlestick_data(self, mock_exchange_api):
        """Test getting candlestick data."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.get_klines.return_value = [
                [1640995200000, 47000, 48000, 46500, 47500, 100],
                [1640998800000, 47500, 48500, 47000, 48000, 120]
            ]
            
            candles = TradingService.get_candlestick_data(
                'BTCUSDT', 
                '1h', 
                limit=100
            )
            
            assert len(candles) == 2
            assert candles[0]['open'] == 47000
            assert candles[0]['high'] == 48000
            assert candles[0]['low'] == 46500
            assert candles[0]['close'] == 47500
    
    def test_calculate_risk_metrics(self, session, test_bot, sample_trades):
        """Test risk metrics calculation."""
        # Add trades to bot
        for trade in sample_trades:
            trade.bot_id = test_bot.id
        session.commit()
        
        risk_metrics = TradingService.calculate_risk_metrics(test_bot.id)
        
        assert 'max_drawdown' in risk_metrics
        assert 'volatility' in risk_metrics
        assert 'sharpe_ratio' in risk_metrics
        assert 'sortino_ratio' in risk_metrics
        assert 'var_95' in risk_metrics  # Value at Risk
        assert 'beta' in risk_metrics
    
    def test_validate_trade_parameters(self, session, active_bot):
        """Test trade parameter validation."""
        # Valid parameters
        valid_params = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': 0.001,
            'order_type': 'market'
        }
        
        assert TradingService.validate_trade_parameters(valid_params) is True
        
        # Invalid side
        invalid_params = valid_params.copy()
        invalid_params['side'] = 'invalid'
        
        with pytest.raises(ValueError, match="Invalid side"):
            TradingService.validate_trade_parameters(invalid_params)
        
        # Invalid quantity
        invalid_params = valid_params.copy()
        invalid_params['quantity'] = -1
        
        with pytest.raises(ValueError, match="Invalid quantity"):
            TradingService.validate_trade_parameters(invalid_params)
    
    def test_check_risk_limits(self, session, active_bot):
        """Test risk limit checking."""
        # Set risk limits
        active_bot.config['max_daily_loss'] = 100
        active_bot.config['max_position_size'] = 1000
        session.commit()
        
        # Within limits
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': 0.001,
            'price': 50000
        }
        
        assert TradingService.check_risk_limits(active_bot.id, trade_data) is True
        
        # Exceeds position size limit
        large_trade = trade_data.copy()
        large_trade['quantity'] = 100  # Very large position
        
        assert TradingService.check_risk_limits(active_bot.id, large_trade) is False
    
    def test_update_bot_status(self, session, test_bot):
        """Test updating bot status."""
        TradingService.update_bot_status(test_bot.id, 'running')
        
        session.refresh(test_bot)
        assert test_bot.status == 'running'
        
        TradingService.update_bot_status(test_bot.id, 'error', 'Connection failed')
        
        session.refresh(test_bot)
        assert test_bot.status == 'error'
        assert test_bot.error_message == 'Connection failed'
    
    def test_get_bot_logs(self, session, test_bot):
        """Test getting bot logs."""
        # Add some log entries
        TradingService.log_bot_activity(test_bot.id, 'info', 'Bot started')
        TradingService.log_bot_activity(test_bot.id, 'warning', 'Low balance')
        TradingService.log_bot_activity(test_bot.id, 'error', 'API error')
        
        logs = TradingService.get_bot_logs(test_bot.id)
        
        assert len(logs) == 3
        assert logs[0]['level'] == 'info'
        assert logs[0]['message'] == 'Bot started'
    
    def test_clone_bot(self, session, test_bot):
        """Test cloning a bot."""
        cloned_bot = TradingService.clone_bot(test_bot.id, 'Cloned Bot')
        
        assert cloned_bot is not None
        assert cloned_bot.id != test_bot.id
        assert cloned_bot.name == 'Cloned Bot'
        assert cloned_bot.strategy == test_bot.strategy
        assert cloned_bot.exchange == test_bot.exchange
        assert cloned_bot.symbol == test_bot.symbol
        assert cloned_bot.config == test_bot.config
        assert cloned_bot.status == 'stopped'
    
    def test_backup_bot_config(self, session, test_bot):
        """Test backing up bot configuration."""
        backup = TradingService.backup_bot_config(test_bot.id)
        
        assert backup is not None
        assert 'bot_id' in backup
        assert 'name' in backup
        assert 'strategy' in backup
        assert 'config' in backup
        assert 'created_at' in backup
    
    def test_restore_bot_config(self, session, test_bot):
        """Test restoring bot configuration."""
        # Create backup
        backup = TradingService.backup_bot_config(test_bot.id)
        
        # Modify bot config
        test_bot.config['grid_size'] = 999
        session.commit()
        
        # Restore from backup
        result = TradingService.restore_bot_config(test_bot.id, backup)
        
        assert result is True
        session.refresh(test_bot)
        assert test_bot.config['grid_size'] != 999  # Should be restored
    
    def test_get_strategy_templates(self):
        """Test getting strategy templates."""
        templates = TradingService.get_strategy_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check template structure
        template = templates[0]
        assert 'name' in template
        assert 'description' in template
        assert 'parameters' in template
        assert 'risk_level' in template
    
    def test_validate_strategy_config(self):
        """Test strategy configuration validation."""
        # Valid grid trading config
        valid_config = {
            'grid_size': 10,
            'investment_amount': 1000,
            'grid_spacing': 0.5
        }
        
        assert TradingService.validate_strategy_config(
            'grid_trading', 
            valid_config
        ) is True
        
        # Invalid config (missing required parameter)
        invalid_config = {
            'grid_size': 10
            # Missing investment_amount and grid_spacing
        }
        
        with pytest.raises(ValueError, match="Missing required parameter"):
            TradingService.validate_strategy_config(
                'grid_trading', 
                invalid_config
            )
    
    def test_get_supported_exchanges(self):
        """Test getting supported exchanges."""
        exchanges = TradingService.get_supported_exchanges()
        
        assert isinstance(exchanges, list)
        assert 'binance' in exchanges
        assert 'coinbase' in exchanges
    
    def test_get_exchange_symbols(self, mock_exchange_api):
        """Test getting exchange symbols."""
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.get_symbols.return_value = [
                'BTCUSDT', 'ETHUSDT', 'ADAUSDT'
            ]
            
            symbols = TradingService.get_exchange_symbols('binance')
            
            assert isinstance(symbols, list)
            assert 'BTCUSDT' in symbols
            assert 'ETHUSDT' in symbols
    
    def test_calculate_position_size(self, session, active_bot):
        """Test position size calculation."""
        # Set bot config
        active_bot.config['investment_amount'] = 1000
        active_bot.config['risk_per_trade'] = 2  # 2%
        session.commit()
        
        position_size = TradingService.calculate_position_size(
            active_bot.id,
            entry_price=50000,
            stop_loss=49000
        )
        
        assert position_size > 0
        assert isinstance(position_size, float)
    
    def test_emergency_stop_all_bots(self, session, test_user, mock_exchange_api):
        """Test emergency stop for all user bots."""
        # Create multiple running bots
        bot1 = Bot(
            user_id=test_user.id,
            name='Bot 1',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT',
            status='running'
        )
        bot2 = Bot(
            user_id=test_user.id,
            name='Bot 2',
            strategy='dca',
            exchange='binance',
            symbol='ETHUSDT',
            status='running'
        )
        session.add_all([bot1, bot2])
        session.commit()
        
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_api.return_value = mock_exchange_api
            mock_exchange_api.cancel_all_orders.return_value = True
            
            result = TradingService.emergency_stop_all_bots(test_user.id)
            
            assert result is True
            session.refresh(bot1)
            session.refresh(bot2)
            assert bot1.status == 'stopped'
            assert bot2.status == 'stopped'