import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class AdvancedScalpingStrategy(BaseStrategy):
    """Advanced Scalping Strategy with multiple timeframe analysis and market microstructure"""
    
    def __init__(self,
                 timeframes: List[str] = ['1m', '5m', '15m'],
                 min_spread: float = 0.0001,  # Minimum spread requirement
                 max_spread: float = 0.001,   # Maximum spread allowed
                 volume_threshold: float = 1000000,  # Minimum volume
                 volatility_threshold: float = 0.005,  # Minimum volatility
                 quick_profit_target: float = 0.002,  # 0.2% quick profit
                 extended_profit_target: float = 0.005,  # 0.5% extended profit
                 stop_loss: float = 0.003,    # 0.3% stop loss
                 max_holding_time: int = 300,  # 5 minutes max holding
                 rsi_oversold: float = 25,
                 rsi_overbought: float = 75,
                 use_order_book: bool = True,
                 use_tape_reading: bool = True):
        """
        Initialize Advanced Scalping Strategy
        
        Args:
            timeframes: List of timeframes to analyze
            min_spread: Minimum bid-ask spread required
            max_spread: Maximum bid-ask spread allowed
            volume_threshold: Minimum volume requirement
            volatility_threshold: Minimum volatility requirement
            quick_profit_target: Quick profit target percentage
            extended_profit_target: Extended profit target percentage
            stop_loss: Stop loss percentage
            max_holding_time: Maximum holding time in seconds
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            use_order_book: Use order book analysis
            use_tape_reading: Use tape reading signals
        """
        super().__init__()
        self.name = 'Advanced Scalping Strategy'
        self.description = 'High-frequency scalping with multi-timeframe analysis and market microstructure'
        
        self.timeframes = timeframes
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.volume_threshold = volume_threshold
        self.volatility_threshold = volatility_threshold
        self.quick_profit_target = quick_profit_target
        self.extended_profit_target = extended_profit_target
        self.stop_loss = stop_loss
        self.max_holding_time = max_holding_time
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.use_order_book = use_order_book
        self.use_tape_reading = use_tape_reading
        
        self.active_positions = {}
        self.market_data_cache = {}
        self.logger = logging.getLogger(__name__)
        
    def generate_signals(self, df: pd.DataFrame, order_book: Optional[Dict] = None, 
                        recent_trades: Optional[List] = None) -> pd.DataFrame:
        """Generate scalping signals with market microstructure analysis
        
        Args:
            df: OHLCV data (1-minute timeframe)
            order_book: Current order book data
            recent_trades: Recent trade data for tape reading
            
        Returns:
            DataFrame with signals and trade information
        """
        df = df.copy()
        
        # Calculate technical indicators
        df = self._calculate_scalping_indicators(df)
        
        # Analyze market microstructure
        if self.use_order_book and order_book:
            df = self._analyze_order_book(df, order_book)
        
        if self.use_tape_reading and recent_trades:
            df = self._analyze_tape_reading(df, recent_trades)
        
        # Multi-timeframe analysis
        df = self._multi_timeframe_analysis(df)
        
        # Initialize signal columns
        df['signal'] = 0
        df['entry_type'] = 'none'
        df['exit_type'] = 'none'
        df['confidence'] = 0.0
        df['position_size'] = 0.0
        
        # Generate entry signals
        df = self._generate_entry_signals(df)
        
        # Generate exit signals
        df = self._generate_exit_signals(df)
        
        return df
    
    def _calculate_scalping_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators optimized for scalping"""
        # Fast RSI (5-period)
        df['rsi_fast'] = self._calculate_rsi(df['close'], period=5)
        
        # Standard RSI (14-period)
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        
        # Fast moving averages
        df['ema_3'] = df['close'].ewm(span=3).mean()
        df['ema_8'] = df['close'].ewm(span=8).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        
        # VWAP (Volume Weighted Average Price)
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Price momentum
        df['momentum_1'] = df['close'].pct_change(1)
        df['momentum_3'] = df['close'].pct_change(3)
        df['momentum_5'] = df['close'].pct_change(5)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Volatility
        df['volatility'] = df['close'].pct_change().rolling(window=10).std()
        
        # Support and resistance levels
        df['resistance'] = df['high'].rolling(window=20).max()
        df['support'] = df['low'].rolling(window=20).min()
        
        # Price position within range
        df['price_position'] = (df['close'] - df['support']) / (df['resistance'] - df['support'])
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _analyze_order_book(self, df: pd.DataFrame, order_book: Dict) -> pd.DataFrame:
        """Analyze order book for market microstructure signals"""
        if 'bids' not in order_book or 'asks' not in order_book:
            return df
        
        bids = order_book['bids']
        asks = order_book['asks']
        
        if not bids or not asks:
            return df
        
        # Calculate spread
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread = (best_ask - best_bid) / best_bid
        
        # Order book imbalance
        bid_volume = sum([float(bid[1]) for bid in bids[:10]])
        ask_volume = sum([float(ask[1]) for ask in asks[:10]])
        total_volume = bid_volume + ask_volume
        
        if total_volume > 0:
            order_book_imbalance = (bid_volume - ask_volume) / total_volume
        else:
            order_book_imbalance = 0
        
        # Add to dataframe (broadcast to all rows)
        df['spread'] = spread
        df['order_book_imbalance'] = order_book_imbalance
        df['bid_volume'] = bid_volume
        df['ask_volume'] = ask_volume
        
        return df
    
    def _analyze_tape_reading(self, df: pd.DataFrame, recent_trades: List) -> pd.DataFrame:
        """Analyze recent trades for tape reading signals"""
        if not recent_trades:
            return df
        
        # Analyze recent trade flow
        buy_volume = sum([float(trade['qty']) for trade in recent_trades if trade['side'] == 'buy'])
        sell_volume = sum([float(trade['qty']) for trade in recent_trades if trade['side'] == 'sell'])
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            buy_pressure = buy_volume / total_volume
        else:
            buy_pressure = 0.5
        
        # Large trade detection
        avg_trade_size = total_volume / len(recent_trades) if recent_trades else 0
        large_trades = [trade for trade in recent_trades if float(trade['qty']) > avg_trade_size * 3]
        
        # Add to dataframe
        df['buy_pressure'] = buy_pressure
        df['large_trade_count'] = len(large_trades)
        df['avg_trade_size'] = avg_trade_size
        
        return df
    
    def _multi_timeframe_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform multi-timeframe analysis"""
        # For simplicity, we'll use the current timeframe data
        # In production, you would fetch data from multiple timeframes
        
        # Trend analysis
        df['trend_short'] = 'neutral'
        df['trend_medium'] = 'neutral'
        
        # Short-term trend (EMA 3 vs EMA 8)
        df.loc[df['ema_3'] > df['ema_8'], 'trend_short'] = 'bullish'
        df.loc[df['ema_3'] < df['ema_8'], 'trend_short'] = 'bearish'
        
        # Medium-term trend (EMA 8 vs EMA 21)
        df.loc[df['ema_8'] > df['ema_21'], 'trend_medium'] = 'bullish'
        df.loc[df['ema_8'] < df['ema_21'], 'trend_medium'] = 'bearish'
        
        return df
    
    def _generate_entry_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate entry signals based on multiple factors"""
        for i, row in df.iterrows():
            # Skip if market conditions are not suitable
            if not self._check_market_conditions(row):
                continue
            
            # Long entry conditions
            long_conditions = [
                row['rsi_fast'] < self.rsi_oversold,
                row['close'] < row['vwap'],
                row['momentum_1'] > 0,
                row['trend_short'] == 'bullish' or row['trend_medium'] == 'bullish',
                row['volume_ratio'] > 1.2,
            ]
            
            # Add order book conditions if available
            if 'order_book_imbalance' in row:
                long_conditions.append(row['order_book_imbalance'] > 0.1)
            
            if 'buy_pressure' in row:
                long_conditions.append(row['buy_pressure'] > 0.6)
            
            # Short entry conditions
            short_conditions = [
                row['rsi_fast'] > self.rsi_overbought,
                row['close'] > row['vwap'],
                row['momentum_1'] < 0,
                row['trend_short'] == 'bearish' or row['trend_medium'] == 'bearish',
                row['volume_ratio'] > 1.2,
            ]
            
            # Add order book conditions if available
            if 'order_book_imbalance' in row:
                short_conditions.append(row['order_book_imbalance'] < -0.1)
            
            if 'buy_pressure' in row:
                short_conditions.append(row['buy_pressure'] < 0.4)
            
            # Calculate confidence scores
            long_confidence = sum(long_conditions) / len(long_conditions)
            short_confidence = sum(short_conditions) / len(short_conditions)
            
            # Generate signals based on confidence
            if long_confidence >= 0.7:
                df.at[i, 'signal'] = 1
                df.at[i, 'entry_type'] = 'long'
                df.at[i, 'confidence'] = long_confidence
                df.at[i, 'position_size'] = self._calculate_position_size(row, long_confidence)
            elif short_confidence >= 0.7:
                df.at[i, 'signal'] = -1
                df.at[i, 'entry_type'] = 'short'
                df.at[i, 'confidence'] = short_confidence
                df.at[i, 'position_size'] = self._calculate_position_size(row, short_confidence)
        
        return df
    
    def _generate_exit_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate exit signals for active positions"""
        for position_id, position in self.active_positions.items():
            if position['status'] != 'active':
                continue
            
            for i, row in df.iterrows():
                current_price = row['close']
                entry_price = position['entry_price']
                side = position['side']
                entry_time = position['entry_time']
                
                # Calculate profit/loss
                if side == 'long':
                    pnl_pct = (current_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                
                # Time-based exit
                if isinstance(i, pd.Timestamp) and isinstance(entry_time, pd.Timestamp):
                    time_held = (i - entry_time).total_seconds()
                    if time_held > self.max_holding_time:
                        df.at[i, 'signal'] = -1 if side == 'long' else 1
                        df.at[i, 'exit_type'] = 'time_exit'
                        self._close_position(position_id, current_price, 'time_exit')
                        continue
                
                # Profit target exits
                if pnl_pct >= self.quick_profit_target:
                    df.at[i, 'signal'] = -1 if side == 'long' else 1
                    df.at[i, 'exit_type'] = 'quick_profit'
                    self._close_position(position_id, current_price, 'quick_profit')
                elif pnl_pct >= self.extended_profit_target:
                    df.at[i, 'signal'] = -1 if side == 'long' else 1
                    df.at[i, 'exit_type'] = 'extended_profit'
                    self._close_position(position_id, current_price, 'extended_profit')
                
                # Stop loss exit
                elif pnl_pct <= -self.stop_loss:
                    df.at[i, 'signal'] = -1 if side == 'long' else 1
                    df.at[i, 'exit_type'] = 'stop_loss'
                    self._close_position(position_id, current_price, 'stop_loss')
        
        return df
    
    def _check_market_conditions(self, row: pd.Series) -> bool:
        """Check if market conditions are suitable for scalping"""
        conditions = [
            row['volume'] >= self.volume_threshold,
            row['volatility'] >= self.volatility_threshold,
        ]
        
        # Check spread conditions if available
        if 'spread' in row:
            conditions.extend([
                row['spread'] >= self.min_spread,
                row['spread'] <= self.max_spread
            ])
        
        return all(conditions)
    
    def _calculate_position_size(self, row: pd.Series, confidence: float) -> float:
        """Calculate position size based on confidence and market conditions"""
        base_size = 1000  # Base position size in USD
        
        # Adjust based on confidence
        size_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1.0x based on confidence
        
        # Adjust based on volatility
        volatility_adjustment = 1 / (1 + row['volatility'] * 10)  # Reduce size in high volatility
        
        return base_size * size_multiplier * volatility_adjustment
    
    def _open_position(self, timestamp, price: float, side: str, size: float) -> str:
        """Open a new position"""
        position_id = f"scalp_{len(self.active_positions) + 1}_{timestamp}"
        
        self.active_positions[position_id] = {
            'entry_time': timestamp,
            'entry_price': price,
            'side': side,
            'size': size,
            'status': 'active'
        }
        
        return position_id
    
    def _close_position(self, position_id: str, exit_price: float, reason: str):
        """Close an active position"""
        if position_id not in self.active_positions:
            return
        
        position = self.active_positions[position_id]
        
        # Calculate final P&L
        if position['side'] == 'long':
            pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
        else:
            pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
        
        pnl_amount = position['size'] * pnl_pct
        
        # Update position
        position['status'] = 'closed'
        position['exit_price'] = exit_price
        position['exit_reason'] = reason
        position['pnl_pct'] = pnl_pct
        position['pnl_amount'] = pnl_amount
        position['close_time'] = datetime.now()
    
    def get_parameters(self) -> Dict:
        """Get strategy parameters"""
        return {
            'timeframes': self.timeframes,
            'min_spread': self.min_spread,
            'max_spread': self.max_spread,
            'volume_threshold': self.volume_threshold,
            'volatility_threshold': self.volatility_threshold,
            'quick_profit_target': self.quick_profit_target,
            'extended_profit_target': self.extended_profit_target,
            'stop_loss': self.stop_loss,
            'max_holding_time': self.max_holding_time,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'use_order_book': self.use_order_book,
            'use_tape_reading': self.use_tape_reading
        }
    
    def set_parameters(self, parameters: Dict):
        """Set strategy parameters"""
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for closed positions"""
        closed_positions = [pos for pos in self.active_positions.values() if pos['status'] == 'closed']
        
        if not closed_positions:
            return {'total_trades': 0, 'win_rate': 0, 'avg_profit': 0}
        
        winning_trades = [pos for pos in closed_positions if pos['pnl_amount'] > 0]
        
        return {
            'total_trades': len(closed_positions),
            'winning_trades': len(winning_trades),
            'losing_trades': len(closed_positions) - len(winning_trades),
            'win_rate': len(winning_trades) / len(closed_positions) * 100,
            'avg_profit_pct': np.mean([pos['pnl_pct'] for pos in closed_positions]) * 100,
            'total_profit': sum([pos['pnl_amount'] for pos in closed_positions]),
            'avg_holding_time': np.mean([(pos['close_time'] - pos['entry_time']).total_seconds() 
                                       for pos in closed_positions if 'close_time' in pos])
        }