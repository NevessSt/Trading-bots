#!/usr/bin/env python3
"""
Stripe Billing Integration for TradingBot Pro
Handles subscription management, payments, and billing webhooks.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import stripe
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

# Database setup
Base = declarative_base()
engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///billing.db'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"

class PlanType(Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    INSTITUTIONAL = "institutional"

@dataclass
class PlanConfig:
    name: str
    price_monthly: int  # in cents
    price_yearly: int   # in cents
    features: List[str]
    limitations: Dict[str, Any]
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str

# Subscription Models
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True)
    email = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True)
    plan_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    trial_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    stripe_payment_method_id = Column(String, unique=True, index=True)
    type = Column(String, nullable=False)  # card, bank_account, etc.
    last4 = Column(String)
    brand = Column(String)
    exp_month = Column(Integer)
    exp_year = Column(Integer)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    stripe_invoice_id = Column(String, unique=True, index=True)
    amount_paid = Column(Integer)  # in cents
    amount_due = Column(Integer)   # in cents
    currency = Column(String, default="usd")
    status = Column(String, nullable=False)
    invoice_pdf = Column(String)
    hosted_invoice_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    metric_name = Column(String, nullable=False)  # trades, api_calls, etc.
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    billing_period = Column(String)  # YYYY-MM format

class BillingManager:
    """Manages Stripe billing operations"""
    
    def __init__(self):
        self.db = SessionLocal()
        
        # Define subscription plans
        self.plans = {
            PlanType.STARTER: PlanConfig(
                name="Starter",
                price_monthly=2999,  # $29.99
                price_yearly=29999,  # $299.99 (save $60)
                features=[
                    "Basic trading strategies",
                    "Risk management",
                    "Web dashboard",
                    "Email support"
                ],
                limitations={
                    "max_exchanges": 2,
                    "max_strategies": 3,
                    "api_calls_per_month": 10000,
                    "trades_per_month": 1000
                },
                stripe_price_id_monthly=os.getenv('STRIPE_STARTER_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_STARTER_YEARLY_PRICE_ID')
            ),
            PlanType.PROFESSIONAL: PlanConfig(
                name="Professional",
                price_monthly=7999,  # $79.99
                price_yearly=79999,  # $799.99 (save $160)
                features=[
                    "All starter features",
                    "Advanced strategies",
                    "Portfolio management",
                    "API access",
                    "Priority support"
                ],
                limitations={
                    "max_exchanges": 5,
                    "max_strategies": 10,
                    "api_calls_per_month": 50000,
                    "trades_per_month": 5000
                },
                stripe_price_id_monthly=os.getenv('STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_PROFESSIONAL_YEARLY_PRICE_ID')
            ),
            PlanType.ENTERPRISE: PlanConfig(
                name="Enterprise",
                price_monthly=24999,  # $249.99
                price_yearly=249999,  # $2499.99 (save $500)
                features=[
                    "All professional features",
                    "Full source code",
                    "Custom integrations",
                    "White-label options",
                    "Dedicated support"
                ],
                limitations={
                    "max_exchanges": "unlimited",
                    "max_strategies": "unlimited",
                    "api_calls_per_month": "unlimited",
                    "trades_per_month": "unlimited"
                },
                stripe_price_id_monthly=os.getenv('STRIPE_ENTERPRISE_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_ENTERPRISE_YEARLY_PRICE_ID')
            ),
            PlanType.INSTITUTIONAL: PlanConfig(
                name="Institutional",
                price_monthly=99999,  # $999.99
                price_yearly=999999,  # $9999.99 (save $2000)
                features=[
                    "All enterprise features",
                    "Multi-tenant support",
                    "Custom development",
                    "On-site training",
                    "24/7 support"
                ],
                limitations={
                    "max_exchanges": "unlimited",
                    "max_strategies": "unlimited",
                    "api_calls_per_month": "unlimited",
                    "trades_per_month": "unlimited",
                    "custom_features": True
                },
                stripe_price_id_monthly=os.getenv('STRIPE_INSTITUTIONAL_MONTHLY_PRICE_ID'),
                stripe_price_id_yearly=os.getenv('STRIPE_INSTITUTIONAL_YEARLY_PRICE_ID')
            )
        }
    
    def create_customer(self, user_id: str, email: str, name: str, company: str = None) -> Customer:
        """Create a new customer in Stripe and local database"""
        try:
            # Create Stripe customer
            stripe_customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'user_id': user_id,
                    'company': company or ''
                }
            )
            
            # Create local customer record
            customer = Customer(
                user_id=user_id,
                stripe_customer_id=stripe_customer.id,
                email=email,
                name=name,
                company=company
            )
            
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            
            logger.info(f"Created customer: {customer.id} for user: {user_id}")
            return customer
            
        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            self.db.rollback()
            raise
    
    def create_subscription(self, customer_id: int, plan_type: PlanType, 
                          billing_cycle: str = "monthly", trial_days: int = 7) -> Subscription:
        """Create a new subscription"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            plan = self.plans[plan_type]
            
            # Select price ID based on billing cycle
            price_id = (plan.stripe_price_id_yearly if billing_cycle == "yearly" 
                       else plan.stripe_price_id_monthly)
            
            if not price_id:
                raise ValueError(f"Price ID not configured for {plan_type.value} {billing_cycle}")
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer.stripe_customer_id,
                items=[{'price': price_id}],
                trial_period_days=trial_days,
                metadata={
                    'user_id': customer.user_id,
                    'plan_type': plan_type.value
                }
            )
            
            # Create local subscription record
            subscription = Subscription(
                customer_id=customer_id,
                stripe_subscription_id=stripe_subscription.id,
                plan_type=plan_type.value,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None
            )
            
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            self.db.rollback()
            raise
    
    def cancel_subscription(self, subscription_id: int, at_period_end: bool = True) -> bool:
        """Cancel a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            # Cancel in Stripe
            if at_period_end:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
            else:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELED.value
            
            subscription.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Canceled subscription: {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            self.db.rollback()
            raise
    
    def get_customer_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get active subscription for a user"""
        customer = self.db.query(Customer).filter(Customer.user_id == user_id).first()
        if not customer:
            return None
        
        subscription = self.db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value])
        ).first()
        
        return subscription
    
    def check_usage_limits(self, user_id: str, metric: str, current_usage: int) -> Dict[str, Any]:
        """Check if user has exceeded usage limits"""
        subscription = self.get_customer_subscription(user_id)
        if not subscription:
            return {"allowed": False, "reason": "No active subscription"}
        
        plan = self.plans[PlanType(subscription.plan_type)]
        limit = plan.limitations.get(metric)
        
        if limit == "unlimited":
            return {"allowed": True, "limit": "unlimited", "usage": current_usage}
        
        if isinstance(limit, int) and current_usage >= limit:
            return {
                "allowed": False,
                "reason": f"Usage limit exceeded",
                "limit": limit,
                "usage": current_usage
            }
        
        return {
            "allowed": True,
            "limit": limit,
            "usage": current_usage,
            "remaining": limit - current_usage if isinstance(limit, int) else "unlimited"
        }
    
    def record_usage(self, user_id: str, metric: str, quantity: int = 1):
        """Record usage for billing purposes"""
        customer = self.db.query(Customer).filter(Customer.user_id == user_id).first()
        if not customer:
            return
        
        billing_period = datetime.utcnow().strftime('%Y-%m')
        
        usage_record = UsageRecord(
            customer_id=customer.id,
            metric_name=metric,
            quantity=quantity,
            billing_period=billing_period
        )
        
        self.db.add(usage_record)
        self.db.commit()
    
    def get_usage_summary(self, user_id: str, period: str = None) -> Dict[str, int]:
        """Get usage summary for a user"""
        customer = self.db.query(Customer).filter(Customer.user_id == user_id).first()
        if not customer:
            return {}
        
        if not period:
            period = datetime.utcnow().strftime('%Y-%m')
        
        usage_records = self.db.query(UsageRecord).filter(
            UsageRecord.customer_id == customer.id,
            UsageRecord.billing_period == period
        ).all()
        
        summary = {}
        for record in usage_records:
            if record.metric_name not in summary:
                summary[record.metric_name] = 0
            summary[record.metric_name] += record.quantity
        
        return summary
    
    def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_webhook_secret
            )
        except ValueError:
            logger.error("Invalid payload")
            return {"error": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            return {"error": "Invalid signature"}
        
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
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return {"status": "success"}
    
    def _handle_subscription_created(self, subscription_data):
        """Handle subscription created webhook"""
        logger.info(f"Subscription created: {subscription_data['id']}")
    
    def _handle_subscription_updated(self, subscription_data):
        """Handle subscription updated webhook"""
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
            subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Updated subscription: {subscription.id}")
    
    def _handle_subscription_deleted(self, subscription_data):
        """Handle subscription deleted webhook"""
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED.value
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Deleted subscription: {subscription.id}")
    
    def _handle_payment_succeeded(self, invoice_data):
        """Handle successful payment webhook"""
        logger.info(f"Payment succeeded for invoice: {invoice_data['id']}")
        
        # Update or create invoice record
        invoice = self.db.query(Invoice).filter(
            Invoice.stripe_invoice_id == invoice_data['id']
        ).first()
        
        if not invoice:
            # Find customer
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == invoice_data['customer']
            ).first()
            
            if customer:
                invoice = Invoice(
                    customer_id=customer.id,
                    stripe_invoice_id=invoice_data['id'],
                    amount_paid=invoice_data['amount_paid'],
                    amount_due=invoice_data['amount_due'],
                    currency=invoice_data['currency'],
                    status=invoice_data['status'],
                    invoice_pdf=invoice_data.get('invoice_pdf'),
                    hosted_invoice_url=invoice_data.get('hosted_invoice_url'),
                    paid_at=datetime.fromtimestamp(invoice_data['status_transitions']['paid_at']) if invoice_data['status_transitions'].get('paid_at') else None
                )
                
                self.db.add(invoice)
                self.db.commit()
    
    def _handle_payment_failed(self, invoice_data):
        """Handle failed payment webhook"""
        logger.warning(f"Payment failed for invoice: {invoice_data['id']}")
        
        # You might want to send notifications, update subscription status, etc.
        # This is where you'd implement your dunning management logic

# Create tables
Base.metadata.create_all(bind=engine)

# Flask routes for billing API
def create_billing_routes(app: Flask):
    billing_manager = BillingManager()
    
    @app.route('/api/billing/plans', methods=['GET'])
    def get_plans():
        """Get available subscription plans"""
        plans_data = {}
        for plan_type, config in billing_manager.plans.items():
            plans_data[plan_type.value] = {
                'name': config.name,
                'price_monthly': config.price_monthly,
                'price_yearly': config.price_yearly,
                'features': config.features,
                'limitations': config.limitations
            }
        return jsonify(plans_data)
    
    @app.route('/api/billing/subscribe', methods=['POST'])
    def create_subscription():
        """Create a new subscription"""
        data = request.get_json()
        
        try:
            # Create or get customer
            customer = billing_manager.db.query(Customer).filter(
                Customer.user_id == data['user_id']
            ).first()
            
            if not customer:
                customer = billing_manager.create_customer(
                    user_id=data['user_id'],
                    email=data['email'],
                    name=data['name'],
                    company=data.get('company')
                )
            
            # Create subscription
            subscription = billing_manager.create_subscription(
                customer_id=customer.id,
                plan_type=PlanType(data['plan_type']),
                billing_cycle=data.get('billing_cycle', 'monthly'),
                trial_days=data.get('trial_days', 7)
            )
            
            return jsonify({
                'subscription_id': subscription.id,
                'stripe_subscription_id': subscription.stripe_subscription_id,
                'status': subscription.status
            })
            
        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/billing/webhook', methods=['POST'])
    def stripe_webhook():
        """Handle Stripe webhooks"""
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        result = billing_manager.handle_webhook(payload.decode('utf-8'), sig_header)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    @app.route('/api/billing/usage/<user_id>', methods=['GET'])
    def get_usage(user_id: str):
        """Get usage summary for user"""
        period = request.args.get('period')
        usage = billing_manager.get_usage_summary(user_id, period)
        return jsonify(usage)
    
    @app.route('/api/billing/limits/<user_id>/<metric>', methods=['GET'])
    def check_limits(user_id: str, metric: str):
        """Check usage limits for user"""
        current_usage = int(request.args.get('current_usage', 0))
        result = billing_manager.check_usage_limits(user_id, metric, current_usage)
        return jsonify(result)

if __name__ == '__main__':
    # Test the billing system
    billing = BillingManager()
    print("Billing system initialized successfully")
    print(f"Available plans: {list(billing.plans.keys())}")