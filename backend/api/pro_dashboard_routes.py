from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Bot, Trade, APIKey
from db import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import logging

logger = logging.getLogger(__name__)

# Create blueprint
pro_dashboard_bp = Blueprint('pro_dashboard', __name__)

@pro_dashboard_bp.route('/api/pro-dashboard/overview', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    """Get comprehensive dashboard overview with real-time metrics"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's bots
        bots = Bot.query.filter_by(user_id=user_id).all()
        
        # Get trades from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_trades = Trade.query.filter(
            Trade.bot_id.in_([bot.id for bot in bots]),
            Trade.timestamp >= thirty_days_ago
        ).order_by(desc(Trade.timestamp)).all()
        
        # Calculate metrics
        total_pnl = sum(float(trade.pnl) for trade in recent_trades if trade.pnl)
        total_volume = sum(float(trade.quantity) * float(trade.price) for trade in recent_trades)
        active_bots = len([bot for bot in bots if bot.status == 'running'])
        
        # Calculate daily PnL for chart
        daily_pnl = {}
        for trade in recent_trades:
            date_key = trade.timestamp.date().isoformat()
            if date_key not in daily_pnl:
                daily_pnl[date_key] = 0
            daily_pnl[date_key] += float(trade.pnl) if trade.pnl else 0
        
        # Get top performing symbols
        symbol_performance = {}
        for trade in recent_trades:
            if trade.symbol not in symbol_performance:
                symbol_performance[trade.symbol] = {'pnl': 0, 'trades': 0, 'volume': 0}
            symbol_performance[trade.symbol]['pnl'] += float(trade.pnl) if trade.pnl else 0
            symbol_performance[trade.symbol]['trades'] += 1
            symbol_performance[trade.symbol]['volume'] += float(trade.quantity) * float(trade.price)
        
        # Sort by PnL
        top_symbols = sorted(symbol_performance.items(), key=lambda x: x[1]['pnl'], reverse=True)[:5]
        
        # Calculate win rate
        winning_trades = len([trade for trade in recent_trades if trade.pnl and float(trade.pnl) > 0])
        total_trades = len(recent_trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Get recent activity
        recent_activity = [{
            'id': trade.id,
            'type': 'trade',
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': float(trade.quantity),
            'price': float(trade.price),
            'pnl': float(trade.pnl) if trade.pnl else 0,
            'timestamp': trade.timestamp.isoformat(),
            'bot_name': next((bot.name for bot in bots if bot.id == trade.bot_id), 'Unknown')
        } for trade in recent_trades[:10]]
        
        overview_data = {
            'portfolio': {
                'total_pnl': total_pnl,
                'total_volume': total_volume,
                'active_bots': active_bots,
                'total_bots': len(bots),
                'win_rate': win_rate,
                'total_trades': total_trades
            },
            'charts': {
                'daily_pnl': [{'date': date, 'pnl': pnl} for date, pnl in sorted(daily_pnl.items())],
                'top_symbols': [{
                    'symbol': symbol,
                    'pnl': data['pnl'],
                    'trades': data['trades'],
                    'volume': data['volume']
                } for symbol, data in top_symbols]
            },
            'recent_activity': recent_activity,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(overview_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard overview'}), 500

@pro_dashboard_bp.route('/api/pro-dashboard/real-time-metrics', methods=['GET'])
@jwt_required()
def get_real_time_metrics():
    """Get real-time trading metrics"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's bots
        bots = Bot.query.filter_by(user_id=user_id).all()
        
        # Get trades from last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_trades = Trade.query.filter(
            Trade.bot_id.in_([bot.id for bot in bots]),
            Trade.timestamp >= twenty_four_hours_ago
        ).all()
        
        # Calculate real-time metrics
        daily_pnl = sum(float(trade.pnl) for trade in recent_trades if trade.pnl)
        daily_volume = sum(float(trade.quantity) * float(trade.price) for trade in recent_trades)
        daily_trades = len(recent_trades)
        
        # Get active positions (simplified - in real implementation, this would come from exchange)
        active_positions = []
        for bot in bots:
            if bot.status == 'running':
                # This is a placeholder - in real implementation, get actual positions from exchange
                active_positions.append({
                    'bot_id': bot.id,
                    'bot_name': bot.name,
                    'symbol': bot.symbol if hasattr(bot, 'symbol') else 'BTCUSDT',
                    'side': 'long',  # Placeholder
                    'size': 0.1,     # Placeholder
                    'entry_price': 50000,  # Placeholder
                    'current_price': 51000,  # Placeholder
                    'unrealized_pnl': 100,   # Placeholder
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        metrics_data = {
            'daily_metrics': {
                'pnl': daily_pnl,
                'volume': daily_volume,
                'trades': daily_trades,
                'active_positions': len(active_positions)
            },
            'active_positions': active_positions,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(metrics_data)
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        return jsonify({'error': 'Failed to get real-time metrics'}), 500

@pro_dashboard_bp.route('/api/pro-dashboard/market-data/<symbol>', methods=['GET'])
@jwt_required()
def get_market_data(symbol):
    """Get market data for a specific symbol"""
    try:
        # Get timeframe from query params
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 100))
        
        # In a real implementation, this would fetch from the trading engine
        # For now, return mock data
        mock_data = {
            'symbol': symbol,
            'timeframe': timeframe,
            'data': [
                {
                    'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    'open': 50000 + (i * 10),
                    'high': 50100 + (i * 10),
                    'low': 49900 + (i * 10),
                    'close': 50050 + (i * 10),
                    'volume': 1000 + (i * 5)
                } for i in range(limit, 0, -1)
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(mock_data)
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        return jsonify({'error': 'Failed to get market data'}), 500

@pro_dashboard_bp.route('/api/pro-dashboard/risk-metrics', methods=['GET'])
@jwt_required()
def get_risk_metrics():
    """Get risk management metrics"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's bots and trades
        bots = Bot.query.filter_by(user_id=user_id).all()
        
        # Get trades from last 30 days for risk calculation
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_trades = Trade.query.filter(
            Trade.bot_id.in_([bot.id for bot in bots]),
            Trade.timestamp >= thirty_days_ago
        ).all()
        
        # Calculate risk metrics
        pnl_values = [float(trade.pnl) for trade in recent_trades if trade.pnl]
        
        if pnl_values:
            import statistics
            
            # Calculate Sharpe ratio (simplified)
            avg_return = statistics.mean(pnl_values)
            std_dev = statistics.stdev(pnl_values) if len(pnl_values) > 1 else 0
            sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0
            
            # Calculate maximum drawdown
            cumulative_pnl = []
            running_total = 0
            for pnl in pnl_values:
                running_total += pnl
                cumulative_pnl.append(running_total)
            
            peak = cumulative_pnl[0]
            max_drawdown = 0
            for value in cumulative_pnl:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak != 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            # Calculate Value at Risk (VaR) - 95% confidence
            sorted_pnl = sorted(pnl_values)
            var_95 = sorted_pnl[int(len(sorted_pnl) * 0.05)] if len(sorted_pnl) > 20 else min(pnl_values)
        else:
            sharpe_ratio = 0
            max_drawdown = 0
            var_95 = 0
        
        risk_data = {
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,  # Convert to percentage
            'var_95': var_95,
            'total_trades': len(recent_trades),
            'winning_trades': len([pnl for pnl in pnl_values if pnl > 0]),
            'losing_trades': len([pnl for pnl in pnl_values if pnl < 0]),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(risk_data)
        
    except Exception as e:
        logger.error(f"Error getting risk metrics: {str(e)}")
        return jsonify({'error': 'Failed to get risk metrics'}), 500

@pro_dashboard_bp.route('/api/pro-dashboard/performance-analytics', methods=['GET'])
@jwt_required()
def get_performance_analytics():
    """Get detailed performance analytics"""
    try:
        user_id = get_jwt_identity()
        timeframe = request.args.get('timeframe', '30d')  # 7d, 30d, 90d, 1y
        
        # Calculate date range based on timeframe
        if timeframe == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif timeframe == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        elif timeframe == '90d':
            start_date = datetime.utcnow() - timedelta(days=90)
        elif timeframe == '1y':
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        # Get user's bots and trades
        bots = Bot.query.filter_by(user_id=user_id).all()
        trades = Trade.query.filter(
            Trade.bot_id.in_([bot.id for bot in bots]),
            Trade.timestamp >= start_date
        ).order_by(Trade.timestamp).all()
        
        # Calculate performance metrics
        total_pnl = sum(float(trade.pnl) for trade in trades if trade.pnl)
        total_volume = sum(float(trade.quantity) * float(trade.price) for trade in trades)
        
        # Bot performance breakdown
        bot_performance = {}
        for bot in bots:
            bot_trades = [trade for trade in trades if trade.bot_id == bot.id]
            bot_pnl = sum(float(trade.pnl) for trade in bot_trades if trade.pnl)
            bot_performance[bot.id] = {
                'name': bot.name,
                'strategy': bot.strategy,
                'pnl': bot_pnl,
                'trades': len(bot_trades),
                'win_rate': len([t for t in bot_trades if t.pnl and float(t.pnl) > 0]) / len(bot_trades) * 100 if bot_trades else 0
            }
        
        # Time series data for charts
        daily_performance = {}
        for trade in trades:
            date_key = trade.timestamp.date().isoformat()
            if date_key not in daily_performance:
                daily_performance[date_key] = {'pnl': 0, 'volume': 0, 'trades': 0}
            daily_performance[date_key]['pnl'] += float(trade.pnl) if trade.pnl else 0
            daily_performance[date_key]['volume'] += float(trade.quantity) * float(trade.price)
            daily_performance[date_key]['trades'] += 1
        
        analytics_data = {
            'summary': {
                'total_pnl': total_pnl,
                'total_volume': total_volume,
                'total_trades': len(trades),
                'timeframe': timeframe
            },
            'bot_performance': list(bot_performance.values()),
            'daily_performance': [{
                'date': date,
                'pnl': data['pnl'],
                'volume': data['volume'],
                'trades': data['trades']
            } for date, data in sorted(daily_performance.items())],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {str(e)}")
        return jsonify({'error': 'Failed to get performance analytics'}), 500