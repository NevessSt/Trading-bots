"""Unit tests for utility functions."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from utils.validators import (
    validate_email,
    validate_password,
    validate_trading_pair,
    validate_decimal_amount,
    validate_api_key_format
)
from utils.formatters import (
    format_currency,
    format_percentage,
    format_datetime,
    format_trade_data
)
from utils.security import (
    generate_api_key,
    hash_api_secret,
    verify_api_secret,
    encrypt_sensitive_data,
    decrypt_sensitive_data
)
from utils.calculations import (
    calculate_profit_loss,
    calculate_win_rate,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_portfolio_value
)


class TestValidators:
    """Test validation utility functions."""
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            'user@example.com',
            'test.email+tag@domain.co.uk',
            'user123@test-domain.org',
            'firstname.lastname@company.com'
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user..double.dot@domain.com',
            'user@domain',
            ''
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False
    
    def test_validate_password_valid(self):
        """Test password validation with valid passwords."""
        valid_passwords = [
            'SecurePass123!',
            'MyP@ssw0rd',
            'Complex1ty!',
            'Str0ng#Password'
        ]
        
        for password in valid_passwords:
            result = validate_password(password)
            assert result['valid'] is True
            assert len(result['errors']) == 0
    
    def test_validate_password_invalid(self):
        """Test password validation with invalid passwords."""
        invalid_cases = [
            ('123', ['too_short', 'no_uppercase', 'no_lowercase', 'no_special']),
            ('password', ['no_uppercase', 'no_digit', 'no_special']),
            ('PASSWORD', ['no_lowercase', 'no_digit', 'no_special']),
            ('Password123', ['no_special']),
            ('Pass!', ['too_short', 'no_digit'])
        ]
        
        for password, expected_errors in invalid_cases:
            result = validate_password(password)
            assert result['valid'] is False
            for error in expected_errors:
                assert error in result['errors']
    
    def test_validate_trading_pair_valid(self):
        """Test trading pair validation with valid pairs."""
        valid_pairs = [
            'BTCUSDT',
            'ETHBTC',
            'ADAUSDT',
            'DOTETH',
            'LINKUSD'
        ]
        
        for pair in valid_pairs:
            assert validate_trading_pair(pair) is True
    
    def test_validate_trading_pair_invalid(self):
        """Test trading pair validation with invalid pairs."""
        invalid_pairs = [
            'BTC',
            'BTCUSDTETH',
            'btcusdt',
            '123USDT',
            'BTC-USDT',
            ''
        ]
        
        for pair in invalid_pairs:
            assert validate_trading_pair(pair) is False
    
    def test_validate_decimal_amount_valid(self):
        """Test decimal amount validation with valid amounts."""
        valid_amounts = [
            '100.50',
            '0.001',
            '1000000',
            '0.00000001'
        ]
        
        for amount in valid_amounts:
            result = validate_decimal_amount(amount)
            assert result['valid'] is True
            assert isinstance(result['decimal'], Decimal)
    
    def test_validate_decimal_amount_invalid(self):
        """Test decimal amount validation with invalid amounts."""
        invalid_amounts = [
            'abc',
            '-100',
            '0',
            '',
            '100.123.456'
        ]
        
        for amount in invalid_amounts:
            result = validate_decimal_amount(amount)
            assert result['valid'] is False
    
    def test_validate_api_key_format_valid(self):
        """Test API key format validation with valid keys."""
        valid_keys = [
            'abcd1234efgh5678ijkl9012mnop3456',
            'ABCD1234EFGH5678IJKL9012MNOP3456',
            'AbCd1234EfGh5678IjKl9012MnOp3456'
        ]
        
        for key in valid_keys:
            assert validate_api_key_format(key) is True
    
    def test_validate_api_key_format_invalid(self):
        """Test API key format validation with invalid keys."""
        invalid_keys = [
            'short',
            'toolongapikeythatexceedsmaximumlength1234567890',
            'invalid-chars!@#',
            '',
            '123'
        ]
        
        for key in invalid_keys:
            assert validate_api_key_format(key) is False


class TestFormatters:
    """Test formatting utility functions."""
    
    def test_format_currency(self):
        """Test currency formatting."""
        test_cases = [
            (Decimal('100.50'), 'USD', '$100.50'),
            (Decimal('1000'), 'EUR', '€1,000.00'),
            (Decimal('0.001'), 'BTC', '0.00100000 BTC'),
            (Decimal('1234567.89'), 'USD', '$1,234,567.89')
        ]
        
        for amount, currency, expected in test_cases:
            result = format_currency(amount, currency)
            assert expected in result
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        test_cases = [
            (0.1234, '12.34%'),
            (0.05, '5.00%'),
            (-0.0789, '-7.89%'),
            (1.5, '150.00%')
        ]
        
        for value, expected in test_cases:
            result = format_percentage(value)
            assert result == expected
    
    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2023, 12, 25, 15, 30, 45)
        
        # Test different formats
        assert '2023-12-25' in format_datetime(dt, 'date')
        assert '15:30:45' in format_datetime(dt, 'time')
        assert '2023-12-25 15:30:45' in format_datetime(dt, 'datetime')
    
    def test_format_trade_data(self):
        """Test trade data formatting."""
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': Decimal('0.001'),
            'price': Decimal('50000.00'),
            'timestamp': datetime.utcnow()
        }
        
        formatted = format_trade_data(trade_data)
        
        assert formatted['symbol'] == 'BTCUSDT'
        assert formatted['side'] == 'BUY'
        assert '0.001' in formatted['quantity']
        assert '$50,000.00' in formatted['price']
        assert 'timestamp' in formatted


class TestSecurity:
    """Test security utility functions."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = generate_api_key()
        
        assert len(api_key) == 43  # URL-safe base64 encoding of 32 bytes
        assert all(c.isalnum() or c in '-_' for c in api_key)  # URL-safe characters
        
        # Test uniqueness
        api_key2 = generate_api_key()
        assert api_key != api_key2
    
    def test_hash_and_verify_api_secret(self):
        """Test API secret hashing and verification."""
        secret = 'my_secret_key_123'
        
        # Hash the secret
        hashed = hash_api_secret(secret)
        assert hashed != secret
        assert len(hashed) > len(secret)
        
        # Verify the secret
        assert verify_api_secret(secret, hashed) is True
        assert verify_api_secret('wrong_secret', hashed) is False
    
    def test_encrypt_decrypt_sensitive_data(self):
        """Test encryption and decryption of sensitive data."""
        sensitive_data = 'very_secret_information'
        
        # Encrypt the data
        encrypted = encrypt_sensitive_data(sensitive_data)
        assert encrypted != sensitive_data
        assert len(encrypted) > len(sensitive_data)
        
        # Decrypt the data
        decrypted = decrypt_sensitive_data(encrypted)
        assert decrypted == sensitive_data
    
    def test_encrypt_decrypt_with_key(self):
        """Test encryption/decryption with custom key."""
        data = 'test_data_123'
        key = 'custom_encryption_key'
        
        encrypted = encrypt_sensitive_data(data, key)
        decrypted = decrypt_sensitive_data(encrypted, key)
        
        assert decrypted == data
        
        # Wrong key should fail
        with pytest.raises(Exception):
            decrypt_sensitive_data(encrypted, 'wrong_key')


class TestCalculations:
    """Test calculation utility functions."""
    
    def test_calculate_profit_loss(self):
        """Test profit/loss calculation."""
        # Profitable trade
        buy_price = Decimal('50000')
        sell_price = Decimal('52000')
        quantity = Decimal('0.1')
        
        pnl = calculate_profit_loss(buy_price, sell_price, quantity, 'long')
        assert pnl == Decimal('200')  # (52000 - 50000) * 0.1
        
        # Loss trade
        sell_price = Decimal('48000')
        pnl = calculate_profit_loss(buy_price, sell_price, quantity, 'long')
        assert pnl == Decimal('-200')  # (48000 - 50000) * 0.1
        
        # Short position
        pnl = calculate_profit_loss(buy_price, sell_price, quantity, 'short')
        assert pnl == Decimal('200')  # (50000 - 48000) * 0.1
    
    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        # All winning trades
        trades = [{'pnl': 100}, {'pnl': 50}, {'pnl': 200}]
        win_rate = calculate_win_rate(trades)
        assert win_rate == 100.0
        
        # Mixed trades
        trades = [{'pnl': 100}, {'pnl': -50}, {'pnl': 200}, {'pnl': -30}]
        win_rate = calculate_win_rate(trades)
        assert win_rate == 50.0
        
        # No trades
        win_rate = calculate_win_rate([])
        assert win_rate == 0.0
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        returns = [0.01, 0.02, -0.01, 0.03, 0.015, -0.005, 0.025]
        risk_free_rate = 0.02
        
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
        assert isinstance(sharpe, float)
        assert sharpe > 0  # Should be positive for profitable strategy
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        portfolio_values = [1000, 1100, 1050, 900, 950, 1200, 1150]
        
        max_dd = calculate_max_drawdown(portfolio_values)
        assert isinstance(max_dd, float)
        assert max_dd < 0  # Drawdown should be negative
        assert max_dd >= -1.0  # Should not exceed -100%
    
    def test_calculate_portfolio_value(self):
        """Test portfolio value calculation."""
        positions = [
            {'symbol': 'BTC', 'quantity': Decimal('0.5'), 'price': Decimal('50000')},
            {'symbol': 'ETH', 'quantity': Decimal('2.0'), 'price': Decimal('3000')},
            {'symbol': 'USDT', 'quantity': Decimal('1000'), 'price': Decimal('1')}
        ]
        
        total_value = calculate_portfolio_value(positions)
        expected = Decimal('0.5') * Decimal('50000') + Decimal('2.0') * Decimal('3000') + Decimal('1000')
        assert total_value == expected
    
    def test_calculate_portfolio_value_empty(self):
        """Test portfolio value calculation with empty positions."""
        total_value = calculate_portfolio_value([])
        assert total_value == Decimal('0')


class TestUtilityIntegration:
    """Test integration between utility functions."""
    
    def test_trade_processing_pipeline(self):
        """Test complete trade processing pipeline."""
        # Raw trade data
        raw_trade = {
            'symbol': 'btcusdt',  # lowercase
            'side': 'buy',
            'quantity': '0.001000',  # string with trailing zeros
            'price': '50000.00',
            'timestamp': '2023-12-25T15:30:45Z'
        }
        
        # Validate and normalize
        symbol = raw_trade['symbol'].upper()
        assert validate_trading_pair(symbol)
        
        quantity_result = validate_decimal_amount(raw_trade['quantity'])
        assert quantity_result['valid']
        quantity = quantity_result['decimal']
        
        price_result = validate_decimal_amount(raw_trade['price'])
        assert price_result['valid']
        price = price_result['decimal']
        
        # Format for display
        formatted_trade = {
            'symbol': symbol,
            'side': raw_trade['side'].upper(),
            'quantity': str(quantity),
            'price': format_currency(price, 'USD'),
            'value': format_currency(quantity * price, 'USD')
        }
        
        assert formatted_trade['symbol'] == 'BTCUSDT'
        assert formatted_trade['side'] == 'BUY'
        assert '$50.00' in formatted_trade['value']
    
    def test_security_workflow(self):
        """Test complete security workflow."""
        # Generate API credentials
        api_key = generate_api_key()
        api_secret = 'user_provided_secret_123'
        
        # Validate format
        assert validate_api_key_format(api_key)
        
        # Hash secret for storage
        hashed_secret = hash_api_secret(api_secret)
        
        # Encrypt sensitive data
        sensitive_config = {
            'api_key': api_key,
            'webhook_url': 'https://example.com/webhook'
        }
        
        encrypted_config = encrypt_sensitive_data(str(sensitive_config))
        
        # Later: verify and decrypt
        assert verify_api_secret(api_secret, hashed_secret)
        decrypted_config = decrypt_sensitive_data(encrypted_config)
        assert api_key in decrypted_config
    
    def test_performance_calculation_workflow(self):
        """Test complete performance calculation workflow."""
        # Sample trade history
        trades = [
            {'buy_price': 50000, 'sell_price': 52000, 'quantity': 0.1, 'type': 'long'},
            {'buy_price': 51000, 'sell_price': 49000, 'quantity': 0.05, 'type': 'long'},
            {'buy_price': 48000, 'sell_price': 50000, 'quantity': 0.2, 'type': 'long'}
        ]
        
        # Calculate individual P&L
        pnl_list = []
        for trade in trades:
            pnl = calculate_profit_loss(
                Decimal(str(trade['buy_price'])),
                Decimal(str(trade['sell_price'])),
                Decimal(str(trade['quantity'])),
                trade['type']
            )
            pnl_list.append({'pnl': float(pnl)})
        
        # Calculate performance metrics
        win_rate = calculate_win_rate(pnl_list)
        
        # Calculate returns for Sharpe ratio
        returns = [float(trade['pnl']) / 1000 for trade in pnl_list]  # Normalize
        sharpe = calculate_sharpe_ratio(returns, 0.02)
        
        # Format results
        performance_report = {
            'total_trades': len(trades),
            'win_rate': format_percentage(win_rate / 100),
            'sharpe_ratio': f'{sharpe:.2f}',
            'total_pnl': format_currency(sum(trade['pnl'] for trade in pnl_list), 'USD')
        }
        
        assert performance_report['total_trades'] == 3
        assert '%' in performance_report['win_rate']
        assert '$' in performance_report['total_pnl']