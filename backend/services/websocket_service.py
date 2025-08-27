from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from functools import wraps
import json
import logging
from datetime import datetime
from typing import Optional
from models import User, Bot, Trade
from db import db
from sqlalchemy import func
from utils.logger import get_logger

logger = get_logger(__name__)

class WebSocketService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.connected_users = {}  # session_id -> user_id
        self.user_subscriptions = {}  # user_id -> set of symbols
        self.realtime_service = None  # Will be set by app initialization
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Get user info from auth token or session
                user_id = auth.get('user_id') if auth else None
                if user_id:
                    self.connected_users[request.sid] = user_id
                    join_room(f'user_{user_id}')
                    logger.info(f"User {user_id} connected with session {request.sid}")
                    
                    # Send initial dashboard data
                    self.send_dashboard_update(user_id)
                else:
                    logger.warning(f"Unauthenticated connection attempt: {request.sid}")
                    return False
            except Exception as e:
                logger.error(f"Connection error: {str(e)}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                user_id = self.connected_users.get(request.sid)
                if user_id:
                    # Unsubscribe from all symbols
                    if user_id in self.user_subscriptions and self.realtime_service:
                        for symbol in list(self.user_subscriptions[user_id]):
                            self.realtime_service.unsubscribe_user_from_symbol(user_id, symbol)
                    
                    # Clean up
                    leave_room(f'user_{user_id}')
                    del self.connected_users[request.sid]
                    if user_id in self.user_subscriptions:
                        del self.user_subscriptions[user_id]
                    
                    logger.info(f"User {user_id} disconnected")
            except Exception as e:
                logger.error(f"Disconnection error: {str(e)}")
        
        @self.socketio.on('subscribe_to_symbol')
        def handle_symbol_subscription(data):
            """Handle symbol subscription for real-time price updates"""
            try:
                symbol = data.get('symbol', '').upper()
                user_id = self.connected_users.get(request.sid)
                
                if user_id and symbol:
                    # Join symbol room
                    join_room(f'symbol_{symbol}')
                    
                    # Track user subscription
                    if user_id not in self.user_subscriptions:
                        self.user_subscriptions[user_id] = set()
                    self.user_subscriptions[user_id].add(symbol)
                    
                    # Subscribe to real-time data service
                    if self.realtime_service:
                        success = self.realtime_service.subscribe_user_to_symbol(user_id, symbol)
                        if success:
                            # Send current price if available
                            current_price = self.realtime_service.get_current_price(symbol)
                            if current_price:
                                emit('price_update', {
                                    'symbol': symbol,
                                    'data': current_price,
                                    'timestamp': datetime.utcnow().isoformat()
                                })
                    
                    logger.info(f"User {user_id} subscribed to {symbol}")
                    emit('subscription_confirmed', {
                        'symbol': symbol,
                        'status': 'success'
                    })
                else:
                    emit('subscription_error', {
                        'symbol': symbol,
                        'error': 'Invalid symbol or user not authenticated'
                    })
            except Exception as e:
                logger.error(f"Symbol subscription error: {str(e)}")
                emit('subscription_error', {
                    'symbol': data.get('symbol', ''),
                    'error': str(e)
                })
        
        @self.socketio.on('unsubscribe_from_symbol')
        def handle_symbol_unsubscription(data):
            """Handle symbol unsubscription"""
            try:
                symbol = data.get('symbol', '').upper()
                user_id = self.connected_users.get(request.sid)
                
                if user_id and symbol:
                    # Leave symbol room
                    leave_room(f'symbol_{symbol}')
                    
                    # Remove from user subscriptions
                    if user_id in self.user_subscriptions:
                        self.user_subscriptions[user_id].discard(symbol)
                    
                    # Unsubscribe from real-time data service
                    if self.realtime_service:
                        self.realtime_service.unsubscribe_user_from_symbol(user_id, symbol)
                    
                    logger.info(f"User {user_id} unsubscribed from {symbol}")
                    emit('unsubscription_confirmed', {
                        'symbol': symbol,
                        'status': 'success'
                    })
            except Exception as e:
                logger.error(f"Symbol unsubscription error: {str(e)}")
                emit('unsubscription_error', {
                    'symbol': data.get('symbol', ''),
                    'error': str(e)
                })
        
        @self.socketio.on('get_portfolio_update')
        def handle_portfolio_update_request(data):
            """Handle request for portfolio update"""
            try:
                user_id = self.connected_users.get(request.sid)
                
                if user_id:
                    if self.realtime_service:
                        # Force portfolio update
                        self.realtime_service.force_portfolio_update(user_id)
                        
                        # Get cached portfolio data
                        portfolio_data = self.realtime_service.get_portfolio_data(user_id)
                        if portfolio_data:
                            emit('portfolio_update', portfolio_data)
                        else:
                            # Fallback to dashboard update
                            self.send_dashboard_update(user_id)
                    else:
                        self.send_dashboard_update(user_id)
            except Exception as e:
                logger.error(f"Portfolio update request error: {str(e)}")
                emit('portfolio_error', {'error': str(e)})
        
        @self.socketio.on('get_price_history')
        def handle_price_history_request(data):
            """Handle request for price history"""
            try:
                symbol = data.get('symbol', '').upper()
                limit = data.get('limit', 100)
                user_id = self.connected_users.get(request.sid)
                
                if user_id and symbol and self.realtime_service:
                    history = self.realtime_service.get_price_history(symbol, limit)
                    emit('price_history', {
                        'symbol': symbol,
                        'history': history,
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.error(f"Price history request error: {str(e)}")
                emit('price_history_error', {
                    'symbol': data.get('symbol', ''),
                    'error': str(e)
                })
    
    def send_dashboard_update(self, user_id):
        """Send dashboard data update to specific user"""
        try:
            # Get user's bots
            bots = Bot.query.filter_by(user_id=user_id).all()
            
            # Get recent trades
            recent_trades = Trade.query.filter(
                Trade.bot_id.in_([bot.id for bot in bots])
            ).order_by(Trade.timestamp.desc()).limit(10).all()
            
            # Calculate portfolio metrics
            total_pnl = sum(trade.pnl for trade in recent_trades if trade.pnl)
            active_bots = len([bot for bot in bots if bot.status == 'running'])
            
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'portfolio': {
                    'total_pnl': total_pnl,
                    'active_bots': active_bots,
                    'total_bots': len(bots)
                },
                'bots': [{
                    'id': bot.id,
                    'name': bot.name,
                    'status': bot.status,
                    'strategy': bot.strategy,
                    'updated_at': bot.updated_at.isoformat() if bot.updated_at else None
                } for bot in bots],
                'recent_trades': [{
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': float(trade.quantity),
                    'price': float(trade.price),
                    'pnl': float(trade.pnl) if trade.pnl else 0,
                    'timestamp': trade.timestamp.isoformat()
                } for trade in recent_trades]
            }
            
            self.socketio.emit('dashboard_update', dashboard_data, room=f'user_{user_id}')
            
        except Exception as e:
            logger.error(f"Error sending dashboard update to user {user_id}: {str(e)}")
    
    def broadcast_price_update(self, symbol, price_data):
        """Broadcast price update to all subscribers of a symbol"""
        try:
            self.socketio.emit('price_update', {
                'symbol': symbol,
                'data': price_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'symbol_{symbol}')
        except Exception as e:
            logger.error(f"Error broadcasting price update for {symbol}: {str(e)}")
    
    def send_bot_status_update(self, user_id, bot_id, status, message=None):
        """Send bot status update to specific user"""
        try:
            update_data = {
                'bot_id': bot_id,
                'status': status,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('bot_status_update', update_data, room=f'user_{user_id}')
            
        except Exception as e:
            logger.error(f"Error sending bot status update: {str(e)}")
    
    def send_trade_notification(self, user_id, trade_data):
        """Send trade notification to specific user"""
        try:
            notification_data = {
                'type': 'trade',
                'data': trade_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('trade_notification', notification_data, room=f'user_{user_id}')
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {str(e)}")
    
    def broadcast_market_alert(self, alert_data):
        """Broadcast market alert to all connected users"""
        try:
            self.socketio.emit('market_alert', {
                'data': alert_data,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        except Exception as e:
            logger.error(f"Error broadcasting market alert: {str(e)}")
    
    def set_realtime_service(self, realtime_service):
        """Set the real-time data service reference."""
        self.realtime_service = realtime_service
        logger.info("Real-time data service connected to WebSocket service")
    
    def send_portfolio_update(self, user_id: int, portfolio_data: dict):
        """Send portfolio update to specific user."""
        try:
            self.socketio.emit('portfolio_update', portfolio_data, room=f'user_{user_id}')
        except Exception as e:
            logger.error(f"Error sending portfolio update to user {user_id}: {str(e)}")
    
    def send_price_alert(self, user_id: int, alert_data: dict):
        """Send price alert to specific user."""
        try:
            self.socketio.emit('price_alert', {
                'data': alert_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'user_{user_id}')
        except Exception as e:
            logger.error(f"Error sending price alert to user {user_id}: {str(e)}")
    
    def broadcast_system_status(self, status_data: dict):
        """Broadcast system status update to all connected users."""
        try:
            self.socketio.emit('system_status', {
                'data': status_data,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        except Exception as e:
            logger.error(f"Error broadcasting system status: {str(e)}")
    
    def get_connected_users_count(self) -> int:
        """Get count of connected users."""
        return len(set(self.connected_users.values()))
    
    def get_user_subscriptions(self, user_id: int) -> set:
        """Get symbols subscribed by a user."""
        return self.user_subscriptions.get(user_id, set())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user is currently connected."""
        return user_id in self.connected_users.values()
    
    def send_connection_stats(self):
        """Send connection statistics to all connected users."""
        try:
            stats = {
                'connected_users': self.get_connected_users_count(),
                'total_connections': len(self.connected_users),
                'active_subscriptions': sum(len(subs) for subs in self.user_subscriptions.values()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('connection_stats', stats, broadcast=True)
        except Exception as e:
            logger.error(f"Error sending connection stats: {str(e)}")
    
    def send_notification_to_user(self, user_id: int, notification_data: dict):
        """Send notification to a specific user"""
        try:
            if self.is_user_connected(user_id):
                self.socketio.emit('notification', notification_data, room=f'user_{user_id}')
                logger.info(f'Sent notification to user {user_id}: {notification_data.get("event_type")}')
                return True
            else:
                logger.debug(f'User {user_id} not connected for notification')
                return False
        except Exception as e:
            logger.error(f'Error sending notification to user {user_id}: {e}')
            return False
    
    def send_system_alert(self, user_id: int, alert_data: dict):
        """Send system alert notification"""
        try:
            if self.is_user_connected(user_id):
                self.socketio.emit('system_alert', alert_data, room=f'user_{user_id}')
                logger.info(f'Sent system alert to user {user_id}: {alert_data.get("alert_type")}')
                return True
            else:
                logger.debug(f'User {user_id} not connected for system alert')
                return False
        except Exception as e:
            logger.error(f'Error sending system alert to user {user_id}: {e}')
            return False
    
    def broadcast_to_all_users(self, event_name: str, data: dict):
        """Broadcast message to all connected users"""
        try:
            self.socketio.emit(event_name, data, broadcast=True)
            logger.info(f'Broadcasted {event_name} to all users')
        except Exception as e:
            logger.error(f'Error broadcasting {event_name}: {e}')
    
    def get_connected_user_ids(self) -> list:
        """Get list of currently connected user IDs"""
        return list(set(self.connected_users.values()))
    
    def disconnect_user(self, user_id: int):
        """Disconnect all sessions for a specific user"""
        try:
            sessions_to_disconnect = [sid for sid, uid in self.connected_users.items() if uid == user_id]
            for session_id in sessions_to_disconnect:
                self.socketio.disconnect(session_id)
            logger.info(f'Disconnected all sessions for user {user_id}')
        except Exception as e:
            logger.error(f'Error disconnecting user {user_id}: {e}')