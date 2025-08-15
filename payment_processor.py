#!/usr/bin/env python3
"""
Payment Processing System for TradingBot Pro
Handles subscription payments, billing, and customer management
"""

import stripe
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # Replace with actual key

Base = declarative_base()

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    plan_type = Column(String(50))  # 'basic', 'pro', 'enterprise'
    status = Column(String(50))  # 'active', 'canceled', 'past_due'
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Subscription plans
        self.plans = {
            'basic': {
                'name': 'Basic Plan',
                'price': 29.99,
                'features': ['1 Trading Bot', 'Basic Strategies', 'Email Support'],
                'stripe_price_id': 'price_basic_monthly'
            },
            'pro': {
                'name': 'Pro Plan', 
                'price': 79.99,
                'features': ['5 Trading Bots', 'All Strategies', 'Priority Support', 'Advanced Analytics'],
                'stripe_price_id': 'price_pro_monthly'
            },
            'enterprise': {
                'name': 'Enterprise Plan',
                'price': 199.99,
                'features': ['Unlimited Bots', 'Custom Strategies', '24/7 Support', 'White-label'],
                'stripe_price_id': 'price_enterprise_monthly'
            }
        }
    
    def create_customer(self, user_email, user_name):
        """Create a new Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user_email,
                name=user_name,
                metadata={'source': 'tradingbot_pro'}
            )
            return customer
        except stripe.error.StripeError as e:
            self.logger.error(f"Failed to create customer: {e}")
            return None
    
    def create_subscription(self, customer_id, plan_type):
        """Create a new subscription"""
        try:
            if plan_type not in self.plans:
                raise ValueError(f"Invalid plan type: {plan_type}")
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price': self.plans[plan_type]['stripe_price_id']
                }],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            return subscription
        except stripe.error.StripeError as e:
            self.logger.error(f"Failed to create subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id):
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            self.logger.error(f"Failed to cancel subscription: {e}")
            return None
    
    def get_subscription_status(self, subscription_id):
        """Get subscription status"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            self.logger.error(f"Failed to get subscription: {e}")
            return None
    
    def handle_webhook(self, payload, sig_header):
        """Handle Stripe webhooks"""
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            self.logger.error("Invalid payload")
            return False
        except stripe.error.SignatureVerificationError:
            self.logger.error("Invalid signature")
            return False
        
        # Handle the event
        if event['type'] == 'customer.subscription.created':
            self._handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            self._handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self._handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            self._handle_payment_failed(event['data']['object'])
        
        return True
    
    def _handle_subscription_created(self, subscription):
        """Handle subscription creation"""
        self.logger.info(f"Subscription created: {subscription['id']}")
        # Update database with new subscription
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        self.logger.info(f"Subscription updated: {subscription['id']}")
        # Update database with subscription changes
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        self.logger.info(f"Subscription canceled: {subscription['id']}")
        # Update database and disable user access
    
    def _handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        self.logger.info(f"Payment succeeded for invoice: {invoice['id']}")
        # Update subscription status and extend access
    
    def _handle_payment_failed(self, invoice):
        """Handle failed payment"""
        self.logger.warning(f"Payment failed for invoice: {invoice['id']}")
        # Send notification and potentially suspend access
    
    def get_pricing_info(self):
        """Get all pricing plans"""
        return self.plans
    
    def validate_subscription(self, user_id):
        """Validate if user has active subscription"""
        # This would query the database for user's subscription status
        # For now, return a mock response
        return {
            'is_active': True,
            'plan_type': 'pro',
            'expires_at': datetime.utcnow() + timedelta(days=30)
        }

if __name__ == "__main__":
    processor = PaymentProcessor()
    print("Payment processor initialized")
    print("Available plans:", processor.get_pricing_info())