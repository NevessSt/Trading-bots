"""Subscription service for managing user subscriptions."""

from flask import current_app
from datetime import datetime, timedelta
from decimal import Decimal
from models import Subscription, User, db
from typing import Dict, List, Optional
import json


class SubscriptionService:
    """Service for handling subscription operations."""
    
    # Subscription plans configuration
    PLANS = {
        'free': {
            'name': 'Free',
            'price': Decimal('0.00'),
            'max_bots': 1,
            'max_api_calls_per_minute': 10,
            'features': ['paper_trading', 'basic_strategies'],
            'duration_days': None  # Unlimited
        },
        'pro': {
            'name': 'Pro',
            'price': Decimal('29.99'),
            'max_bots': 5,
            'max_api_calls_per_minute': 60,
            'features': ['live_trading', 'advanced_strategies', 'backtesting'],
            'duration_days': 30
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': Decimal('99.99'),
            'max_bots': -1,  # Unlimited
            'max_api_calls_per_minute': 300,
            'features': ['live_trading', 'all_strategies', 'advanced_backtesting', 'custom_strategies'],
            'duration_days': 30
        }
    }
    
    @staticmethod
    def create_subscription(user_id, plan_type, payment_method_id=None):
        """Create a new subscription for a user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if plan_type not in SubscriptionService.PLANS:
            raise ValueError("Invalid plan type")
        
        plan = SubscriptionService.PLANS[plan_type]
        
        # Check if user already has an active subscription
        existing = Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if existing:
            raise ValueError("User already has an active subscription")
        
        # Calculate end date
        start_date = datetime.utcnow()
        end_date = None
        if plan['duration_days']:
            end_date = start_date + timedelta(days=plan['duration_days'])
        
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            status='active' if plan_type == 'free' else 'pending',
            start_date=start_date,
            end_date=end_date,
            price=plan['price'],
            features=plan['features'],
            payment_method_id=payment_method_id
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return subscription
    
    @staticmethod
    def get_user_subscription(user_id):
        """Get active subscription for a user."""
        return Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
    
    @staticmethod
    def upgrade_subscription(user_id, new_plan_type, payment_method_id=None):
        """Upgrade user subscription to a new plan."""
        current_subscription = SubscriptionService.get_user_subscription(user_id)
        
        if not current_subscription:
            # Create new subscription if none exists
            return SubscriptionService.create_subscription(user_id, new_plan_type, payment_method_id)
        
        if new_plan_type not in SubscriptionService.PLANS:
            raise ValueError("Invalid plan type")
        
        # Cancel current subscription
        current_subscription.status = 'cancelled'
        current_subscription.cancelled_at = datetime.utcnow()
        
        # Create new subscription
        new_subscription = SubscriptionService.create_subscription(user_id, new_plan_type, payment_method_id)
        
        db.session.commit()
        
        return new_subscription
    
    @staticmethod
    def cancel_subscription(user_id, reason=None):
        """Cancel user subscription."""
        subscription = SubscriptionService.get_user_subscription(user_id)
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        subscription.status = 'cancelled'
        subscription.cancelled_at = datetime.utcnow()
        subscription.cancellation_reason = reason
        
        db.session.commit()
        
        # Create free subscription
        SubscriptionService.create_subscription(user_id, 'free')
        
        return subscription
    
    @staticmethod
    def renew_subscription(user_id, payment_method_id=None):
        """Renew user subscription."""
        subscription = SubscriptionService.get_user_subscription(user_id)
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        if subscription.plan_type == 'free':
            raise ValueError("Free subscriptions don't need renewal")
        
        plan = SubscriptionService.PLANS[subscription.plan_type]
        
        # Extend end date
        if subscription.end_date:
            new_end_date = subscription.end_date + timedelta(days=plan['duration_days'])
        else:
            new_end_date = datetime.utcnow() + timedelta(days=plan['duration_days'])
        
        subscription.end_date = new_end_date
        subscription.renewed_at = datetime.utcnow()
        
        if payment_method_id:
            subscription.payment_method_id = payment_method_id
        
        db.session.commit()
        
        return subscription
    
    @staticmethod
    def check_subscription_limits(user_id, resource_type, current_usage=0):
        """Check if user is within subscription limits."""
        subscription = SubscriptionService.get_user_subscription(user_id)
        
        if not subscription:
            # Default to free plan limits
            plan = SubscriptionService.PLANS['free']
        else:
            plan = SubscriptionService.PLANS[subscription.plan_type]
        
        limits = {
            'max_bots': plan['max_bots'],
            'max_api_calls_per_minute': plan['max_api_calls_per_minute'],
            'features': plan['features']
        }
        
        if resource_type == 'bots':
            if limits['max_bots'] == -1:  # Unlimited
                return True, limits
            return current_usage < limits['max_bots'], limits
        
        elif resource_type == 'api_calls':
            return current_usage < limits['max_api_calls_per_minute'], limits
        
        elif resource_type == 'feature':
            feature_name = current_usage  # In this case, current_usage is feature name
            return feature_name in limits['features'], limits
        
        return False, limits
    
    @staticmethod
    def get_subscription_usage(user_id):
        """Get current subscription usage statistics."""
        from models import Bot, APIKey
        
        # Count user's bots
        bot_count = Bot.query.filter_by(user_id=user_id).count()
        
        # Count API keys
        api_key_count = APIKey.query.filter_by(user_id=user_id, is_active=True).count()
        
        return {
            'current_bots': bot_count,
            'current_api_keys': api_key_count,
            'api_calls_today': 0,  # Would need to implement API call tracking
        }
    
    @staticmethod
    def is_subscription_expired(user_id):
        """Check if user subscription is expired."""
        subscription = SubscriptionService.get_user_subscription(user_id)
        
        if not subscription:
            return True
        
        if subscription.plan_type == 'free':
            return False  # Free plans don't expire
        
        if subscription.end_date and subscription.end_date < datetime.utcnow():
            # Mark as expired
            subscription.status = 'expired'
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def get_plan_features(plan_type):
        """Get features for a specific plan."""
        if plan_type not in SubscriptionService.PLANS:
            return None
        
        return SubscriptionService.PLANS[plan_type]
    
    @staticmethod
    def get_all_plans():
        """Get all available subscription plans."""
        return SubscriptionService.PLANS
    
    @staticmethod
    def process_payment(subscription_id, payment_data):
        """Process payment for subscription (mock implementation)."""
        subscription = Subscription.query.get(subscription_id)
        
        if not subscription:
            raise ValueError("Subscription not found")
        
        # Mock payment processing
        # In real implementation, integrate with Stripe/PayPal
        
        subscription.status = 'active'
        subscription.payment_status = 'paid'
        subscription.paid_at = datetime.utcnow()
        
        db.session.commit()
        
        return subscription
    
    @staticmethod
    def handle_payment_failure(subscription_id, error_message):
        """Handle payment failure for subscription."""
        subscription = Subscription.query.get(subscription_id)
        
        if not subscription:
            raise ValueError("Subscription not found")
        
        subscription.status = 'payment_failed'
        subscription.payment_status = 'failed'
        subscription.payment_error = error_message
        
        db.session.commit()
        
        return subscription