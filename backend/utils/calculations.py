"""Utility functions for trading calculations and analytics."""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
import math


def calculate_profit_loss(entry_price: float, exit_price: float, quantity: float, side: str) -> float:
    """
    Calculate profit/loss for a trade.
    
    Args:
        entry_price: Price at which the position was entered
        exit_price: Price at which the position was exited
        quantity: Amount of the asset traded
        side: 'buy' or 'sell'
    
    Returns:
        Profit/loss amount
    """
    if side.lower() == 'buy':
        return (exit_price - entry_price) * quantity
    elif side.lower() == 'sell':
        return (entry_price - exit_price) * quantity
    else:
        raise ValueError("Side must be 'buy' or 'sell'")


def calculate_win_rate(trades: List[Dict]) -> float:
    """
    Calculate win rate from a list of trades.
    
    Args:
        trades: List of trade dictionaries with 'profit_loss' key
    
    Returns:
        Win rate as a percentage (0-100)
    """
    if not trades:
        return 0.0
    
    winning_trades = sum(1 for trade in trades if trade.get('profit_loss', 0) > 0)
    return (winning_trades / len(trades)) * 100


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for a series of returns.
    
    Args:
        returns: List of periodic returns
        risk_free_rate: Risk-free rate (default 2%)
    
    Returns:
        Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = math.sqrt(variance)
    
    if std_dev == 0:
        return 0.0
    
    return (mean_return - risk_free_rate) / std_dev


def calculate_max_drawdown(portfolio_values: List[float]) -> float:
    """
    Calculate maximum drawdown from portfolio values.
    
    Args:
        portfolio_values: List of portfolio values over time
    
    Returns:
        Maximum drawdown as a percentage
    """
    if not portfolio_values or len(portfolio_values) < 2:
        return 0.0
    
    peak = portfolio_values[0]
    max_drawdown = 0.0
    
    for value in portfolio_values[1:]:
        if value > peak:
            peak = value
        else:
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown * 100


def calculate_portfolio_value(positions: List[Dict], current_prices: Dict[str, float]) -> float:
    """
    Calculate total portfolio value based on current positions and prices.
    
    Args:
        positions: List of position dictionaries with 'symbol', 'quantity', 'side'
        current_prices: Dictionary mapping symbols to current prices
    
    Returns:
        Total portfolio value
    """
    total_value = 0.0
    
    for position in positions:
        symbol = position.get('symbol')
        quantity = position.get('quantity', 0)
        side = position.get('side', 'buy')
        
        if symbol in current_prices:
            price = current_prices[symbol]
            if side.lower() == 'buy':
                total_value += quantity * price
            elif side.lower() == 'sell':
                total_value -= quantity * price
    
    return total_value


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
    
    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate simple moving average.
    
    Args:
        prices: List of prices
        period: Moving average period
    
    Returns:
        Moving average value or None if insufficient data
    """
    if len(prices) < period:
        return None
    
    return sum(prices[-period:]) / period


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
    
    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0 if new_value == 0 else float('inf')
    
    return ((new_value - old_value) / old_value) * 100


def calculate_compound_return(returns: List[float]) -> float:
    """
    Calculate compound return from a series of periodic returns.
    
    Args:
        returns: List of periodic returns (as decimals, e.g., 0.05 for 5%)
    
    Returns:
        Compound return as a percentage
    """
    if not returns:
        return 0.0
    
    compound = 1.0
    for ret in returns:
        compound *= (1 + ret)
    
    return (compound - 1) * 100