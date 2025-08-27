"""Real-time data service for WebSocket streaming of market data and P/L updates."""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from threading import Thread, Lock
from collections import defaultdict, deque

import websocket
import requests
from flask import current_app
from sqlalchemy import func

from models import User, Bot, Trade, APIKey
from db import db
from services.websocket_service import WebSocketService
from bot_engine.exchange_factory import ExchangeFactory
from utils.logger import get_logger

logger = get_logger(__name__)

class RealTimeDataService:
    """Service for managing real-time market data streams and P/L updates."""
    
    def __init__(self, websocket_service: WebSocketService):
        self.websocket_service = websocket_service
        self.exchange_factory = ExchangeFactory()
        
        # Connection management
        self.active_streams = {}  # symbol -> websocket connection
        self.subscribed_symbols = set()  # symbols being streamed
        self.user_subscriptions = defaultdict(set)  # user_id -> set of symbols
        
        # Data storage
        self.price_cache = {}  # symbol -> latest price data
        self.price_history = defaultdict(lambda: deque(maxlen=1000))  # symbol -> price history
        self.portfolio_cache = {}  # user_id -> portfolio data
        
        # Threading
        self.stream_threads = {}
        self.update_thread = None
        self.is_running = False
        self.lock = Lock()
        
        # Configuration
        self.update_interval = 1.0  # seconds
        self.price_change_threshold = 0.001  # 0.1% change threshold for notifications
        
    def start(self):
        """Start the real-time data service."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start portfolio update thread
        self.update_thread = Thread(target=self._portfolio_update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("Real-time data service started")
    
    def stop(self):
        """Stop the real-time data service."""
        self.is_running = False
        
        # Stop all streams
        for symbol in list(self.active_streams.keys()):
            self.stop_price_stream(symbol)
            
        # Wait for threads to finish
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
            
        logger.info("Real-time data service stopped")
    
    def subscribe_user_to_symbol(self, user_id: int, symbol: str) -> bool:
        """Subscribe a user to real-time price updates for a symbol."""
        try:
            with self.lock:
                self.user_subscriptions[user_id].add(symbol.upper())
                
            # Start price stream if not already active
            if symbol.upper() not in self.subscribed_symbols:
                success = self.start_price_stream(symbol.upper())
                if not success:
                    return False
                    
            logger.info(f"User {user_id} subscribed to {symbol.upper()}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing user {user_id} to {symbol}: {str(e)}")
            return False
    
    def unsubscribe_user_from_symbol(self, user_id: int, symbol: str) -> bool:
        """Unsubscribe a user from real-time price updates for a symbol."""
        try:
            with self.lock:
                self.user_subscriptions[user_id].discard(symbol.upper())
                
                # Check if any users are still subscribed to this symbol
                still_subscribed = any(
                    symbol.upper() in symbols 
                    for symbols in self.user_subscriptions.values()
                )
                
                # Stop stream if no users are subscribed
                if not still_subscribed:
                    self.stop_price_stream(symbol.upper())
                    
            logger.info(f"User {user_id} unsubscribed from {symbol.upper()}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing user {user_id} from {symbol}: {str(e)}")
            return False
    
    def start_price_stream(self, symbol: str) -> bool:
        """Start real-time price stream for a symbol."""
        try:
            symbol = symbol.upper()
            
            if symbol in self.active_streams:
                logger.info(f"Price stream for {symbol} already active")
                return True
                
            # Create Binance WebSocket stream
            stream_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@ticker"
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    self._process_price_update(symbol, data)
                except Exception as e:
                    logger.error(f"Error processing price update for {symbol}: {str(e)}")
            
            def on_error(ws, error):
                logger.error(f"WebSocket error for {symbol}: {str(error)}")
                self._reconnect_stream(symbol)
            
            def on_close(ws, close_status_code, close_msg):
                logger.info(f"WebSocket closed for {symbol}: {close_status_code} - {close_msg}")
                if self.is_running and symbol in self.subscribed_symbols:
                    self._reconnect_stream(symbol)
            
            def on_open(ws):
                logger.info(f"WebSocket opened for {symbol}")
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                stream_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Start stream in separate thread
            stream_thread = Thread(
                target=ws.run_forever,
                kwargs={'ping_interval': 20, 'ping_timeout': 10},
                daemon=True
            )
            stream_thread.start()
            
            # Store connection and thread
            self.active_streams[symbol] = ws
            self.stream_threads[symbol] = stream_thread
            self.subscribed_symbols.add(symbol)
            
            logger.info(f"Started price stream for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting price stream for {symbol}: {str(e)}")
            return False
    
    def stop_price_stream(self, symbol: str):
        """Stop real-time price stream for a symbol."""
        try:
            symbol = symbol.upper()
            
            if symbol in self.active_streams:
                # Close WebSocket connection
                ws = self.active_streams[symbol]
                ws.close()
                
                # Clean up
                del self.active_streams[symbol]
                self.subscribed_symbols.discard(symbol)
                
                if symbol in self.stream_threads:
                    del self.stream_threads[symbol]
                    
                logger.info(f"Stopped price stream for {symbol}")
                
        except Exception as e:
            logger.error(f"Error stopping price stream for {symbol}: {str(e)}")
    
    def _process_price_update(self, symbol: str, data: dict):
        """Process incoming price update from WebSocket."""
        try:
            # Extract price data from Binance ticker format
            price_data = {
                'symbol': symbol,
                'price': float(data.get('c', 0)),  # Current price
                'change': float(data.get('P', 0)),  # Price change percentage
                'volume': float(data.get('v', 0)),  # Volume
                'high': float(data.get('h', 0)),  # 24h high
                'low': float(data.get('l', 0)),  # 24h low
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Update cache
            old_price = self.price_cache.get(symbol, {}).get('price', 0)
            self.price_cache[symbol] = price_data
            self.price_history[symbol].append({
                'price': price_data['price'],
                'timestamp': price_data['timestamp']
            })
            
            # Broadcast price update to subscribers
            self.websocket_service.broadcast_price_update(symbol, price_data)
            
            # Check for significant price changes
            if old_price > 0:
                change_pct = abs(price_data['price'] - old_price) / old_price
                if change_pct >= self.price_change_threshold:
                    self._send_price_alert(symbol, price_data, change_pct)
                    
        except Exception as e:
            logger.error(f"Error processing price update for {symbol}: {str(e)}")
    
    def _send_price_alert(self, symbol: str, price_data: dict, change_pct: float):
        """Send price alert for significant price changes."""
        try:
            alert_data = {
                'type': 'price_alert',
                'symbol': symbol,
                'price': price_data['price'],
                'change_percent': change_pct * 100,
                'timestamp': price_data['timestamp']
            }
            
            self.websocket_service.broadcast_market_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Error sending price alert for {symbol}: {str(e)}")
    
    def _reconnect_stream(self, symbol: str):
        """Reconnect WebSocket stream after connection loss."""
        try:
            logger.info(f"Reconnecting stream for {symbol}")
            
            # Wait before reconnecting
            time.sleep(5)
            
            # Clean up old connection
            if symbol in self.active_streams:
                del self.active_streams[symbol]
            if symbol in self.stream_threads:
                del self.stream_threads[symbol]
                
            # Restart stream if still needed
            if symbol in self.subscribed_symbols and self.is_running:
                self.start_price_stream(symbol)
                
        except Exception as e:
            logger.error(f"Error reconnecting stream for {symbol}: {str(e)}")
    
    def _portfolio_update_loop(self):
        """Background thread for updating portfolio P/L data."""
        while self.is_running:
            try:
                self._update_all_portfolios()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in portfolio update loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def _update_all_portfolios(self):
        """Update P/L data for all active users."""
        try:
            # Get all users with active bots
            active_users = db.session.query(User.id).join(Bot).filter(
                Bot.is_active == True
            ).distinct().all()
            
            for (user_id,) in active_users:
                self._update_user_portfolio(user_id)
                
        except Exception as e:
            logger.error(f"Error updating all portfolios: {str(e)}")
    
    def _update_user_portfolio(self, user_id: int):
        """Update portfolio data for a specific user."""
        try:
            # Get user's bots and trades
            bots = Bot.query.filter_by(user_id=user_id, is_active=True).all()
            
            if not bots:
                return
                
            # Calculate portfolio metrics
            total_pnl = 0
            total_value = 0
            positions = {}
            
            for bot in bots:
                # Get recent trades for this bot
                trades = Trade.query.filter_by(bot_id=bot.id).order_by(
                    Trade.timestamp.desc()
                ).limit(100).all()
                
                bot_pnl = sum(trade.pnl for trade in trades if trade.pnl)
                total_pnl += bot_pnl
                
                # Calculate current positions
                for trade in trades:
                    symbol = trade.symbol
                    if symbol not in positions:
                        positions[symbol] = {'quantity': 0, 'avg_price': 0, 'pnl': 0}
                    
                    # Update position (simplified calculation)
                    if trade.side == 'buy':
                        positions[symbol]['quantity'] += trade.quantity
                    else:
                        positions[symbol]['quantity'] -= trade.quantity
                    
                    positions[symbol]['pnl'] += trade.pnl or 0
            
            # Calculate current portfolio value using latest prices
            for symbol, position in positions.items():
                if position['quantity'] > 0 and symbol in self.price_cache:
                    current_price = self.price_cache[symbol]['price']
                    position_value = position['quantity'] * current_price
                    total_value += position_value
            
            # Create portfolio update
            portfolio_data = {
                'user_id': user_id,
                'total_pnl': total_pnl,
                'total_value': total_value,
                'positions': positions,
                'active_bots': len(bots),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Cache and broadcast update
            self.portfolio_cache[user_id] = portfolio_data
            self.websocket_service.socketio.emit(
                'portfolio_update', 
                portfolio_data, 
                room=f'user_{user_id}'
            )
            
        except Exception as e:
            logger.error(f"Error updating portfolio for user {user_id}: {str(e)}")
    
    def get_price_history(self, symbol: str, limit: int = 100) -> List[dict]:
        """Get price history for a symbol."""
        try:
            symbol = symbol.upper()
            history = list(self.price_history.get(symbol, []))
            return history[-limit:] if limit else history
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {str(e)}")
            return []
    
    def get_current_price(self, symbol: str) -> Optional[dict]:
        """Get current price data for a symbol."""
        try:
            return self.price_cache.get(symbol.upper())
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    def get_portfolio_data(self, user_id: int) -> Optional[dict]:
        """Get cached portfolio data for a user."""
        try:
            return self.portfolio_cache.get(user_id)
        except Exception as e:
            logger.error(f"Error getting portfolio data for user {user_id}: {str(e)}")
            return None
    
    def get_active_subscriptions(self) -> Dict[str, int]:
        """Get count of active subscriptions per symbol."""
        try:
            subscriptions = {}
            for user_symbols in self.user_subscriptions.values():
                for symbol in user_symbols:
                    subscriptions[symbol] = subscriptions.get(symbol, 0) + 1
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting active subscriptions: {str(e)}")
            return {}
    
    def force_portfolio_update(self, user_id: int):
        """Force immediate portfolio update for a user."""
        try:
            self._update_user_portfolio(user_id)
        except Exception as e:
            logger.error(f"Error forcing portfolio update for user {user_id}: {str(e)}")