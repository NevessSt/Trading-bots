from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, current_app
from functools import wraps
from werkzeug.security import check_password_hash
from models import User, Bot, Trade
from db import db
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')

@dashboard_bp.route('/')
@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for web dashboard."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash('Please verify your email before logging in', 'error')
                return render_template('login.html')
            
            # Create session
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@dashboard_bp.route('/logout')
def logout():
    """Logout and clear session."""
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/', methods=['GET', 'POST'])
@dashboard_bp.route('/main', methods=['GET', 'POST'])
def dashboard():
    """Main dashboard page."""
    if 'user_id' not in session:
        return redirect(url_for('dashboard.login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('dashboard.login'))
    
    # Get user's bots
    bots = Bot.query.filter_by(user_id=user_id).all()
    
    # Get recent trades (last 10) and add profit calculations
    recent_trades_raw = Trade.query.filter_by(user_id=user_id).order_by(Trade.created_at.desc()).limit(10).all()
    recent_trades = []
    for trade in recent_trades_raw:
        trade_dict = {
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': float(trade.quantity),
            'price': float(trade.price),
            'status': trade.status,
            'created_at': trade.created_at.isoformat(),
            'profit': trade.calculate_pnl()
        }
        recent_trades.append(trade_dict)
    
    # Calculate statistics
    total_trades = Trade.query.filter_by(user_id=user_id).count()
    
    # Calculate profitable trades by checking each trade's PnL
    user_trades = Trade.query.filter_by(user_id=user_id).all()
    profitable_trades = sum(1 for trade in user_trades if trade.calculate_pnl() > 0)
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
    total_profit = sum(trade.calculate_pnl() for trade in user_trades)
    
    stats = {
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': float(total_profit)
    }
    
    return render_template('dashboard.html', bots=bots, recent_trades=recent_trades, stats=stats)



@dashboard_bp.route('/api/trades')
def get_trades_data():
    """API endpoint for trades data (for charts)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    # Get trades from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    trades = Trade.query.filter(
        Trade.user_id == user_id,
        Trade.created_at >= thirty_days_ago
    ).order_by(Trade.created_at.asc()).all()
    
    # Format data for charts
    chart_data = []
    running_balance = 1000  # Starting balance
    
    for trade in trades:
        trade_pnl = trade.calculate_pnl()
        running_balance += trade_pnl
        chart_data.append({
            'date': trade.created_at.strftime('%Y-%m-%d'),
            'balance': running_balance,
            'profit': trade_pnl,
            'symbol': trade.symbol
        })
    
    return jsonify(chart_data)

@dashboard_bp.route('/api/bot-status')
def get_bot_status():
    """API endpoint for real-time bot status."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    bots = Bot.query.filter_by(user_id=user_id).all()
    
    bot_status = []
    for bot in bots:
        bot_status.append({
            'id': bot.id,
            'name': bot.name,
            'status': bot.status,
            'strategy': bot.strategy,
            'updated_at': bot.updated_at.strftime('%Y-%m-%d %H:%M:%S') if bot.updated_at else None
        })
    
    return jsonify(bot_status)

@dashboard_bp.route('/bot/<int:bot_id>/start', methods=['POST'])
def start_bot_endpoint(bot_id):
    """Start a trading bot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    try:
        # Get the bot from database
        bot = Bot.query.filter_by(id=bot_id, user_id=user_id).first()
        if not bot:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        # Import trading engine
        from bot_engine.trading_engine import TradingEngine
        
        # Initialize trading engine if not exists
        if not hasattr(current_app, 'trading_engine'):
            current_app.trading_engine = TradingEngine()
        
        # Start the bot
        result = current_app.trading_engine.start_bot(
            user_id=user_id,
            symbol=bot.symbol,
            strategy_name=bot.strategy,
            timeframe=getattr(bot, 'timeframe', '1h'),
            parameters=bot.parameters or {},
            position_size=getattr(bot, 'position_size', 0.02),
            stop_loss=getattr(bot, 'stop_loss', 0.05),
            take_profit=getattr(bot, 'take_profit', 0.10)
        )
        
        if result['success']:
            # Update bot status in database
            bot.status = 'running'
            bot.is_active = True
            db.session.commit()
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to start bot: {str(e)}'}), 500

@dashboard_bp.route('/bot/<int:bot_id>/stop', methods=['POST'])
def stop_bot_endpoint(bot_id):
    """Stop a trading bot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    try:
        # Get the bot from database
        bot = Bot.query.filter_by(id=bot_id, user_id=user_id).first()
        if not bot:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        # Import trading engine
        from bot_engine.trading_engine import TradingEngine
        
        # Initialize trading engine if not exists
        if not hasattr(current_app, 'trading_engine'):
            current_app.trading_engine = TradingEngine()
        
        # Stop the bot using bot_id as string (as expected by trading engine)
        result = current_app.trading_engine.stop_bot(user_id, str(bot_id))
        
        if result['success']:
            # Update bot status in database
            bot.status = 'stopped'
            bot.is_active = False
            db.session.commit()
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to stop bot: {str(e)}'}), 500