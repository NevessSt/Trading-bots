import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy
import logging
from typing import Dict, List, Tuple, Optional

class AdvancedGridStrategy(BaseStrategy):
    """Advanced Grid Trading Strategy with dynamic grid adjustment and risk management"""
    
    def __init__(self, 
                 grid_levels: int = 10,
                 grid_spacing: float = 0.01,  # 1% spacing
                 base_order_size: float = 100,
                 safety_orders: int = 5,
                 safety_order_multiplier: float = 1.5,
                 take_profit: float = 0.02,  # 2%
                 stop_loss: float = 0.05,    # 5%
                 dynamic_adjustment: bool = True,
                 volatility_threshold: float = 0.02):
        """
        Initialize Advanced Grid Strategy
        
        Args:
            grid_levels: Number of grid levels
            grid_spacing: Spacing between grid levels (percentage)
            base_order_size: Base order size in USD
            safety_orders: Number of safety orders
            safety_order_multiplier: Multiplier for safety order sizes
            take_profit: Take profit percentage
            stop_loss: Stop loss percentage
            dynamic_adjustment: Enable dynamic grid adjustment
            volatility_threshold: Volatility threshold for dynamic adjustment
        """
        super().__init__()
        self.name = 'Advanced Grid Strategy'
        self.description = 'Dynamic grid trading with volatility-based adjustments and advanced risk management'
        
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing
        self.base_order_size = base_order_size
        self.safety_orders = safety_orders
        self.safety_order_multiplier = safety_order_multiplier
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.dynamic_adjustment = dynamic_adjustment
        self.volatility_threshold = volatility_threshold
        
        self.grid_orders = []
        self.active_positions = {}
        self.logger = logging.getLogger(__name__)
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate grid trading signals
        
        Args:
            df: OHLCV data
            
        Returns:
            DataFrame with signals and grid levels
        """
        df = df.copy()
        
        # Calculate volatility for dynamic adjustment
        df['volatility'] = df['close'].pct_change().rolling(window=20).std()
        
        # Adjust grid spacing based on volatility if enabled
        if self.dynamic_adjustment:
            df['adjusted_spacing'] = self._calculate_dynamic_spacing(df['volatility'])
        else:
            df['adjusted_spacing'] = self.grid_spacing
            
        # Calculate grid levels
        df['grid_upper'], df['grid_lower'] = self._calculate_grid_levels(df)
        
        # Generate signals
        df['signal'] = 0
        df['order_type'] = 'none'
        df['order_size'] = 0
        
        # Buy signals at lower grid levels
        buy_condition = (df['close'] <= df['grid_lower']) & (df['close'].shift(1) > df['grid_lower'].shift(1))
        df.loc[buy_condition, 'signal'] = 1
        df.loc[buy_condition, 'order_type'] = 'buy'
        df.loc[buy_condition, 'order_size'] = self._calculate_order_size(df.loc[buy_condition])
        
        # Sell signals at upper grid levels
        sell_condition = (df['close'] >= df['grid_upper']) & (df['close'].shift(1) < df['grid_upper'].shift(1))
        df.loc[sell_condition, 'signal'] = -1
        df.loc[sell_condition, 'order_type'] = 'sell'
        df.loc[sell_condition, 'order_size'] = self._calculate_order_size(df.loc[sell_condition])
        
        return df
    
    def _calculate_dynamic_spacing(self, volatility: pd.Series) -> pd.Series:
        """Calculate dynamic grid spacing based on volatility"""
        base_spacing = self.grid_spacing
        volatility_multiplier = 1 + (volatility / self.volatility_threshold)
        return base_spacing * volatility_multiplier.clip(0.5, 3.0)  # Limit multiplier range
    
    def _calculate_grid_levels(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate upper and lower grid levels"""
        current_price = df['close']
        spacing = df['adjusted_spacing']
        
        grid_upper = current_price * (1 + spacing)
        grid_lower = current_price * (1 - spacing)
        
        return grid_upper, grid_lower
    
    def _calculate_order_size(self, df_subset: pd.DataFrame) -> pd.Series:
        """Calculate order size based on grid level and safety orders"""
        # For simplicity, return base order size
        # In production, this would consider position size, available balance, etc.
        return pd.Series([self.base_order_size] * len(df_subset), index=df_subset.index)
    
    def calculate_position_size(self, balance: float, risk_per_trade: float = 0.02) -> float:
        """Calculate position size based on available balance and risk"""
        max_risk_amount = balance * risk_per_trade
        position_size = max_risk_amount / self.stop_loss
        return min(position_size, self.base_order_size)
    
    def should_close_position(self, entry_price: float, current_price: float, side: str) -> bool:
        """Check if position should be closed based on take profit or stop loss"""
        if side == 'long':
            profit_pct = (current_price - entry_price) / entry_price
            return profit_pct >= self.take_profit or profit_pct <= -self.stop_loss
        else:
            profit_pct = (entry_price - current_price) / entry_price
            return profit_pct >= self.take_profit or profit_pct <= -self.stop_loss
    
    def get_parameters(self) -> Dict:
        """Get strategy parameters"""
        return {
            'grid_levels': self.grid_levels,
            'grid_spacing': self.grid_spacing,
            'base_order_size': self.base_order_size,
            'safety_orders': self.safety_orders,
            'safety_order_multiplier': self.safety_order_multiplier,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'dynamic_adjustment': self.dynamic_adjustment,
            'volatility_threshold': self.volatility_threshold
        }
    
    def set_parameters(self, parameters: Dict):
        """Set strategy parameters"""
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def backtest(self, df: pd.DataFrame, initial_balance: float = 10000) -> Dict:
        """Backtest the strategy"""
        df_signals = self.generate_signals(df)
        
        balance = initial_balance
        position = 0
        trades = []
        
        for i, row in df_signals.iterrows():
            if row['signal'] == 1:  # Buy signal
                if balance >= row['order_size']:
                    position += row['order_size'] / row['close']
                    balance -= row['order_size']
                    trades.append({
                        'type': 'buy',
                        'price': row['close'],
                        'size': row['order_size'] / row['close'],
                        'timestamp': i
                    })
            elif row['signal'] == -1:  # Sell signal
                if position > 0:
                    sell_amount = min(position, row['order_size'] / row['close'])
                    balance += sell_amount * row['close']
                    position -= sell_amount
                    trades.append({
                        'type': 'sell',
                        'price': row['close'],
                        'size': sell_amount,
                        'timestamp': i
                    })
        
        # Calculate final portfolio value
        final_value = balance + (position * df_signals['close'].iloc[-1])
        total_return = (final_value - initial_balance) / initial_balance
        
        return {
            'initial_balance': initial_balance,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(trades),
            'trades': trades
        }