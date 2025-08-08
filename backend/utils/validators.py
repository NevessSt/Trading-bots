"""Validation utilities for input data."""

import re
from decimal import Decimal, InvalidOperation
from typing import Union, Optional


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, ""


def validate_trading_pair(trading_pair: str) -> bool:
    """Validate trading pair format.
    
    Args:
        trading_pair: Trading pair like 'BTC/USDT'
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not trading_pair or not isinstance(trading_pair, str):
        return False
    
    # Check format: BASE/QUOTE
    if '/' not in trading_pair:
        return False
    
    parts = trading_pair.split('/')
    if len(parts) != 2:
        return False
    
    base, quote = parts
    
    # Check that both parts are valid (alphanumeric, 2-10 chars)
    if not re.match(r'^[A-Z0-9]{2,10}$', base):
        return False
    
    if not re.match(r'^[A-Z0-9]{2,10}$', quote):
        return False
    
    return True


def validate_decimal_amount(amount: Union[str, int, float, Decimal], 
                          min_value: Optional[Decimal] = None,
                          max_value: Optional[Decimal] = None,
                          max_decimal_places: int = 8) -> tuple[bool, str, Optional[Decimal]]:
    """Validate decimal amount.
    
    Args:
        amount: Amount to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        max_decimal_places: Maximum decimal places allowed
        
    Returns:
        tuple: (is_valid, error_message, decimal_value)
    """
    try:
        # Convert to Decimal
        if isinstance(amount, str):
            decimal_amount = Decimal(amount)
        elif isinstance(amount, (int, float)):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            decimal_amount = amount
        else:
            return False, "Invalid amount type", None
        
        # Check for NaN or infinity
        if not decimal_amount.is_finite():
            return False, "Amount must be a finite number", None
        
        # Check decimal places
        if decimal_amount.as_tuple().exponent < -max_decimal_places:
            return False, f"Amount cannot have more than {max_decimal_places} decimal places", None
        
        # Check minimum value
        if min_value is not None and decimal_amount < min_value:
            return False, f"Amount must be at least {min_value}", None
        
        # Check maximum value
        if max_value is not None and decimal_amount > max_value:
            return False, f"Amount must be at most {max_value}", None
        
        return True, "", decimal_amount
        
    except (InvalidOperation, ValueError, TypeError):
        return False, "Invalid amount format", None


def validate_api_key_format(api_key: str, exchange: str = None) -> bool:
    """Validate API key format.
    
    Args:
        api_key: API key to validate
        exchange: Exchange name for specific validation
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # General validation - should be alphanumeric with some special chars
    if not re.match(r'^[A-Za-z0-9_\-\.]{16,128}$', api_key):
        return False
    
    # Exchange-specific validation
    if exchange:
        exchange = exchange.lower()
        
        if exchange == 'binance':
            # Binance API keys are typically 64 characters
            return len(api_key) == 64 and re.match(r'^[A-Za-z0-9]{64}$', api_key)
        
        elif exchange == 'coinbase':
            # Coinbase API keys have specific format
            return len(api_key) >= 32 and re.match(r'^[A-Za-z0-9\-_]{32,}$', api_key)
        
        elif exchange == 'kraken':
            # Kraken API keys are base64-like
            return len(api_key) >= 40 and re.match(r'^[A-Za-z0-9+/=]{40,}$', api_key)
    
    return True


def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 30:
        return False, "Username must be less than 30 characters"
    
    # Allow alphanumeric, underscore, and hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Must start with letter or number
    if not re.match(r'^[a-zA-Z0-9]', username):
        return False, "Username must start with a letter or number"
    
    return True, ""


def validate_bot_name(name: str) -> tuple[bool, str]:
    """Validate bot name.
    
    Args:
        name: Bot name to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "Bot name is required"
    
    if len(name.strip()) < 1:
        return False, "Bot name cannot be empty"
    
    if len(name) > 100:
        return False, "Bot name must be less than 100 characters"
    
    # Allow most characters but not control characters
    if re.search(r'[\x00-\x1f\x7f]', name):
        return False, "Bot name contains invalid characters"
    
    return True, ""


def validate_strategy_name(strategy: str) -> bool:
    """Validate strategy name.
    
    Args:
        strategy: Strategy name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not strategy or not isinstance(strategy, str):
        return False
    
    # Valid strategy names (snake_case)
    valid_strategies = {
        'grid',
        'dca',
        'scalping',
        'sma_crossover',
        'rsi_oversold',
        'bollinger_bands',
        'macd_signal',
        'mean_reversion',
        'momentum',
        'arbitrage'
    }
    
    return strategy in valid_strategies


def validate_json_config(config: dict, required_fields: list = None) -> tuple[bool, str]:
    """Validate JSON configuration.
    
    Args:
        config: Configuration dictionary
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(config, dict):
        return False, "Configuration must be a dictionary"
    
    if required_fields:
        for field in required_fields:
            if field not in config:
                return False, f"Required field '{field}' is missing"
    
    # Check for reasonable size (prevent DoS)
    if len(str(config)) > 10000:  # 10KB limit
        return False, "Configuration is too large"
    
    return True, ""