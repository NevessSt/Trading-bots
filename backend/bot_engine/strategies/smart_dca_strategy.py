import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class SmartDCAStrategy(BaseStrategy):
    """Smart Dollar Cost Averaging Strategy with market condition analysis"""
    
    def __init__(self,
                 base_order_amount: float = 100,
                 safety_order_amount: float = 200,
                 max_safety_orders: int = 5,
                 price_deviation: float = 0.025,  # 2.5%
                 safety_order_step_scale: float = 1.2,
                 safety_order_volume_scale: float = 1.4,
                 take_profit: float = 0.015,  # 1.5%
                 stop_loss: float = 0.08,     # 8%
                 cooldown_period: int = 24,   # hours
                 rsi_oversold: float = 30,
                 rsi_overbought: float = 70,
                 use_market_conditions: bool = True):
        """
        Initialize Smart DCA Strategy
        
        Args:
            base_order_amount: Initial order amount in USD
            safety_order_amount: Safety order amount in USD
            max_safety_orders: Maximum number of safety orders
            price_deviation: Price deviation to trigger safety orders
            safety_order_step_scale: Scale factor for safety order steps
            safety_order_volume_scale: Scale factor for safety order volumes
            take_profit: Take profit percentage
            stop_loss: Stop loss percentage
            cooldown_period: Cooldown period between deals (hours)
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            use_market_conditions: Use market condition analysis
        """
        super().__init__()
        self.name = 'Smart DCA Strategy'
        self.description = 'Intelligent DCA with market condition analysis and dynamic safety orders'
        
        self.base_order_amount = base_order_amount
        self.safety_order_amount = safety_order_amount
        self.max_safety_orders = max_safety_orders
        self.price_deviation = price_deviation
        self.safety_order_step_scale = safety_order_step_scale
        self.safety_order_volume_scale = safety_order_volume_scale
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.cooldown_period = cooldown_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.use_market_conditions = use_market_conditions
        
        self.active_deals = {}
        self.last_deal_time = None
        self.logger = logging.getLogger(__name__)
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate DCA trading signals
        
        Args:
            df: OHLCV data with datetime index
            
        Returns:
            DataFrame with signals and order information
        """
        df = df.copy()
        
        # Calculate technical indicators
        df = self._calculate_indicators(df)
        
        # Analyze market conditions
        if self.use_market_conditions:
            df = self._analyze_market_conditions(df)
        
        # Initialize signal columns
        df['signal'] = 0
        df['order_type'] = 'none'
        df['order_amount'] = 0
        df['deal_action'] = 'none'
        
        # Generate base order signals
        df = self._generate_base_order_signals(df)
        
        # Generate safety order signals
        df = self._generate_safety_order_signals(df)
        
        # Generate take profit signals
        df = self._generate_take_profit_signals(df)
        
        return df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volatility
        df['volatility'] = df['close'].pct_change().rolling(window=20).std()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _analyze_market_conditions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze market conditions for better entry timing"""
        # Market trend analysis
        df['trend'] = 'neutral'
        df.loc[df['sma_20'] > df['sma_50'], 'trend'] = 'bullish'
        df.loc[df['sma_20'] < df['sma_50'], 'trend'] = 'bearish'
        
        # Market strength
        df['market_strength'] = 0.5  # Neutral
        
        # Bullish conditions
        bullish_conditions = (
            (df['rsi'] < self.rsi_oversold) |
            (df['close'] < df['bb_lower']) |
            (df['macd'] > df['macd_signal']) & (df['macd_histogram'] > 0)
        )
        df.loc[bullish_conditions, 'market_strength'] = 0.8
        
        # Bearish conditions
        bearish_conditions = (
            (df['rsi'] > self.rsi_overbought) |
            (df['close'] > df['bb_upper']) |
            (df['macd'] < df['macd_signal']) & (df['macd_histogram'] < 0)
        )
        df.loc[bearish_conditions, 'market_strength'] = 0.2
        
        return df
    
    def _generate_base_order_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate base order entry signals"""
        for i, row in df.iterrows():
            # Check cooldown period
            if self._is_in_cooldown(i):
                continue
                
            # Entry conditions
            entry_conditions = [
                row['rsi'] < self.rsi_oversold + 10,  # Slightly oversold
                row['close'] < row['sma_20'],  # Below moving average
            ]
            
            if self.use_market_conditions:
                entry_conditions.append(row['market_strength'] > 0.6)
            
            if all(entry_conditions):
                df.at[i, 'signal'] = 1
                df.at[i, 'order_type'] = 'base_order'
                df.at[i, 'order_amount'] = self.base_order_amount
                df.at[i, 'deal_action'] = 'start_deal'
                
                # Start new deal
                self._start_new_deal(i, row['close'])
        
        return df
    
    def _generate_safety_order_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate safety order signals for active deals"""
        for deal_id, deal in self.active_deals.items():
            if deal['status'] != 'active':
                continue
                
            for i, row in df.iterrows():
                current_price = row['close']
                
                # Calculate price deviation from average entry price
                price_deviation = (deal['avg_entry_price'] - current_price) / deal['avg_entry_price']
                
                # Check if we need a safety order
                required_deviation = self.price_deviation * (self.safety_order_step_scale ** deal['safety_orders_count'])
                
                if (price_deviation >= required_deviation and 
                    deal['safety_orders_count'] < self.max_safety_orders):
                    
                    safety_order_amount = self.safety_order_amount * (self.safety_order_volume_scale ** deal['safety_orders_count'])
                    
                    df.at[i, 'signal'] = 1
                    df.at[i, 'order_type'] = 'safety_order'
                    df.at[i, 'order_amount'] = safety_order_amount
                    df.at[i, 'deal_action'] = 'add_safety_order'
                    
                    # Update deal
                    self._add_safety_order(deal_id, current_price, safety_order_amount)
        
        return df
    
    def _generate_take_profit_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate take profit signals"""
        for deal_id, deal in self.active_deals.items():
            if deal['status'] != 'active':
                continue
                
            for i, row in df.iterrows():
                current_price = row['close']
                
                # Calculate profit percentage
                profit_pct = (current_price - deal['avg_entry_price']) / deal['avg_entry_price']
                
                # Check take profit condition
                if profit_pct >= self.take_profit:
                    df.at[i, 'signal'] = -1
                    df.at[i, 'order_type'] = 'take_profit'
                    df.at[i, 'order_amount'] = deal['total_quantity']
                    df.at[i, 'deal_action'] = 'close_deal'
                    
                    # Close deal
                    self._close_deal(deal_id, current_price, 'take_profit')
                
                # Check stop loss condition
                elif profit_pct <= -self.stop_loss:
                    df.at[i, 'signal'] = -1
                    df.at[i, 'order_type'] = 'stop_loss'
                    df.at[i, 'order_amount'] = deal['total_quantity']
                    df.at[i, 'deal_action'] = 'close_deal'
                    
                    # Close deal
                    self._close_deal(deal_id, current_price, 'stop_loss')
        
        return df
    
    def _is_in_cooldown(self, timestamp) -> bool:
        """Check if we're in cooldown period"""
        if self.last_deal_time is None:
            return False
        
        if isinstance(timestamp, str):
            current_time = pd.to_datetime(timestamp)
        else:
            current_time = timestamp
            
        time_diff = current_time - self.last_deal_time
        return time_diff < timedelta(hours=self.cooldown_period)
    
    def _start_new_deal(self, timestamp, price: float):
        """Start a new DCA deal"""
        deal_id = f"deal_{len(self.active_deals) + 1}_{timestamp}"
        
        self.active_deals[deal_id] = {
            'start_time': timestamp,
            'status': 'active',
            'base_order_price': price,
            'avg_entry_price': price,
            'total_invested': self.base_order_amount,
            'total_quantity': self.base_order_amount / price,
            'safety_orders_count': 0,
            'safety_orders': []
        }
        
        self.last_deal_time = pd.to_datetime(timestamp) if isinstance(timestamp, str) else timestamp
        
    def _add_safety_order(self, deal_id: str, price: float, amount: float):
        """Add safety order to existing deal"""
        deal = self.active_deals[deal_id]
        
        # Calculate new averages
        new_quantity = amount / price
        total_quantity = deal['total_quantity'] + new_quantity
        total_invested = deal['total_invested'] + amount
        new_avg_price = total_invested / total_quantity
        
        # Update deal
        deal['total_quantity'] = total_quantity
        deal['total_invested'] = total_invested
        deal['avg_entry_price'] = new_avg_price
        deal['safety_orders_count'] += 1
        deal['safety_orders'].append({
            'price': price,
            'amount': amount,
            'quantity': new_quantity
        })
    
    def _close_deal(self, deal_id: str, exit_price: float, reason: str):
        """Close an active deal"""
        deal = self.active_deals[deal_id]
        
        # Calculate final profit/loss
        total_value = deal['total_quantity'] * exit_price
        profit_loss = total_value - deal['total_invested']
        profit_pct = profit_loss / deal['total_invested']
        
        # Update deal status
        deal['status'] = 'closed'
        deal['exit_price'] = exit_price
        deal['exit_reason'] = reason
        deal['profit_loss'] = profit_loss
        deal['profit_pct'] = profit_pct
        deal['close_time'] = datetime.now()
    
    def get_parameters(self) -> Dict:
        """Get strategy parameters"""
        return {
            'base_order_amount': self.base_order_amount,
            'safety_order_amount': self.safety_order_amount,
            'max_safety_orders': self.max_safety_orders,
            'price_deviation': self.price_deviation,
            'safety_order_step_scale': self.safety_order_step_scale,
            'safety_order_volume_scale': self.safety_order_volume_scale,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'cooldown_period': self.cooldown_period,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'use_market_conditions': self.use_market_conditions
        }
    
    def set_parameters(self, parameters: Dict):
        """Set strategy parameters"""
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_active_deals(self) -> Dict:
        """Get all active deals"""
        return {k: v for k, v in self.active_deals.items() if v['status'] == 'active'}
    
    def get_deal_statistics(self) -> Dict:
        """Get deal statistics"""
        closed_deals = [deal for deal in self.active_deals.values() if deal['status'] == 'closed']
        
        if not closed_deals:
            return {'total_deals': 0, 'win_rate': 0, 'avg_profit': 0}
        
        winning_deals = [deal for deal in closed_deals if deal['profit_loss'] > 0]
        
        return {
            'total_deals': len(closed_deals),
            'winning_deals': len(winning_deals),
            'losing_deals': len(closed_deals) - len(winning_deals),
            'win_rate': len(winning_deals) / len(closed_deals) * 100,
            'avg_profit': np.mean([deal['profit_pct'] for deal in closed_deals]) * 100,
            'total_profit': sum([deal['profit_loss'] for deal in closed_deals])
        }