"""Analytics-related Celery tasks for performance calculations and reporting."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from celery import Task
import pandas as pd
import numpy as np

from celery_app import celery_app
from models.user import User
from models.trade import Trade
from models.portfolio import Portfolio
from models.bot import Bot
from services.analytics_service import AnalyticsService
from utils.logging_config import get_api_logger
from database import db

logger = get_api_logger('analytics_tasks')

class AnalyticsTask(Task):
    """Base class for analytics tasks with error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Analytics task {task_id} failed: {exc}")

@celery_app.task(bind=True, base=AnalyticsTask)
def calculate_portfolio_performance(self, user_id: int, period_days: int = 30):
    """Calculate portfolio performance metrics for a user.
    
    Args:
        user_id: User ID
        period_days: Number of days to analyze
    """
    try:
        logger.info(f"Calculating portfolio performance for user {user_id}")
        
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Get portfolio data
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        if not portfolio:
            return {'success': False, 'error': 'Portfolio not found'}
        
        # Get trades within the period
        start_date = datetime.utcnow() - timedelta(days=period_days)
        trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.created_at >= start_date,
            Trade.status == 'completed'
        ).order_by(Trade.created_at).all()
        
        if not trades:
            return {
                'success': True,
                'user_id': user_id,
                'period_days': period_days,
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_trade_duration': 0
            }
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]
        
        total_pnl = sum(float(t.pnl or 0) for t in trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Calculate returns for advanced metrics
        daily_returns = []
        cumulative_pnl = 0
        peak_value = 0
        max_drawdown = 0
        
        for trade in trades:
            trade_pnl = float(trade.pnl or 0)
            cumulative_pnl += trade_pnl
            
            # Track peak and drawdown
            if cumulative_pnl > peak_value:
                peak_value = cumulative_pnl
            
            current_drawdown = (peak_value - cumulative_pnl) / peak_value if peak_value > 0 else 0
            max_drawdown = max(max_drawdown, current_drawdown)
            
            # Calculate daily return
            if trade.quantity and trade.price:
                trade_value = float(trade.quantity) * float(trade.price)
                daily_return = trade_pnl / trade_value if trade_value > 0 else 0
                daily_returns.append(daily_return)
        
        # Calculate Sharpe ratio
        sharpe_ratio = 0
        if daily_returns and len(daily_returns) > 1:
            returns_array = np.array(daily_returns)
            if np.std(returns_array) > 0:
                sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252)  # Annualized
        
        # Calculate average trade duration
        trade_durations = []
        for trade in trades:
            if trade.created_at and trade.updated_at:
                duration = (trade.updated_at - trade.created_at).total_seconds() / 3600  # hours
                trade_durations.append(duration)
        
        avg_trade_duration = np.mean(trade_durations) if trade_durations else 0
        
        # Calculate additional metrics
        avg_win = np.mean([float(t.pnl) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([float(t.pnl) for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Calculate volatility
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        
        performance_data = {
            'success': True,
            'user_id': user_id,
            'period_days': period_days,
            'calculation_date': datetime.utcnow().isoformat(),
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate * 100, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_drawdown': round(max_drawdown * 100, 2),
            'volatility': round(volatility * 100, 2),
            'avg_trade_duration': round(avg_trade_duration, 2)
        }
        
        # Store results in analytics service
        analytics_service = AnalyticsService()
        analytics_service.store_performance_metrics(user_id, performance_data)
        
        logger.info(f"Portfolio performance calculated for user {user_id}: PnL={total_pnl}, Win Rate={win_rate:.2%}")
        
        return performance_data
        
    except Exception as exc:
        logger.error(f"Portfolio performance calculation failed: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=AnalyticsTask)
def generate_trading_report(self, user_id: int, report_type: str = 'monthly'):
    """Generate comprehensive trading report for a user.
    
    Args:
        user_id: User ID
        report_type: 'daily', 'weekly', 'monthly', 'yearly'
    """
    try:
        logger.info(f"Generating {report_type} trading report for user {user_id}")
        
        # Determine date range based on report type
        now = datetime.utcnow()
        if report_type == 'daily':
            start_date = now - timedelta(days=1)
        elif report_type == 'weekly':
            start_date = now - timedelta(weeks=1)
        elif report_type == 'monthly':
            start_date = now - timedelta(days=30)
        elif report_type == 'yearly':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # Default to monthly
        
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Get user's bots and trades
        bots = Bot.query.filter_by(user_id=user_id).all()
        trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.created_at >= start_date,
            Trade.status == 'completed'
        ).all()
        
        # Calculate bot performance
        bot_performance = []
        for bot in bots:
            bot_trades = [t for t in trades if t.bot_id == bot.id]
            if bot_trades:
                bot_pnl = sum(float(t.pnl or 0) for t in bot_trades)
                bot_trades_count = len(bot_trades)
                bot_win_rate = len([t for t in bot_trades if t.pnl and t.pnl > 0]) / bot_trades_count
                
                bot_performance.append({
                    'bot_id': bot.id,
                    'bot_name': bot.name,
                    'strategy': bot.strategy,
                    'trades_count': bot_trades_count,
                    'total_pnl': round(bot_pnl, 2),
                    'win_rate': round(bot_win_rate * 100, 2),
                    'status': bot.status
                })
        
        # Calculate symbol performance
        symbol_stats = {}
        for trade in trades:
            symbol = trade.symbol
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    'trades': 0,
                    'pnl': 0,
                    'volume': 0,
                    'wins': 0
                }
            
            symbol_stats[symbol]['trades'] += 1
            symbol_stats[symbol]['pnl'] += float(trade.pnl or 0)
            symbol_stats[symbol]['volume'] += float(trade.quantity or 0) * float(trade.price or 0)
            if trade.pnl and trade.pnl > 0:
                symbol_stats[symbol]['wins'] += 1
        
        # Convert to list and calculate win rates
        symbol_performance = []
        for symbol, stats in symbol_stats.items():
            win_rate = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
            symbol_performance.append({
                'symbol': symbol,
                'trades_count': stats['trades'],
                'total_pnl': round(stats['pnl'], 2),
                'total_volume': round(stats['volume'], 2),
                'win_rate': round(win_rate * 100, 2)
            })
        
        # Sort by PnL
        symbol_performance.sort(key=lambda x: x['total_pnl'], reverse=True)
        bot_performance.sort(key=lambda x: x['total_pnl'], reverse=True)
        
        # Calculate overall metrics
        total_pnl = sum(float(t.pnl or 0) for t in trades)
        total_volume = sum(float(t.quantity or 0) * float(t.price or 0) for t in trades)
        total_fees = sum(float(t.fee or 0) for t in trades)
        
        report_data = {
            'success': True,
            'user_id': user_id,
            'report_type': report_type,
            'period_start': start_date.isoformat(),
            'period_end': now.isoformat(),
            'generated_at': now.isoformat(),
            'summary': {
                'total_trades': len(trades),
                'total_pnl': round(total_pnl, 2),
                'total_volume': round(total_volume, 2),
                'total_fees': round(total_fees, 2),
                'active_bots': len([b for b in bots if b.status == 'active']),
                'total_bots': len(bots)
            },
            'bot_performance': bot_performance,
            'symbol_performance': symbol_performance[:10],  # Top 10 symbols
            'daily_pnl': []
        }
        
        # Calculate daily PnL breakdown
        daily_pnl = {}
        for trade in trades:
            trade_date = trade.created_at.date().isoformat()
            if trade_date not in daily_pnl:
                daily_pnl[trade_date] = 0
            daily_pnl[trade_date] += float(trade.pnl or 0)
        
        report_data['daily_pnl'] = [
            {'date': date, 'pnl': round(pnl, 2)}
            for date, pnl in sorted(daily_pnl.items())
        ]
        
        # Store report
        analytics_service = AnalyticsService()
        analytics_service.store_trading_report(user_id, report_type, report_data)
        
        logger.info(f"Trading report generated for user {user_id}: {len(trades)} trades, PnL={total_pnl}")
        
        return report_data
        
    except Exception as exc:
        logger.error(f"Trading report generation failed: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=AnalyticsTask)
def calculate_risk_metrics(self, user_id: int, lookback_days: int = 90):
    """Calculate risk metrics for a user's trading activity.
    
    Args:
        user_id: User ID
        lookback_days: Number of days to analyze
    """
    try:
        logger.info(f"Calculating risk metrics for user {user_id}")
        
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.created_at >= start_date,
            Trade.status == 'completed'
        ).order_by(Trade.created_at).all()
        
        if not trades:
            return {
                'success': True,
                'user_id': user_id,
                'lookback_days': lookback_days,
                'var_95': 0,
                'var_99': 0,
                'expected_shortfall': 0,
                'beta': 0,
                'correlation_market': 0
            }
        
        # Calculate daily returns
        daily_returns = []
        daily_pnl = {}
        
        for trade in trades:
            trade_date = trade.created_at.date()
            trade_pnl = float(trade.pnl or 0)
            
            if trade_date not in daily_pnl:
                daily_pnl[trade_date] = 0
            daily_pnl[trade_date] += trade_pnl
        
        # Convert to returns array
        portfolio_value = 10000  # Assume starting portfolio value
        for date in sorted(daily_pnl.keys()):
            daily_return = daily_pnl[date] / portfolio_value
            daily_returns.append(daily_return)
            portfolio_value += daily_pnl[date]
        
        if len(daily_returns) < 10:  # Need minimum data points
            return {
                'success': True,
                'user_id': user_id,
                'lookback_days': lookback_days,
                'insufficient_data': True
            }
        
        returns_array = np.array(daily_returns)
        
        # Calculate Value at Risk (VaR)
        var_95 = np.percentile(returns_array, 5)  # 95% VaR
        var_99 = np.percentile(returns_array, 1)  # 99% VaR
        
        # Calculate Expected Shortfall (Conditional VaR)
        tail_returns = returns_array[returns_array <= var_95]
        expected_shortfall = np.mean(tail_returns) if len(tail_returns) > 0 else 0
        
        # Calculate maximum consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        
        for return_val in returns_array:
            if return_val < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # Calculate downside deviation
        negative_returns = returns_array[returns_array < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0
        
        # Calculate Sortino ratio
        mean_return = np.mean(returns_array)
        sortino_ratio = mean_return / downside_deviation if downside_deviation > 0 else 0
        
        risk_metrics = {
            'success': True,
            'user_id': user_id,
            'lookback_days': lookback_days,
            'calculation_date': datetime.utcnow().isoformat(),
            'var_95': round(var_95 * 100, 4),  # Convert to percentage
            'var_99': round(var_99 * 100, 4),
            'expected_shortfall': round(expected_shortfall * 100, 4),
            'max_consecutive_losses': max_consecutive_losses,
            'downside_deviation': round(downside_deviation * 100, 4),
            'sortino_ratio': round(sortino_ratio, 4),
            'volatility': round(np.std(returns_array) * 100, 4),
            'skewness': round(float(pd.Series(returns_array).skew()), 4),
            'kurtosis': round(float(pd.Series(returns_array).kurtosis()), 4)
        }
        
        # Store risk metrics
        analytics_service = AnalyticsService()
        analytics_service.store_risk_metrics(user_id, risk_metrics)
        
        logger.info(f"Risk metrics calculated for user {user_id}: VaR 95%={var_95:.4f}")
        
        return risk_metrics
        
    except Exception as exc:
        logger.error(f"Risk metrics calculation failed: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task
def generate_system_analytics():
    """Generate system-wide analytics and performance metrics."""
    try:
        logger.info("Generating system analytics")
        
        # Get system-wide statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_bots = Bot.query.count()
        active_bots = Bot.query.filter_by(status='active').count()
        
        # Get recent trades (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_trades = Trade.query.filter(
            Trade.created_at >= yesterday,
            Trade.status == 'completed'
        ).all()
        
        # Calculate system metrics
        total_volume_24h = sum(float(t.quantity or 0) * float(t.price or 0) for t in recent_trades)
        total_pnl_24h = sum(float(t.pnl or 0) for t in recent_trades)
        total_fees_24h = sum(float(t.fee or 0) for t in recent_trades)
        
        # Calculate exchange distribution
        exchange_stats = {}
        for trade in recent_trades:
            exchange = trade.exchange or 'unknown'
            if exchange not in exchange_stats:
                exchange_stats[exchange] = {'trades': 0, 'volume': 0}
            
            exchange_stats[exchange]['trades'] += 1
            exchange_stats[exchange]['volume'] += float(trade.quantity or 0) * float(trade.price or 0)
        
        # Get top performing users
        user_performance = db.session.query(
            Trade.user_id,
            db.func.sum(Trade.pnl).label('total_pnl'),
            db.func.count(Trade.id).label('trade_count')
        ).filter(
            Trade.created_at >= yesterday,
            Trade.status == 'completed'
        ).group_by(Trade.user_id).order_by(db.desc('total_pnl')).limit(10).all()
        
        system_analytics = {
            'success': True,
            'generated_at': datetime.utcnow().isoformat(),
            'system_stats': {
                'total_users': total_users,
                'active_users': active_users,
                'total_bots': total_bots,
                'active_bots': active_bots,
                'user_activity_rate': round(active_users / total_users * 100, 2) if total_users > 0 else 0,
                'bot_activity_rate': round(active_bots / total_bots * 100, 2) if total_bots > 0 else 0
            },
            'trading_stats_24h': {
                'total_trades': len(recent_trades),
                'total_volume': round(total_volume_24h, 2),
                'total_pnl': round(total_pnl_24h, 2),
                'total_fees': round(total_fees_24h, 2),
                'avg_trade_size': round(total_volume_24h / len(recent_trades), 2) if recent_trades else 0
            },
            'exchange_distribution': [
                {
                    'exchange': exchange,
                    'trades': stats['trades'],
                    'volume': round(stats['volume'], 2),
                    'market_share': round(stats['volume'] / total_volume_24h * 100, 2) if total_volume_24h > 0 else 0
                }
                for exchange, stats in exchange_stats.items()
            ],
            'top_performers': [
                {
                    'user_id': perf.user_id,
                    'total_pnl': round(float(perf.total_pnl), 2),
                    'trade_count': perf.trade_count
                }
                for perf in user_performance
            ]
        }
        
        # Store system analytics
        analytics_service = AnalyticsService()
        analytics_service.store_system_analytics(system_analytics)
        
        logger.info(f"System analytics generated: {len(recent_trades)} trades, {total_volume_24h:.2f} volume")
        
        return system_analytics
        
    except Exception as exc:
        logger.error(f"System analytics generation failed: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task
def cleanup_old_analytics(days_to_keep: int = 90):
    """Clean up old analytics data to save storage space.
    
    Args:
        days_to_keep: Number of days of analytics data to retain
    """
    try:
        logger.info(f"Cleaning up analytics data older than {days_to_keep} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        analytics_service = AnalyticsService()
        
        # Clean up old performance metrics
        deleted_performance = analytics_service.cleanup_old_performance_metrics(cutoff_date)
        
        # Clean up old reports
        deleted_reports = analytics_service.cleanup_old_reports(cutoff_date)
        
        # Clean up old risk metrics
        deleted_risk = analytics_service.cleanup_old_risk_metrics(cutoff_date)
        
        cleanup_result = {
            'success': True,
            'cleanup_date': datetime.utcnow().isoformat(),
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_records': {
                'performance_metrics': deleted_performance,
                'reports': deleted_reports,
                'risk_metrics': deleted_risk
            },
            'total_deleted': deleted_performance + deleted_reports + deleted_risk
        }
        
        logger.info(f"Analytics cleanup completed: {cleanup_result['total_deleted']} records deleted")
        
        return cleanup_result
        
    except Exception as exc:
        logger.error(f"Analytics cleanup failed: {exc}")
        return {'success': False, 'error': str(exc)}