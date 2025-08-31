"""Analytics and performance reporting routes."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import logging
from typing import Dict, Any, List, Optional

from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.license import License
from services.trading_service import TradingService
from services.admin_service import AdminService
from tasks.analytics import (
    calculate_sharpe_ratio,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_max_drawdown,
    calculate_volatility,
    calculate_average_trade_duration
)
from utils.decorators import handle_errors
from utils.error_categories import ErrorCategory
from utils.permissions import Permission, require_permission
from db import db

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
logger = logging.getLogger(__name__)


@analytics_bp.route('/performance', methods=['GET'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def get_user_performance():
    """Get comprehensive performance analytics for the current user."""
    user_id = get_jwt_identity()
    
    # Get time period from query params
    period = request.args.get('period', '30d')
    bot_id = request.args.get('bot_id')
    
    try:
        # Parse time period
        if period == '1d':
            start_date = datetime.utcnow() - timedelta(days=1)
        elif period == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == '90d':
            start_date = datetime.utcnow() - timedelta(days=90)
        elif period == '1y':
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        # Build query
        query = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.created_at >= start_date,
            Trade.status == 'completed'
        )
        
        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)
        
        trades = query.all()
        
        if not trades:
            return jsonify({
                'success': True,
                'performance': {
                    'total_trades': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'volatility': 0,
                    'average_trade_duration': 0,
                    'total_volume': 0,
                    'total_fees': 0,
                    'best_trade': 0,
                    'worst_trade': 0,
                    'winning_trades': 0,
                    'losing_trades': 0
                }
            }), 200
        
        # Calculate performance metrics
        total_trades = len(trades)
        total_pnl = sum(float(t.pnl or 0) for t in trades)
        total_volume = sum(float(t.quantity or 0) * float(t.price or 0) for t in trades)
        total_fees = sum(float(t.fee or 0) for t in trades)
        
        winning_trades = [t for t in trades if float(t.pnl or 0) > 0]
        losing_trades = [t for t in trades if float(t.pnl or 0) < 0]
        
        win_rate = calculate_win_rate(trades)
        profit_factor = calculate_profit_factor(trades)
        sharpe_ratio = calculate_sharpe_ratio(trades)
        max_drawdown = calculate_max_drawdown(trades)
        volatility = calculate_volatility(trades)
        avg_duration = calculate_average_trade_duration(trades)
        
        best_trade = max((float(t.pnl or 0) for t in trades), default=0)
        worst_trade = min((float(t.pnl or 0) for t in trades), default=0)
        
        performance = {
            'total_trades': total_trades,
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'volatility': round(volatility, 2),
            'average_trade_duration': round(avg_duration, 2),
            'total_volume': round(total_volume, 2),
            'total_fees': round(total_fees, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades)
        }
        
        return jsonify({
            'success': True,
            'performance': performance
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate performance metrics'
        }), 500


@analytics_bp.route('/portfolio', methods=['GET'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def get_portfolio_summary():
    """Get portfolio summary and allocation."""
    user_id = get_jwt_identity()
    
    try:
        # Get user's bots
        bots = Bot.query.filter_by(user_id=user_id).all()
        
        # Get recent trades for portfolio calculation
        recent_trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.status == 'completed'
        ).order_by(Trade.created_at.desc()).limit(1000).all()
        
        # Calculate portfolio metrics
        total_pnl = sum(float(t.pnl or 0) for t in recent_trades)
        
        # Symbol allocation
        symbol_allocation = {}
        for trade in recent_trades:
            symbol = trade.symbol
            if symbol not in symbol_allocation:
                symbol_allocation[symbol] = {
                    'trades': 0,
                    'volume': 0,
                    'pnl': 0
                }
            
            symbol_allocation[symbol]['trades'] += 1
            symbol_allocation[symbol]['volume'] += float(trade.quantity or 0) * float(trade.price or 0)
            symbol_allocation[symbol]['pnl'] += float(trade.pnl or 0)
        
        # Bot performance
        bot_performance = []
        for bot in bots:
            bot_trades = [t for t in recent_trades if t.bot_id == bot.id]
            if bot_trades:
                bot_pnl = sum(float(t.pnl or 0) for t in bot_trades)
                bot_performance.append({
                    'bot_id': bot.id,
                    'bot_name': bot.name,
                    'strategy': bot.strategy,
                    'symbol': bot.symbol,
                    'trades': len(bot_trades),
                    'pnl': round(bot_pnl, 2),
                    'status': bot.status
                })
        
        # Sort by PnL
        bot_performance.sort(key=lambda x: x['pnl'], reverse=True)
        
        portfolio = {
            'total_pnl': round(total_pnl, 2),
            'active_bots': len([b for b in bots if b.is_active]),
            'total_bots': len(bots),
            'symbol_allocation': [
                {
                    'symbol': symbol,
                    'trades': data['trades'],
                    'volume': round(data['volume'], 2),
                    'pnl': round(data['pnl'], 2)
                }
                for symbol, data in sorted(symbol_allocation.items(), 
                                         key=lambda x: x[1]['volume'], reverse=True)
            ],
            'bot_performance': bot_performance[:10]  # Top 10 bots
        }
        
        return jsonify({
            'success': True,
            'portfolio': portfolio
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get portfolio summary'
        }), 500


@analytics_bp.route('/bots/<bot_id>/performance', methods=['GET'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def get_bot_performance(bot_id):
    """Get detailed performance metrics for a specific bot."""
    user_id = get_jwt_identity()
    
    try:
        # Verify bot ownership
        bot = Bot.query.filter_by(id=bot_id, user_id=user_id).first()
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot not found'
            }), 404
        
        # Get bot performance from trading service
        performance = TradingService.get_bot_performance(bot_id, user_id)
        
        # Get additional metrics
        trades = Trade.query.filter_by(bot_id=bot_id, user_id=user_id).all()
        
        if trades:
            # Calculate advanced metrics
            sharpe_ratio = calculate_sharpe_ratio(trades)
            max_drawdown = calculate_max_drawdown(trades)
            volatility = calculate_volatility(trades)
            
            performance.update({
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'volatility': round(volatility, 2)
            })
        
        return jsonify({
            'success': True,
            'performance': performance
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error getting bot performance: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get bot performance'
        }), 500


@analytics_bp.route('/trades', methods=['GET'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def get_trade_history():
    """Get paginated trade history with filtering options."""
    user_id = get_jwt_identity()
    
    # Get query parameters
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 100)  # Max 100 per page
    symbol = request.args.get('symbol')
    bot_id = request.args.get('bot_id')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        # Build query
        query = Trade.query.filter(Trade.user_id == user_id)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)
        if status:
            query = query.filter(Trade.status == status)
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Trade.created_at >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Trade.created_at <= end_dt)
        
        # Order by most recent first
        query = query.order_by(Trade.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        trades = [{
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side,
            'trade_type': trade.trade_type,
            'quantity': float(trade.quantity or 0),
            'price': float(trade.price or 0),
            'pnl': float(trade.pnl or 0),
            'fee': float(trade.fee or 0),
            'status': trade.status,
            'bot_id': trade.bot_id,
            'exchange_order_id': trade.exchange_order_id,
            'created_at': trade.created_at.isoformat() if trade.created_at else None,
            'executed_at': trade.executed_at.isoformat() if trade.executed_at else None
        } for trade in pagination.items]
        
        return jsonify({
            'success': True,
            'trades': trades,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get trade history'
        }), 500


@analytics_bp.route('/reports/daily', methods=['GET'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def get_daily_report():
    """Get daily performance report."""
    user_id = get_jwt_identity()
    
    try:
        # Get trades from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.created_at >= yesterday,
            Trade.status == 'completed'
        ).all()
        
        if not trades:
            return jsonify({
                'success': True,
                'report': {
                    'date': datetime.utcnow().date().isoformat(),
                    'total_trades': 0,
                    'total_pnl': 0,
                    'total_volume': 0,
                    'total_fees': 0,
                    'win_rate': 0,
                    'best_trade': 0,
                    'worst_trade': 0,
                    'active_symbols': [],
                    'active_bots': 0
                }
            }), 200
        
        # Calculate daily metrics
        total_pnl = sum(float(t.pnl or 0) for t in trades)
        total_volume = sum(float(t.quantity or 0) * float(t.price or 0) for t in trades)
        total_fees = sum(float(t.fee or 0) for t in trades)
        
        winning_trades = len([t for t in trades if float(t.pnl or 0) > 0])
        win_rate = (winning_trades / len(trades) * 100) if trades else 0
        
        best_trade = max((float(t.pnl or 0) for t in trades), default=0)
        worst_trade = min((float(t.pnl or 0) for t in trades), default=0)
        
        active_symbols = list(set(t.symbol for t in trades))
        active_bots = len(set(t.bot_id for t in trades if t.bot_id))
        
        report = {
            'date': datetime.utcnow().date().isoformat(),
            'total_trades': len(trades),
            'total_pnl': round(total_pnl, 2),
            'total_volume': round(total_volume, 2),
            'total_fees': round(total_fees, 2),
            'win_rate': round(win_rate, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'active_symbols': active_symbols,
            'active_bots': active_bots
        }
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate daily report'
        }), 500


@analytics_bp.route('/system/stats', methods=['GET'])
@jwt_required()
@require_permission(Permission.ADMIN_ACCESS)
@handle_errors(ErrorCategory.API_ERROR)
def get_system_analytics():
    """Get system-wide analytics (admin only)."""
    try:
        admin_service = AdminService()
        
        # Get system statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_bots = Bot.query.count()
        active_bots = Bot.query.filter_by(is_active=True).count()
        
        # Get recent activity
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_trades = Trade.query.filter(
            Trade.created_at >= yesterday,
            Trade.status == 'completed'
        ).count()
        
        # Get license statistics
        license_stats = admin_service.get_license_statistics()
        
        system_stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'activity_rate': round(active_users / total_users * 100, 2) if total_users > 0 else 0
            },
            'bots': {
                'total': total_bots,
                'active': active_bots,
                'activity_rate': round(active_bots / total_bots * 100, 2) if total_bots > 0 else 0
            },
            'trading': {
                'trades_24h': recent_trades
            },
            'licenses': license_stats
        }
        
        return jsonify({
            'success': True,
            'system_stats': system_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get system analytics'
        }), 500