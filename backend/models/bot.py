from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
from db import db

class Bot(db.Model):
    """Bot model for SQLAlchemy"""
    
    __tablename__ = 'bots'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Bot identification
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Bot configuration
    strategy = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    timeframe = db.Column(db.String(10), default='1h')
    
    # Trading parameters
    base_amount = db.Column(db.Numeric(20, 8), nullable=False)
    max_position_size = db.Column(db.Numeric(20, 8))
    stop_loss_percentage = db.Column(db.Numeric(5, 2))
    take_profit_percentage = db.Column(db.Numeric(5, 2))
    
    # Risk management
    max_daily_trades = db.Column(db.Integer, default=10)
    max_daily_loss = db.Column(db.Numeric(20, 8))
    risk_per_trade = db.Column(db.Numeric(5, 2), default=2.0)
    
    # Bot status
    is_active = db.Column(db.Boolean, default=False)
    is_running = db.Column(db.Boolean, default=False)
    is_paper_trading = db.Column(db.Boolean, default=True)
    
    # Performance tracking
    total_trades = db.Column(db.Integer, default=0)
    winning_trades = db.Column(db.Integer, default=0)
    total_profit_loss = db.Column(db.Numeric(20, 8), default=0)
    
    # Configuration data
    strategy_config = db.Column(db.Text)  # JSON string for strategy parameters
    indicators_config = db.Column(db.Text)  # JSON string for indicator settings
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at = db.Column(db.DateTime)
    
    # Relationships
    trades = db.relationship('Trade', backref='bot', lazy='dynamic')
    
    def __init__(self, user_id, name, strategy, symbol, base_amount, **kwargs):
        self.user_id = user_id
        self.name = name
        self.strategy = strategy
        self.symbol = symbol
        self.base_amount = base_amount
        self.strategy_config = json.dumps({})
        self.indicators_config = json.dumps({})
        
        # Set default values for boolean fields
        self.is_active = kwargs.get('is_active', False)
        self.is_running = kwargs.get('is_running', False)
        self.is_paused = kwargs.get('is_paused', False)
        
        # Set default values for performance tracking
        self.total_trades = kwargs.get('total_trades', 0)
        self.winning_trades = kwargs.get('winning_trades', 0)
        self.total_profit_loss = kwargs.get('total_profit_loss', 0.0)
        
        # Set default timestamps
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        
        # Set other attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['is_active', 'is_running', 'is_paused', 'created_at', 'updated_at']:
                setattr(self, key, value)
    
    def get_strategy_config(self):
        """Get strategy configuration as dictionary"""
        try:
            return json.loads(self.strategy_config or '{}')
        except:
            return {}
    
    def set_strategy_config(self, config):
        """Set strategy configuration from dictionary"""
        self.strategy_config = json.dumps(config)
    
    def get_indicators_config(self):
        """Get indicators configuration as dictionary"""
        try:
            return json.loads(self.indicators_config or '{}')
        except:
            return {}
    
    def set_indicators_config(self, config):
        """Set indicators configuration from dictionary"""
        self.indicators_config = json.dumps(config)
    
    def start_bot(self):
        """Start the bot"""
        self.is_running = True
        self.last_run_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def stop_bot(self):
        """Stop the bot"""
        self.is_running = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def activate_bot(self):
        """Activate the bot"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate_bot(self):
        """Deactivate the bot"""
        self.is_active = False
        self.is_running = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_performance(self, trade_result):
        """Update bot performance metrics"""
        self.total_trades += 1
        
        if trade_result > 0:
            self.winning_trades += 1
        
        self.total_profit_loss = float(self.total_profit_loss or 0) + trade_result
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_win_rate(self):
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100
    
    def get_average_profit_per_trade(self):
        """Calculate average profit per trade"""
        if self.total_trades == 0:
            return 0
        return float(self.total_profit_loss or 0) / self.total_trades
    
    def is_within_risk_limits(self, proposed_trade_amount):
        """Check if proposed trade is within risk limits"""
        # Check daily trade limit
        today_trades = self.trades.filter(
            db.func.date(Trade.created_at) == datetime.utcnow().date()
        ).count()
        
        if today_trades >= self.max_daily_trades:
            return False, "Daily trade limit exceeded"
        
        # Check daily loss limit
        if self.max_daily_loss:
            today_pnl = sum([
                trade.calculate_pnl() for trade in self.trades.filter(
                    db.func.date(Trade.created_at) == datetime.utcnow().date()
                ).all()
            ])
            
            if today_pnl <= -float(self.max_daily_loss):
                return False, "Daily loss limit exceeded"
        
        # Check position size limit
        if self.max_position_size and proposed_trade_amount > float(self.max_position_size):
            return False, "Position size limit exceeded"
        
        return True, "Within risk limits"
    
    def get_recent_trades(self, limit=10):
        """Get recent trades for this bot"""
        return self.trades.order_by(Trade.created_at.desc()).limit(limit).all()
    
    @property
    def profit_loss(self):
        """Alias for total_profit_loss for backward compatibility"""
        return self.total_profit_loss
    
    def get_performance_summary(self, days=30):
        """Get performance summary for specified days"""
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        trades_query = self.trades.filter(Trade.created_at >= start_date)
        
        total_trades = trades_query.count()
        filled_trades = trades_query.filter_by(status='filled').count()
        
        if filled_trades == 0:
            return {
                'total_trades': total_trades,
                'filled_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_pnl': 0,
                'best_trade': 0,
                'worst_trade': 0
            }
        
        filled_trades_list = trades_query.filter_by(status='filled').all()
        pnls = [trade.calculate_pnl() for trade in filled_trades_list]
        winning_trades = len([pnl for pnl in pnls if pnl > 0])
        
        return {
            'total_trades': total_trades,
            'filled_trades': filled_trades,
            'win_rate': (winning_trades / filled_trades) * 100 if filled_trades > 0 else 0,
            'total_pnl': sum(pnls) if pnls else 0,
            'average_pnl': sum(pnls) / len(pnls) if pnls else 0,
            'best_trade': max(pnls) if pnls else 0,
            'worst_trade': min(pnls) if pnls else 0
        }
    
    def to_dict(self):
        """Convert bot to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'strategy': self.strategy,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'base_amount': float(self.base_amount) if self.base_amount else 0,
            'max_position_size': float(self.max_position_size) if self.max_position_size else None,
            'stop_loss_percentage': float(self.stop_loss_percentage) if self.stop_loss_percentage else None,
            'take_profit_percentage': float(self.take_profit_percentage) if self.take_profit_percentage else None,
            'max_daily_trades': self.max_daily_trades,
            'max_daily_loss': float(self.max_daily_loss) if self.max_daily_loss else None,
            'risk_per_trade': float(self.risk_per_trade) if self.risk_per_trade else 0,
            'is_active': self.is_active,
            'is_running': self.is_running,
            'is_paper_trading': self.is_paper_trading,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'total_profit_loss': float(self.total_profit_loss) if self.total_profit_loss else 0,
            'win_rate': self.get_win_rate(),
            'strategy_config': self.get_strategy_config(),
            'indicators_config': self.get_indicators_config(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None
        }
    
    @classmethod
    def find_by_user_id(cls, user_id, active_only=False):
        """Find bots by user ID"""
        query = cls.query.filter_by(user_id=user_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def find_running_bots(cls, user_id=None):
        """Find currently running bots"""
        query = cls.query.filter_by(is_running=True)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.all()
    
    @classmethod
    def find_by_strategy(cls, strategy, user_id=None):
        """Find bots by strategy"""
        query = cls.query.filter_by(strategy=strategy)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    def __repr__(self):
        return f'<Bot {self.name} ({self.strategy}) - {self.symbol}>'