from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from .user import db

class Subscription(db.Model):
    """Subscription model for user billing and plans"""
    
    __tablename__ = 'subscriptions'
    
    # Subscription plans configuration
    PLANS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'currency': 'USD',
            'interval': 'month',
            'features': {
                'max_bots': 1,
                'max_api_keys': 1,
                'backtesting': False,
                'advanced_strategies': False,
                'priority_support': False,
                'api_calls_per_hour': 100
            }
        },
        'pro': {
            'name': 'Pro',
            'price': 29.99,
            'currency': 'USD',
            'interval': 'month',
            'features': {
                'max_bots': 10,
                'max_api_keys': 5,
                'backtesting': True,
                'advanced_strategies': True,
                'priority_support': False,
                'api_calls_per_hour': 1000
            }
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 99.99,
            'currency': 'USD',
            'interval': 'month',
            'features': {
                'max_bots': -1,  # Unlimited
                'max_api_keys': -1,  # Unlimited
                'backtesting': True,
                'advanced_strategies': True,
                'priority_support': True,
                'api_calls_per_hour': 10000
            }
        }
    }
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False, default='free')
    
    # Billing information
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, canceled, past_due, etc.
    
    # Dates
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    canceled_at = db.Column(db.DateTime)
    
    # Billing cycle
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    
    # Usage tracking
    usage_data = db.Column(db.Text)  # JSON string for flexible usage tracking
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id, plan_type='free', **kwargs):
        self.user_id = user_id
        self.plan_type = plan_type
        self.usage_data = json.dumps({})
        
        # Set default dates for free plan
        if plan_type == 'free':
            self.start_date = datetime.utcnow()
            self.end_date = None  # Free plan doesn't expire
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_plan_config(self):
        """Get configuration for current plan"""
        return self.PLANS.get(self.plan_type, self.PLANS['free'])
    
    def get_feature_limit(self, feature_name):
        """Get limit for a specific feature"""
        plan_config = self.get_plan_config()
        return plan_config['features'].get(feature_name, 0)
    
    def has_feature(self, feature_name):
        """Check if subscription includes a feature"""
        plan_config = self.get_plan_config()
        return plan_config['features'].get(feature_name, False)
    
    def get_available_strategies(self):
        """Get list of available trading strategies"""
        base_strategies = ['rsi', 'macd']
        
        if self.has_feature('advanced_strategies'):
            base_strategies.extend(['ema_crossover', 'bollinger_bands', 'stochastic'])
        
        return base_strategies
    
    def is_expired(self):
        """Check if subscription is expired"""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date
    
    def is_trial(self):
        """Check if subscription is in trial period"""
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end
    
    def days_until_expiry(self):
        """Get days until subscription expires"""
        if not self.end_date:
            return None
        
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    def get_usage_data(self):
        """Get usage data as dictionary"""
        try:
            return json.loads(self.usage_data or '{}')
        except:
            return {}
    
    def update_usage(self, usage_type, value):
        """Update usage data"""
        usage = self.get_usage_data()
        usage[usage_type] = value
        usage['last_updated'] = datetime.utcnow().isoformat()
        self.usage_data = json.dumps(usage)
        db.session.commit()
    
    def increment_usage(self, usage_type, increment=1):
        """Increment usage counter"""
        usage = self.get_usage_data()
        current_value = usage.get(usage_type, 0)
        usage[usage_type] = current_value + increment
        usage['last_updated'] = datetime.utcnow().isoformat()
        self.usage_data = json.dumps(usage)
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        usage = self.get_usage_data()
        monthly_counters = ['api_calls', 'backtests_run', 'notifications_sent']
        
        for counter in monthly_counters:
            usage[counter] = 0
        
        usage['last_reset'] = datetime.utcnow().isoformat()
        self.usage_data = json.dumps(usage)
        db.session.commit()
    
    def can_use_feature(self, feature_name, current_usage=None):
        """Check if user can use a feature based on limits"""
        if not self.has_feature(feature_name):
            return False
        
        limit = self.get_feature_limit(feature_name)
        if limit == -1:  # Unlimited
            return True
        
        if current_usage is None:
            usage = self.get_usage_data()
            current_usage = usage.get(feature_name, 0)
        
        return current_usage < limit
    
    def upgrade_plan(self, new_plan_type, stripe_subscription_id=None):
        """Upgrade subscription plan"""
        if new_plan_type not in self.PLANS:
            raise ValueError(f"Invalid plan type: {new_plan_type}")
        
        old_plan = self.plan_type
        self.plan_type = new_plan_type
        
        if stripe_subscription_id:
            self.stripe_subscription_id = stripe_subscription_id
        
        # Set billing period for paid plans
        if new_plan_type != 'free':
            self.current_period_start = datetime.utcnow()
            self.current_period_end = datetime.utcnow() + timedelta(days=30)
            self.end_date = self.current_period_end
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        return old_plan
    
    def cancel_subscription(self, at_period_end=True):
        """Cancel subscription"""
        self.status = 'canceled'
        self.canceled_at = datetime.utcnow()
        
        if not at_period_end:
            self.is_active = False
            self.end_date = datetime.utcnow()
        
        db.session.commit()
    
    def reactivate_subscription(self):
        """Reactivate canceled subscription"""
        self.status = 'active'
        self.is_active = True
        self.canceled_at = None
        
        # Extend subscription if it was expired
        if self.is_expired():
            self.current_period_start = datetime.utcnow()
            self.current_period_end = datetime.utcnow() + timedelta(days=30)
            self.end_date = self.current_period_end
        
        db.session.commit()
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        plan_config = self.get_plan_config()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_type': self.plan_type,
            'plan_name': plan_config['name'],
            'price': plan_config['price'],
            'currency': plan_config['currency'],
            'features': plan_config['features'],
            'is_active': self.is_active,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'days_until_expiry': self.days_until_expiry(),
            'is_trial': self.is_trial(),
            'is_expired': self.is_expired(),
            'usage_data': self.get_usage_data(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_free_subscription(cls, user_id):
        """Create a free subscription for a user"""
        subscription = cls(
            user_id=user_id,
            plan_type='free',
            is_active=True,
            status='active'
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return subscription
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """Find active subscription by user ID"""
        return cls.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()
    
    @classmethod
    def find_by_stripe_subscription_id(cls, stripe_subscription_id):
        """Find subscription by Stripe subscription ID"""
        return cls.query.filter_by(
            stripe_subscription_id=stripe_subscription_id
        ).first()
    
    @classmethod
    def get_expired_subscriptions(cls):
        """Get all expired subscriptions"""
        return cls.query.filter(
            cls.end_date < datetime.utcnow(),
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_subscription_stats(cls):
        """Get subscription statistics"""
        total_subscriptions = cls.query.count()
        active_subscriptions = cls.query.filter_by(is_active=True).count()
        
        plan_counts = {}
        for plan_type in cls.PLANS.keys():
            count = cls.query.filter_by(
                plan_type=plan_type,
                is_active=True
            ).count()
            plan_counts[plan_type] = count
        
        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'plan_distribution': plan_counts
        }
    
    def __repr__(self):
        return f'<Subscription {self.plan_type} for User {self.user_id}>'