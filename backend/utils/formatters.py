"""Formatting utilities for data presentation."""

from decimal import Decimal
from datetime import datetime
from typing import Union, Optional


def format_currency(amount: Union[Decimal, float, int], 
                   currency: str = 'USD',
                   decimal_places: int = 2) -> str:
    """Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency symbol or code
        decimal_places: Number of decimal places
        
    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return f"0.00 {currency}"
    
    try:
        # Convert to Decimal for precision
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Format with specified decimal places
        format_str = f"{{:.{decimal_places}f}}"
        formatted_amount = format_str.format(float(amount))
        
        # Add currency
        if currency.upper() in ['USD', 'USDT', 'USDC']:
            return f"${formatted_amount}"
        elif currency.upper() == 'EUR':
            return f"€{formatted_amount}"
        elif currency.upper() == 'GBP':
            return f"£{formatted_amount}"
        else:
            return f"{formatted_amount} {currency}"
            
    except (ValueError, TypeError):
        return f"0.00 {currency}"


def format_percentage(value: Union[Decimal, float, int], 
                     decimal_places: int = 2,
                     include_sign: bool = True) -> str:
    """Format value as percentage.
    
    Args:
        value: Value to format (0.1 = 10%)
        decimal_places: Number of decimal places
        include_sign: Whether to include + sign for positive values
        
    Returns:
        str: Formatted percentage string
    """
    if value is None:
        return "0.00%"
    
    try:
        # Convert to percentage
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        percentage = value * 100
        
        # Format with specified decimal places
        format_str = f"{{:.{decimal_places}f}}"
        formatted_value = format_str.format(float(percentage))
        
        # Add sign if requested
        if include_sign and percentage > 0:
            return f"+{formatted_value}%"
        else:
            return f"{formatted_value}%"
            
    except (ValueError, TypeError):
        return "0.00%"


def format_datetime(dt: datetime, 
                   format_type: str = 'default',
                   timezone: str = None) -> str:
    """Format datetime for display.
    
    Args:
        dt: Datetime to format
        format_type: Type of formatting ('default', 'short', 'long', 'iso')
        timezone: Timezone to convert to
        
    Returns:
        str: Formatted datetime string
    """
    if not dt:
        return "N/A"
    
    try:
        # Format based on type
        if format_type == 'short':
            return dt.strftime('%m/%d/%Y %H:%M')
        elif format_type == 'long':
            return dt.strftime('%B %d, %Y at %I:%M %p')
        elif format_type == 'iso':
            return dt.isoformat()
        elif format_type == 'date_only':
            return dt.strftime('%Y-%m-%d')
        elif format_type == 'time_only':
            return dt.strftime('%H:%M:%S')
        else:  # default
            return dt.strftime('%Y-%m-%d %H:%M:%S')
            
    except (ValueError, AttributeError):
        return "Invalid Date"


def format_decimal(value: Union[Decimal, float, int],
                  decimal_places: int = 8,
                  strip_trailing_zeros: bool = True) -> str:
    """Format decimal value.
    
    Args:
        value: Value to format
        decimal_places: Maximum decimal places
        strip_trailing_zeros: Whether to remove trailing zeros
        
    Returns:
        str: Formatted decimal string
    """
    if value is None:
        return "0"
    
    try:
        # Convert to Decimal for precision
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format with specified decimal places
        format_str = f"{{:.{decimal_places}f}}"
        formatted_value = format_str.format(float(value))
        
        # Strip trailing zeros if requested
        if strip_trailing_zeros:
            formatted_value = formatted_value.rstrip('0').rstrip('.')
            if not formatted_value:
                formatted_value = "0"
        
        return formatted_value
        
    except (ValueError, TypeError):
        return "0"


def format_large_number(value: Union[Decimal, float, int],
                       decimal_places: int = 2) -> str:
    """Format large numbers with K, M, B suffixes.
    
    Args:
        value: Value to format
        decimal_places: Number of decimal places
        
    Returns:
        str: Formatted number string
    """
    if value is None:
        return "0"
    
    try:
        # Convert to float for calculation
        if isinstance(value, Decimal):
            value = float(value)
        elif not isinstance(value, (int, float)):
            value = float(str(value))
        
        abs_value = abs(value)
        
        if abs_value >= 1_000_000_000:
            formatted = value / 1_000_000_000
            suffix = "B"
        elif abs_value >= 1_000_000:
            formatted = value / 1_000_000
            suffix = "M"
        elif abs_value >= 1_000:
            formatted = value / 1_000
            suffix = "K"
        else:
            return format_decimal(value, decimal_places)
        
        format_str = f"{{:.{decimal_places}f}}"
        return f"{format_str.format(formatted)}{suffix}"
        
    except (ValueError, TypeError):
        return "0"


def format_trade_side(side: str) -> str:
    """Format trade side for display.
    
    Args:
        side: Trade side ('buy' or 'sell')
        
    Returns:
        str: Formatted trade side
    """
    if not side:
        return "Unknown"
    
    side = side.lower()
    if side == 'buy':
        return "BUY"
    elif side == 'sell':
        return "SELL"
    else:
        return side.upper()


def format_bot_status(status: str) -> str:
    """Format bot status for display.
    
    Args:
        status: Bot status
        
    Returns:
        str: Formatted status
    """
    if not status:
        return "Unknown"
    
    status_map = {
        'active': 'Active',
        'inactive': 'Inactive',
        'running': 'Running',
        'stopped': 'Stopped',
        'paused': 'Paused',
        'error': 'Error'
    }
    
    return status_map.get(status.lower(), status.title())


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted file size
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: Union[int, float]) -> str:
    """Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    if seconds is None or seconds < 0:
        return "0s"
    
    try:
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            else:
                return f"{minutes}m"
        elif seconds < 86400:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            else:
                return f"{hours}h"
        else:
            days = seconds // 86400
            remaining_hours = (seconds % 86400) // 3600
            if remaining_hours > 0:
                return f"{days}d {remaining_hours}h"
            else:
                return f"{days}d"
                
    except (ValueError, TypeError):
        return "0s"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated string
    """
    if not text or len(text) <= max_length:
        return text or ""
    
    return text[:max_length - len(suffix)] + suffix


def format_trade_data(trade_data: dict) -> dict:
    """Format trade data for display.
    
    Args:
        trade_data: Raw trade data dictionary
        
    Returns:
        dict: Formatted trade data
    """
    if not trade_data:
        return {}
    
    formatted = trade_data.copy()
    
    # Format monetary values
    if 'entry_price' in formatted:
        formatted['entry_price'] = format_currency(formatted['entry_price'])
    
    if 'exit_price' in formatted:
        formatted['exit_price'] = format_currency(formatted['exit_price'])
    
    if 'profit_loss' in formatted:
        formatted['profit_loss'] = format_currency(formatted['profit_loss'])
    
    if 'quantity' in formatted:
        formatted['quantity'] = format_decimal(formatted['quantity'], 8)
    
    # Format timestamps
    if 'created_at' in formatted:
        formatted['created_at'] = format_datetime(formatted['created_at'])
    
    if 'updated_at' in formatted:
        formatted['updated_at'] = format_datetime(formatted['updated_at'])
    
    # Format trade side
    if 'side' in formatted:
        formatted['side'] = format_trade_side(formatted['side'])
    
    return formatted