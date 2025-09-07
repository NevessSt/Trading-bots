#!/usr/bin/env python3
"""
Paper Trading System
Live testing mode that simulates real trading without actual money
Uses real market data and conditions for accurate simulation
"""

import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import websocket
import requests
from decimal import Decimal, ROUND_HALF_UP

# Import our components
from .risk_manager import AdvancedRiskManager, RiskParameters, PositionSide, Position
from .enhanced_backtesting import Trade, TechnicalIndicators

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"

@dataclass
class PaperOrder:
    """Paper trading order"""
    id: str
    symbol: str
    side: str  # BUY or SELL
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # None for market orders
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    commission: float = 0.0
    slippage: float = 0.0
    reason: str = ""
    parent_order_id: Optional[str] = None  # For OCO orders

@dataclass
class PaperPosition:
    """Paper trading position"""
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    trailing_stop_distance: Optional[float] = None

@dataclass
class MarketData:
    """Real-time market data"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime
    high_24h: float = 0.0
    low_24h: float = 0.0
    change_24h: float = 0.0

@dataclass
class PaperAccount:
    """Paper trading account state"""
    balance: float
    equity: float
    margin_used: float = 0.0
    margin_available: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_commission: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class MarketDataProvider:
    """Real-time market data provider"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.logger = logging.getLogger(__name__)
        self.market_data = {}
        self.subscribers = []
        self.ws_connections = {}
        self.running = False
        
    def subscribe(self, callback: Callable[[MarketData], None]):
        """Subscribe to market data updates"""
        self.subscribers.append(callback)
    
    def start(self):
        """Start real-time data feed"""
        self.running = True
        
        # Start WebSocket connections for each symbol
        for symbol in self.symbols:
            threading.Thread(
                target=self._start_websocket,
                args=(symbol,),
                daemon=True
            ).start()
        
        # Start price update simulator (fallback)
        threading.Thread(
            target=self._simulate_price_updates,
            daemon=True
        ).start()
    
    def stop(self):
        """Stop data feed"""
        self.running = False
        for ws in self.ws_connections.values():
            if ws:
                ws.close()
    
    def _start_websocket(self, symbol: str):
        """Start WebSocket connection for symbol"""
        try:
            # Binance WebSocket URL (example)
            ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@ticker"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    market_data = MarketData(
                        symbol=data.get('s', symbol),
                        price=float(data.get('c', 0)),
                        bid=float(data.get('b', 0)),
                        ask=float(data.get('a', 0)),
                        volume=float(data.get('v', 0)),
                        timestamp=datetime.now(),
                        high_24h=float(data.get('h', 0)),
                        low_24h=float(data.get('l', 0)),
                        change_24h=float(data.get('P', 0))
                    )
                    
                    self.market_data[symbol] = market_data
                    
                    # Notify subscribers
                    for callback in self.subscribers:
                        try:
                            callback(market_data)
                        except Exception as e:
                            self.logger.error(f"Error in market data callback: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error processing market data: {e}")
            
            def on_error(ws, error):
                self.logger.error(f"WebSocket error for {symbol}: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                self.logger.info(f"WebSocket closed for {symbol}")
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            self.ws_connections[symbol] = ws
            ws.run_forever()
            
        except Exception as e:
            self.logger.error(f"Error starting WebSocket for {symbol}: {e}")
    
    def _simulate_price_updates(self):
        """Simulate price updates when WebSocket is not available"""
        import random
        
        base_prices = {
            'BTCUSDT': 45000,
            'ETHUSDT': 3000,
            'ADAUSDT': 0.5,
            'DOTUSDT': 25,
            'LINKUSDT': 15
        }
        
        while self.running:
            try:
                for symbol in self.symbols:
                    if symbol not in self.market_data:
                        # Initialize with base price
                        base_price = base_prices.get(symbol, 100)
                        
                        # Add some random variation
                        price_change = random.uniform(-0.02, 0.02)  # ±2%
                        current_price = base_price * (1 + price_change)
                        
                        # Simulate bid/ask spread
                        spread = current_price * 0.001  # 0.1% spread
                        bid = current_price - spread / 2
                        ask = current_price + spread / 2
                        
                        market_data = MarketData(
                            symbol=symbol,
                            price=current_price,
                            bid=bid,
                            ask=ask,
                            volume=random.uniform(1000, 10000),
                            timestamp=datetime.now(),
                            high_24h=current_price * 1.05,
                            low_24h=current_price * 0.95,
                            change_24h=random.uniform(-5, 5)
                        )
                        
                        self.market_data[symbol] = market_data
                        
                        # Notify subscribers
                        for callback in self.subscribers:
                            try:
                                callback(market_data)
                            except Exception as e:
                                self.logger.error(f"Error in simulated data callback: {e}")
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                self.logger.error(f"Error in price simulation: {e}")
                time.sleep(5)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        market_data = self.market_data.get(symbol)
        return market_data.price if market_data else None
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get full market data for symbol"""
        return self.market_data.get(symbol)

class PaperTradingEngine:
    """Main paper trading engine"""
    
    def __init__(self, initial_balance: float = 10000.0, commission_rate: float = 0.001):
        self.logger = logging.getLogger(__name__)
        self.commission_rate = commission_rate
        self.slippage_rate = 0.0005  # 0.05% slippage
        
        # Initialize account
        self.account = PaperAccount(
            balance=initial_balance,
            equity=initial_balance,
            margin_available=initial_balance
        )
        
        # Trading state
        self.orders = {}  # order_id -> PaperOrder
        self.positions = {}  # symbol -> PaperPosition
        self.trades = []  # List of completed trades
        self.order_counter = 0
        
        # Market data
        self.market_data_provider = None
        self.current_prices = {}
        
        # Risk management
        self.risk_manager = AdvancedRiskManager(RiskParameters())
        
        # Performance tracking
        self.equity_history = deque(maxlen=1000)
        self.performance_metrics = {}
        
        # Event callbacks
        self.order_callbacks = []
        self.trade_callbacks = []
        self.position_callbacks = []
        
        # Technical indicators
        self.indicators = TechnicalIndicators()
        
        # Start monitoring thread
        self.running = False
        self.monitor_thread = None
    
    def start(self, symbols: List[str]):
        """Start paper trading engine"""
        try:
            self.logger.info("Starting paper trading engine...")
            
            # Initialize market data provider
            self.market_data_provider = MarketDataProvider(symbols)
            self.market_data_provider.subscribe(self._on_market_data_update)
            self.market_data_provider.start()
            
            # Start monitoring
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_orders_and_positions, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info("Paper trading engine started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting paper trading engine: {e}")
            raise
    
    def stop(self):
        """Stop paper trading engine"""
        try:
            self.logger.info("Stopping paper trading engine...")
            
            self.running = False
            
            if self.market_data_provider:
                self.market_data_provider.stop()
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            self.logger.info("Paper trading engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping paper trading engine: {e}")
    
    def _on_market_data_update(self, market_data: MarketData):
        """Handle market data updates"""
        try:
            self.current_prices[market_data.symbol] = market_data.price
            
            # Update position unrealized PnL
            if market_data.symbol in self.positions:
                position = self.positions[market_data.symbol]
                position.current_price = market_data.price
                
                if position.side == PositionSide.LONG:
                    position.unrealized_pnl = (market_data.price - position.entry_price) * position.quantity
                else:
                    position.unrealized_pnl = (position.entry_price - market_data.price) * position.quantity
                
                position.updated_at = datetime.now()
            
            # Update account equity
            self._update_account_equity()
            
        except Exception as e:
            self.logger.error(f"Error handling market data update: {e}")
    
    def _monitor_orders_and_positions(self):
        """Monitor orders and positions for execution and risk management"""
        while self.running:
            try:
                # Check pending orders
                for order_id, order in list(self.orders.items()):
                    if order.status == OrderStatus.PENDING:
                        self._check_order_execution(order)
                
                # Check position risk management
                for symbol, position in list(self.positions.items()):
                    self._check_position_risk_management(position)
                
                # Update performance metrics
                self._update_performance_metrics()
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.logger.error(f"Error in monitoring thread: {e}")
                time.sleep(1)
    
    def place_order(self, symbol: str, side: str, order_type: OrderType, quantity: float, 
                   price: Optional[float] = None, stop_price: Optional[float] = None) -> str:
        """Place a paper trading order"""
        try:
            # Generate order ID
            self.order_counter += 1
            order_id = f"paper_{int(time.time())}_{self.order_counter}"
            
            # Validate order
            if not self._validate_order(symbol, side, quantity, price):
                raise ValueError("Invalid order parameters")
            
            # Create order
            order = PaperOrder(
                id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price
            )
            
            # Calculate commission
            if order_type == OrderType.MARKET:
                current_price = self.current_prices.get(symbol, price or 0)
                order.commission = current_price * quantity * self.commission_rate
            else:
                order.commission = (price or 0) * quantity * self.commission_rate
            
            # Store order
            self.orders[order_id] = order
            
            # Try immediate execution for market orders
            if order_type == OrderType.MARKET:
                self._execute_market_order(order)
            
            # Notify callbacks
            for callback in self.order_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    self.logger.error(f"Error in order callback: {e}")
            
            self.logger.info(f"Order placed: {order_id} - {side} {quantity} {symbol}")
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        try:
            if order_id not in self.orders:
                return False
            
            order = self.orders[order_id]
            
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                
                self.logger.info(f"Order cancelled: {order_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    def _validate_order(self, symbol: str, side: str, quantity: float, price: Optional[float]) -> bool:
        """Validate order parameters"""
        try:
            # Check quantity
            if quantity <= 0:
                return False
            
            # Check balance for buy orders
            if side.upper() == "BUY":
                current_price = self.current_prices.get(symbol, price or 0)
                required_balance = current_price * quantity * (1 + self.commission_rate)
                
                if required_balance > self.account.margin_available:
                    self.logger.warning(f"Insufficient balance for order: {required_balance} > {self.account.margin_available}")
                    return False
            
            # Check position for sell orders
            elif side.upper() == "SELL":
                position = self.positions.get(symbol)
                if not position or position.quantity < quantity:
                    self.logger.warning(f"Insufficient position for sell order: {symbol}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating order: {e}")
            return False
    
    def _check_order_execution(self, order: PaperOrder):
        """Check if order should be executed"""
        try:
            current_price = self.current_prices.get(order.symbol)
            if not current_price:
                return
            
            should_execute = False
            execution_price = current_price
            
            if order.order_type == OrderType.LIMIT:
                if order.side.upper() == "BUY" and current_price <= order.price:
                    should_execute = True
                    execution_price = order.price
                elif order.side.upper() == "SELL" and current_price >= order.price:
                    should_execute = True
                    execution_price = order.price
            
            elif order.order_type == OrderType.STOP_LOSS:
                if order.side.upper() == "BUY" and current_price >= order.stop_price:
                    should_execute = True
                elif order.side.upper() == "SELL" and current_price <= order.stop_price:
                    should_execute = True
            
            elif order.order_type == OrderType.TAKE_PROFIT:
                if order.side.upper() == "BUY" and current_price <= order.stop_price:
                    should_execute = True
                elif order.side.upper() == "SELL" and current_price >= order.stop_price:
                    should_execute = True
            
            if should_execute:
                self._execute_order(order, execution_price)
                
        except Exception as e:
            self.logger.error(f"Error checking order execution: {e}")
    
    def _execute_market_order(self, order: PaperOrder):
        """Execute market order immediately"""
        try:
            current_price = self.current_prices.get(order.symbol)
            if not current_price:
                order.status = OrderStatus.REJECTED
                order.reason = "No market data available"
                return
            
            # Apply slippage
            if order.side.upper() == "BUY":
                execution_price = current_price * (1 + self.slippage_rate)
            else:
                execution_price = current_price * (1 - self.slippage_rate)
            
            self._execute_order(order, execution_price)
            
        except Exception as e:
            self.logger.error(f"Error executing market order: {e}")
            order.status = OrderStatus.REJECTED
            order.reason = str(e)
    
    def _execute_order(self, order: PaperOrder, execution_price: float):
        """Execute an order"""
        try:
            # Apply slippage
            order.slippage = abs(execution_price - self.current_prices.get(order.symbol, execution_price)) * order.quantity
            
            # Update order
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_fill_price = execution_price
            order.updated_at = datetime.now()
            
            # Update position
            self._update_position(order)
            
            # Update account
            self._update_account_after_execution(order)
            
            # Create trade record
            trade = Trade(
                symbol=order.symbol,
                side=order.side,
                entry_time=order.created_at,
                exit_time=order.updated_at,
                entry_price=execution_price,
                exit_price=execution_price,
                quantity=order.quantity,
                pnl=0.0,  # Will be calculated when position is closed
                pnl_percentage=0.0,
                commission=order.commission,
                slippage=order.slippage,
                reason="order_execution",
                duration=timedelta(0)
            )
            
            self.trades.append(trade)
            
            # Notify callbacks
            for callback in self.trade_callbacks:
                try:
                    callback(trade)
                except Exception as e:
                    self.logger.error(f"Error in trade callback: {e}")
            
            self.logger.info(f"Order executed: {order.id} at {execution_price}")
            
        except Exception as e:
            self.logger.error(f"Error executing order: {e}")
            order.status = OrderStatus.REJECTED
            order.reason = str(e)
    
    def _update_position(self, order: PaperOrder):
        """Update position after order execution"""
        try:
            symbol = order.symbol
            
            if symbol not in self.positions:
                # Create new position
                side = PositionSide.LONG if order.side.upper() == "BUY" else PositionSide.SHORT
                
                position = PaperPosition(
                    symbol=symbol,
                    side=side,
                    quantity=order.quantity,
                    entry_price=order.avg_fill_price,
                    current_price=order.avg_fill_price
                )
                
                self.positions[symbol] = position
                
            else:
                # Update existing position
                position = self.positions[symbol]
                
                if order.side.upper() == "BUY":
                    if position.side == PositionSide.LONG:
                        # Add to long position
                        total_value = (position.quantity * position.entry_price) + (order.quantity * order.avg_fill_price)
                        total_quantity = position.quantity + order.quantity
                        position.entry_price = total_value / total_quantity
                        position.quantity = total_quantity
                    else:
                        # Reduce short position
                        position.quantity -= order.quantity
                        if position.quantity <= 0:
                            del self.positions[symbol]
                            return
                
                else:  # SELL
                    if position.side == PositionSide.SHORT:
                        # Add to short position
                        total_value = (position.quantity * position.entry_price) + (order.quantity * order.avg_fill_price)
                        total_quantity = position.quantity + order.quantity
                        position.entry_price = total_value / total_quantity
                        position.quantity = total_quantity
                    else:
                        # Reduce long position
                        position.quantity -= order.quantity
                        if position.quantity <= 0:
                            del self.positions[symbol]
                            return
                
                position.updated_at = datetime.now()
            
            # Notify callbacks
            if symbol in self.positions:
                for callback in self.position_callbacks:
                    try:
                        callback(self.positions[symbol])
                    except Exception as e:
                        self.logger.error(f"Error in position callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
    
    def _update_account_after_execution(self, order: PaperOrder):
        """Update account after order execution"""
        try:
            # Update trade count
            self.account.total_trades += 1
            
            # Update commission
            self.account.total_commission += order.commission
            
            # Update balance (for buy orders, reduce balance; for sell orders, increase balance)
            if order.side.upper() == "BUY":
                self.account.balance -= (order.avg_fill_price * order.quantity) + order.commission
            else:
                self.account.balance += (order.avg_fill_price * order.quantity) - order.commission
            
            self.account.updated_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error updating account: {e}")
    
    def _check_position_risk_management(self, position: PaperPosition):
        """Check position for risk management triggers"""
        try:
            current_price = position.current_price
            
            # Check stop loss
            if position.stop_loss:
                should_close = False
                
                if position.side == PositionSide.LONG and current_price <= position.stop_loss:
                    should_close = True
                elif position.side == PositionSide.SHORT and current_price >= position.stop_loss:
                    should_close = True
                
                if should_close:
                    self._close_position_at_market(position, "stop_loss")
                    return
            
            # Check take profit
            if position.take_profit:
                should_close = False
                
                if position.side == PositionSide.LONG and current_price >= position.take_profit:
                    should_close = True
                elif position.side == PositionSide.SHORT and current_price <= position.take_profit:
                    should_close = True
                
                if should_close:
                    self._close_position_at_market(position, "take_profit")
                    return
            
            # Check trailing stop
            if position.trailing_stop and position.trailing_stop_distance:
                new_trailing_stop = None
                
                if position.side == PositionSide.LONG:
                    new_trailing_stop = current_price - position.trailing_stop_distance
                    if new_trailing_stop > position.trailing_stop:
                        position.trailing_stop = new_trailing_stop
                    elif current_price <= position.trailing_stop:
                        self._close_position_at_market(position, "trailing_stop")
                        return
                
                else:  # SHORT
                    new_trailing_stop = current_price + position.trailing_stop_distance
                    if new_trailing_stop < position.trailing_stop:
                        position.trailing_stop = new_trailing_stop
                    elif current_price >= position.trailing_stop:
                        self._close_position_at_market(position, "trailing_stop")
                        return
            
        except Exception as e:
            self.logger.error(f"Error checking position risk management: {e}")
    
    def _close_position_at_market(self, position: PaperPosition, reason: str):
        """Close position at market price"""
        try:
            side = "SELL" if position.side == PositionSide.LONG else "BUY"
            
            order_id = self.place_order(
                symbol=position.symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=position.quantity
            )
            
            # Update order reason
            if order_id in self.orders:
                self.orders[order_id].reason = reason
            
            self.logger.info(f"Position closed at market: {position.symbol} - {reason}")
            
        except Exception as e:
            self.logger.error(f"Error closing position at market: {e}")
    
    def _update_account_equity(self):
        """Update account equity with unrealized PnL"""
        try:
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            self.account.unrealized_pnl = total_unrealized_pnl
            self.account.equity = self.account.balance + total_unrealized_pnl
            self.account.margin_available = self.account.equity * 0.8  # 80% margin available
            
            # Add to equity history
            self.equity_history.append({
                'timestamp': datetime.now(),
                'equity': self.account.equity,
                'balance': self.account.balance,
                'unrealized_pnl': total_unrealized_pnl
            })
            
        except Exception as e:
            self.logger.error(f"Error updating account equity: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            if len(self.equity_history) < 2:
                return
            
            # Calculate returns
            equity_values = [entry['equity'] for entry in self.equity_history]
            returns = [(equity_values[i] / equity_values[i-1]) - 1 for i in range(1, len(equity_values))]
            
            if returns:
                # Basic metrics
                total_return = (equity_values[-1] / equity_values[0]) - 1
                avg_return = sum(returns) / len(returns)
                volatility = (sum([(r - avg_return) ** 2 for r in returns]) / len(returns)) ** 0.5
                
                # Sharpe ratio (assuming 2% risk-free rate)
                risk_free_rate = 0.02 / 365  # Daily risk-free rate
                sharpe_ratio = (avg_return - risk_free_rate) / volatility if volatility > 0 else 0
                
                # Drawdown
                peak = max(equity_values)
                current_drawdown = (peak - equity_values[-1]) / peak if peak > 0 else 0
                
                # Win rate
                winning_trades = len([t for t in self.trades if t.pnl > 0])
                win_rate = winning_trades / len(self.trades) if self.trades else 0
                
                self.performance_metrics = {
                    'total_return': total_return,
                    'avg_daily_return': avg_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'current_drawdown': current_drawdown,
                    'win_rate': win_rate,
                    'total_trades': len(self.trades),
                    'equity': equity_values[-1],
                    'balance': self.account.balance
                }
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    # Public API methods
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information"""
        return asdict(self.account)
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions"""
        return {symbol: asdict(position) for symbol, position in self.positions.items()}
    
    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Dict[str, Any]]:
        """Get orders, optionally filtered by status"""
        orders = list(self.orders.values())
        
        if status:
            orders = [order for order in orders if order.status == status]
        
        return [asdict(order) for order in orders]
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """Get trade history"""
        return [asdict(trade) for trade in self.trades]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """Get equity curve data"""
        return list(self.equity_history)
    
    def set_position_stop_loss(self, symbol: str, stop_loss: float) -> bool:
        """Set stop loss for position"""
        if symbol in self.positions:
            self.positions[symbol].stop_loss = stop_loss
            return True
        return False
    
    def set_position_take_profit(self, symbol: str, take_profit: float) -> bool:
        """Set take profit for position"""
        if symbol in self.positions:
            self.positions[symbol].take_profit = take_profit
            return True
        return False
    
    def set_position_trailing_stop(self, symbol: str, distance: float) -> bool:
        """Set trailing stop for position"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.trailing_stop_distance = distance
            
            # Initialize trailing stop
            if position.side == PositionSide.LONG:
                position.trailing_stop = position.current_price - distance
            else:
                position.trailing_stop = position.current_price + distance
            
            return True
        return False
    
    def close_position(self, symbol: str) -> bool:
        """Close position at market price"""
        if symbol in self.positions:
            position = self.positions[symbol]
            self._close_position_at_market(position, "manual_close")
            return True
        return False
    
    def close_all_positions(self) -> int:
        """Close all positions at market price"""
        closed_count = 0
        
        for symbol in list(self.positions.keys()):
            if self.close_position(symbol):
                closed_count += 1
        
        return closed_count
    
    def reset_account(self, initial_balance: float = 10000.0):
        """Reset account to initial state"""
        try:
            # Close all positions
            self.close_all_positions()
            
            # Cancel all pending orders
            for order_id in list(self.orders.keys()):
                self.cancel_order(order_id)
            
            # Reset account
            self.account = PaperAccount(
                balance=initial_balance,
                equity=initial_balance,
                margin_available=initial_balance
            )
            
            # Clear data
            self.orders.clear()
            self.positions.clear()
            self.trades.clear()
            self.equity_history.clear()
            self.performance_metrics.clear()
            self.order_counter = 0
            
            self.logger.info(f"Account reset with balance: ${initial_balance}")
            
        except Exception as e:
            self.logger.error(f"Error resetting account: {e}")
    
    # Callback registration
    
    def on_order_update(self, callback: Callable[[PaperOrder], None]):
        """Register callback for order updates"""
        self.order_callbacks.append(callback)
    
    def on_trade(self, callback: Callable[[Trade], None]):
        """Register callback for trade events"""
        self.trade_callbacks.append(callback)
    
    def on_position_update(self, callback: Callable[[PaperPosition], None]):
        """Register callback for position updates"""
        self.position_callbacks.append(callback)

# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create paper trading engine
    engine = PaperTradingEngine(initial_balance=10000.0)
    
    # Register callbacks
    def on_trade_callback(trade):
        print(f"Trade executed: {trade.symbol} {trade.side} {trade.quantity} @ {trade.entry_price}")
    
    def on_position_callback(position):
        print(f"Position updated: {position.symbol} {position.side.value} {position.quantity} PnL: {position.unrealized_pnl:.2f}")
    
    engine.on_trade(on_trade_callback)
    engine.on_position_update(on_position_callback)
    
    # Start engine
    symbols = ["BTCUSDT", "ETHUSDT"]
    engine.start(symbols)
    
    try:
        # Wait for market data
        time.sleep(2)
        
        # Place some test orders
        print("\nPlacing test orders...")
        
        # Market buy order
        order_id1 = engine.place_order("BTCUSDT", "BUY", OrderType.MARKET, 0.1)
        print(f"Market buy order placed: {order_id1}")
        
        time.sleep(1)
        
        # Limit sell order
        current_price = engine.current_prices.get("BTCUSDT", 45000)
        limit_price = current_price * 1.02  # 2% above current price
        
        order_id2 = engine.place_order("BTCUSDT", "SELL", OrderType.LIMIT, 0.05, limit_price)
        print(f"Limit sell order placed: {order_id2} at {limit_price}")
        
        # Set stop loss for position
        stop_loss_price = current_price * 0.95  # 5% below current price
        engine.set_position_stop_loss("BTCUSDT", stop_loss_price)
        print(f"Stop loss set at {stop_loss_price}")
        
        # Monitor for a while
        print("\nMonitoring for 30 seconds...")
        for i in range(30):
            time.sleep(1)
            
            if i % 5 == 0:  # Print status every 5 seconds
                account = engine.get_account_info()
                positions = engine.get_positions()
                metrics = engine.get_performance_metrics()
                
                print(f"\nStatus at {i}s:")
                print(f"  Equity: ${account['equity']:.2f}")
                print(f"  Positions: {len(positions)}")
                print(f"  Total Return: {metrics.get('total_return', 0):.2%}")
        
        # Final status
        print("\nFinal Status:")
        account = engine.get_account_info()
        positions = engine.get_positions()
        trades = engine.get_trades()
        metrics = engine.get_performance_metrics()
        
        print(f"Account: {account}")
        print(f"Positions: {len(positions)}")
        print(f"Trades: {len(trades)}")
        print(f"Performance: {metrics}")
        
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        engine.stop()
        print("Paper trading engine stopped")