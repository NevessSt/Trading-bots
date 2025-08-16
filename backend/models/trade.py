from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
from db import db

class Trade(db.Model):
    """Trade model for SQLAlchemy"""
    
    __tablename__ = 'trades'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bots.id'), nullable=True)
    
    # Trade details
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    trade_type = db.Column(db.String(20), nullable=False)  # 'market', 'limit', 'stop'
    
    # Quantities and prices
    quantity = db.Column(db.Numeric(20, 8), nullable=False)
    price = db.Column(db.Numeric(20, 8), nullable=False)
    filled_quantity = db.Column(db.Numeric(20, 8), default=0)
    average_price = db.Column(db.Numeric(20, 8))
    
    # Financial details
    total_value = db.Column(db.Numeric(20, 8))
    fee = db.Column(db.Numeric(20, 8), default=0)
    fee_currency = db.Column(db.String(10))
    
    # Status and execution
    status = db.Column(db.String(20), default='pending')  # pending, filled, partial, canceled, failed
    exchange = db.Column(db.String(50), default='binance')
    exchange_order_id = db.Column(db.String(100))
    
    # Strategy and signals
    strategy = db.Column(db.String(50))
    signal_data = db.Column(db.Text)  # JSON string for signal details
    
    # Risk management
    stop_loss = db.Column(db.Numeric(20, 8))
    take_profit = db.Column(db.Numeric(20, 8))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    executed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    notes = db.Column(db.Text)
    is_paper_trade = db.Column(db.Boolean, default=False)
    
    def __init__(self, user_id, symbol, side, trade_type, quantity, price, **kwargs):
        self.user_id = user_id
        self.symbol = symbol
        self.side = side
        self.trade_type = trade_type
        self.quantity = quantity
        self.price = price
        self.signal_data = json.dumps({})
        self.status = 'pending'  # Set default status
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_signal_data(self):
        """Get signal data as dictionary"""
        try:
            return json.loads(self.signal_data or '{}')
        except:
            return {}
    
    def set_signal_data(self, data):
        """Set signal data from dictionary"""
        self.signal_data = json.dumps(data)
    
    def calculate_pnl(self, current_price=None):
        """Calculate profit/loss for the trade"""
        if self.status != 'filled' or not self.average_price:
            return 0
        
        if current_price is None:
            current_price = float(self.price)
        
        if self.side == 'buy':
            pnl = (current_price - float(self.average_price)) * float(self.filled_quantity)
        else:  # sell
            pnl = (float(self.average_price) - current_price) * float(self.filled_quantity)
        
        return pnl - float(self.fee or 0)
    
    @property
    def total(self):
        """Calculate total value of the trade"""
        if self.quantity and self.price:
            return float(self.quantity) * float(self.price)
        return 0
    
    def calculate_percentage_return(self, current_price=None):
        """Calculate percentage return for the trade"""
        if not self.average_price or float(self.average_price) == 0:
            return 0
        
        pnl = self.calculate_pnl(current_price)
        investment = float(self.average_price) * float(self.filled_quantity)
        
        if investment == 0:
            return 0
        
        return (pnl / investment) * 100
    
    def is_profitable(self, current_price=None):
        """Check if trade is profitable"""
        return self.calculate_pnl(current_price) > 0
    
    def update_status(self, new_status, executed_at=None):
        """Update trade status"""
        self.status = new_status
        if executed_at:
            self.executed_at = executed_at
        elif new_status == 'filled':
            self.executed_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_execution(self, filled_quantity, average_price, fee=None):
        """Update trade execution details"""
        self.filled_quantity = filled_quantity
        self.average_price = average_price
        
        if fee is not None:
            self.fee = fee
        
        # Calculate total value
        self.total_value = float(filled_quantity) * float(average_price)
        
        # Update status based on fill
        if float(filled_quantity) >= float(self.quantity):
            self.status = 'filled'
        elif float(filled_quantity) > 0:
            self.status = 'partial'
        
        self.executed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def cancel_trade(self, reason=None):
        """Cancel the trade"""
        self.status = 'canceled'
        if reason:
            notes = self.notes or ''
            self.notes = f"{notes}\nCanceled: {reason}".strip()
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bot_id': self.bot_id,
            'symbol': self.symbol,
            'side': self.side,
            'trade_type': self.trade_type,
            'quantity': f'{self.quantity:.3f}' if self.quantity else '0.000',
            'price': f'{self.price:.2f}' if self.price else '0.00',
            'total': f'{self.total:.2f}',
            'filled_quantity': float(self.filled_quantity) if self.filled_quantity else 0,
            'average_price': float(self.average_price) if self.average_price else 0,
            'total_value': float(self.total_value) if self.total_value else 0,
            'fee': float(self.fee) if self.fee else 0,
            'fee_currency': self.fee_currency,
            'status': self.status,
            'exchange': self.exchange,
            'exchange_order_id': self.exchange_order_id,
            'strategy': self.strategy,
            'signal_data': self.get_signal_data(),
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'created_at': self.created_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
            'is_paper_trade': self.is_paper_trade
        }
    
    @classmethod
    def find_by_user_id(cls, user_id, limit=100, offset=0):
        """Find trades by user ID with pagination"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit)\
                      .offset(offset)\
                      .all()
    
    @classmethod
    def find_by_bot_id(cls, bot_id, limit=100, offset=0):
        """Find trades by bot ID with pagination"""
        return cls.query.filter_by(bot_id=bot_id)\
                      .order_by(cls.created_at.desc())\
                      .limit(limit)\
                      .offset(offset)\
                      .all()
    
    @classmethod
    def find_by_symbol(cls, symbol, user_id=None, limit=100, offset=0):
        """Find trades by symbol"""
        query = cls.query.filter_by(symbol=symbol)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(cls.created_at.desc())\
                   .limit(limit)\
                   .offset(offset)\
                   .all()
    
    @classmethod
    def find_open_trades(cls, user_id=None):
        """Find open/pending trades"""
        query = cls.query.filter(cls.status.in_(['pending', 'partial']))
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_trade_stats(cls, user_id=None, days=30):
        """Get trading statistics"""
        from sqlalchemy import func
        
        query = cls.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        # Filter by date range
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(cls.created_at >= start_date)
        
        # Get basic counts
        total_trades = query.count()
        filled_trades = query.filter_by(status='filled').count()
        
        # Get profit/loss data for filled trades
        filled_query = query.filter_by(status='filled')
        
        stats = {
            'total_trades': total_trades,
            'filled_trades': filled_trades,
            'pending_trades': query.filter(cls.status.in_(['pending', 'partial'])).count(),
            'canceled_trades': query.filter_by(status='canceled').count(),
            'success_rate': (filled_trades / total_trades * 100) if total_trades > 0 else 0
        }
        
        # Calculate total volume and fees
        volume_result = filled_query.with_entities(
            func.sum(cls.total_value).label('total_volume'),
            func.sum(cls.fee).label('total_fees')
        ).first()
        
        stats['total_volume'] = float(volume_result.total_volume or 0)
        stats['total_fees'] = float(volume_result.total_fees or 0)
        
        return stats
    
    @classmethod
    def get_portfolio_performance(cls, user_id, symbol=None):
        """Get portfolio performance metrics"""
        query = cls.query.filter_by(user_id=user_id, status='filled')
        
        if symbol:
            query = query.filter_by(symbol=symbol)
        
        trades = query.order_by(cls.executed_at).all()
        
        if not trades:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'average_return': 0,
                'best_trade': 0,
                'worst_trade': 0
            }
        
        # Calculate performance metrics
        total_pnl = 0
        winning_trades = 0
        returns = []
        
        for trade in trades:
            pnl = trade.calculate_pnl()
            total_pnl += pnl
            
            if pnl > 0:
                winning_trades += 1
            
            return_pct = trade.calculate_percentage_return()
            returns.append(return_pct)
        
        return {
            'total_trades': len(trades),
            'total_pnl': total_pnl,
            'win_rate': (winning_trades / len(trades)) * 100,
            'average_return': sum(returns) / len(returns) if returns else 0,
            'best_trade': max(returns) if returns else 0,
            'worst_trade': min(returns) if returns else 0
        }
    
    def __repr__(self):
        return f'<Trade {self.side} {self.quantity} {self.symbol}>'