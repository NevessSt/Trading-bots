from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from functools import wraps
import json
import logging
from datetime import datetime
from models import User, Bot, Trade
from db import db
from sqlalchemy import func

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.connected_users = {}
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
                    leave_room(f'user_{user_id}')
                    del self.connected_users[request.sid]
                    logger.info(f"User {user_id} disconnected")
            except Exception as e:
                logger.error(f"Disconnection error: {str(e)}")
        
        @self.socketio.on('subscribe_to_symbol')
        def handle_symbol_subscription(data):
            """Handle symbol subscription for real-time price updates"""
            try:
                symbol = data.get('symbol')
                user_id = self.connected_users.get(request.sid)
                
                if user_id and symbol:
                    join_room(f'symbol_{symbol}')
                    logger.info(f"User {user_id} subscribed to {symbol}")
                    emit('subscription_confirmed', {'symbol': symbol})
            except Exception as e:
                logger.error(f"Symbol subscription error: {str(e)}")
        
        @self.socketio.on('unsubscribe_from_symbol')
        def handle_symbol_unsubscription(data):
            """Handle symbol unsubscription"""
            try:
                symbol = data.get('symbol')
                user_id = self.connected_users.get(request.sid)
                
                if user_id and symbol:
                    leave_room(f'symbol_{symbol}')
                    logger.info(f"User {user_id} unsubscribed from {symbol}")
                    emit('unsubscription_confirmed', {'symbol': symbol})
            except Exception as e:
                logger.error(f"Symbol unsubscription error: {str(e)}")
    
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