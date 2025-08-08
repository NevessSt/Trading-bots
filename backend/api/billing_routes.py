from flask import Blueprint, request, jsonify, current_app
import stripe
from datetime import datetime

from auth.decorators import token_required, subscription_required
from auth.validators import validate_json_input
from models.user import User, db
from models.subscription import Subscription
from utils.logger import logger

billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')

# Initialize Stripe
def init_stripe():
    """Initialize Stripe with API key"""
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

@billing_bp.before_request
def before_request():
    """Initialize Stripe before each request"""
    init_stripe()

@billing_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get available subscription plans"""
    try:
        plans = Subscription.PLANS
        
        # Format plans for frontend
        formatted_plans = []
        for plan_id, plan_info in plans.items():
            formatted_plans.append({
                'id': plan_id,
                'name': plan_info['name'],
                'price': plan_info['price'],
                'currency': plan_info['currency'],
                'interval': plan_info['interval'],
                'features': plan_info['features']
            })
        
        return jsonify({'plans': formatted_plans}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get plans error: {str(e)}")
        return jsonify({'error': 'Failed to get plans'}), 500

@billing_bp.route('/subscription', methods=['GET'])
@token_required
def get_subscription():
    """Get user's current subscription"""
    try:
        user = request.current_user
        subscription = User.get_subscription(str(user['_id']))
        
        if not subscription:
            return jsonify({'error': 'No subscription found'}), 404
        
        # Get plan features
        plan = subscription.get('plan', 'free')
        features = Subscription.get_plan_features(plan)
        
        # Get usage statistics
        from models.bot import Bot
        current_bots = Bot.count_by_user_id(str(user['_id']))
        
        return jsonify({
            'subscription': {
                'id': str(subscription['_id']),
                'plan': plan,
                'status': subscription.get('status', 'active'),
                'created_at': subscription.get('created_at').isoformat() if subscription.get('created_at') else None,
                'next_billing_date': subscription.get('next_billing_date').isoformat() if subscription.get('next_billing_date') else None,
                'stripe_subscription_id': subscription.get('stripe_subscription_id'),
                'features': features,
                'usage': {
                    'current_bots': current_bots,
                    'max_bots': features.get('max_bots', 1)
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get subscription error: {str(e)}")
        return jsonify({'error': 'Failed to get subscription'}), 500

@billing_bp.route('/create-checkout-session', methods=['POST'])
@token_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        user = request.current_user
        data = request.get_json()
        
        plan_id = data.get('plan_id')
        if not plan_id or plan_id not in Subscription.PLANS:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        if plan_id == 'free':
            return jsonify({'error': 'Cannot create checkout for free plan'}), 400
        
        plan_info = Subscription.PLANS[plan_id]
        
        # Create Stripe customer if doesn't exist
        stripe_customer_id = user.stripe_customer_id
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                metadata={'user_id': str(user.id)}
            )
            stripe_customer_id = customer.id
            
            # Update user with Stripe customer ID
            user.stripe_customer_id = stripe_customer_id
            user.save()
        
        # Create checkout session
        success_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000') + '/billing/success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000') + '/billing/cancel'
        
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': plan_info['currency'].lower(),
                    'product_data': {
                        'name': f"Trading Bot Platform - {plan_info['name']} Plan",
                        'description': f"Monthly subscription to {plan_info['name']} plan"
                    },
                    'unit_amount': int(plan_info['price'] * 100),  # Convert to cents
                    'recurring': {
                        'interval': plan_info['interval']
                    }
                },
                'quantity': 1
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user['_id']),
                'plan_id': plan_id
            }
        )
        
        return jsonify({
            'checkout_url': session.url,
            'session_id': session.id
        }), 200
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
        return jsonify({'error': 'Payment processing error'}), 500
    except Exception as e:
        current_app.logger.error(f"Create checkout session error: {str(e)}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@billing_bp.route('/portal-session', methods=['POST'])
@token_required
def create_portal_session():
    """Create Stripe customer portal session"""
    try:
        user = request.current_user
        
        stripe_customer_id = user.stripe_customer_id
        if not stripe_customer_id:
            return jsonify({'error': 'No billing account found'}), 404
        
        return_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000') + '/billing'
        
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url
        )
        
        return jsonify({
            'portal_url': session.url
        }), 200
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe portal error: {str(e)}")
        return jsonify({'error': 'Failed to create portal session'}), 500
    except Exception as e:
        current_app.logger.error(f"Create portal session error: {str(e)}")
        return jsonify({'error': 'Failed to create portal session'}), 500

@billing_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        if not endpoint_secret:
            current_app.logger.error("Stripe webhook secret not configured")
            return jsonify({'error': 'Webhook not configured'}), 500
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            current_app.logger.error("Invalid payload in Stripe webhook")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            current_app.logger.error("Invalid signature in Stripe webhook")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            _handle_successful_payment(session)
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            _handle_successful_renewal(invoice)
        
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            _handle_failed_payment(invoice)
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            _handle_subscription_cancelled(subscription)
        
        else:
            current_app.logger.info(f"Unhandled Stripe event type: {event['type']}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Stripe webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@billing_bp.route('/cancel-subscription', methods=['POST'])
@token_required
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user = request.current_user
        subscription = user.subscription
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        stripe_subscription_id = subscription.stripe_subscription_id
        if stripe_subscription_id:
            # Cancel in Stripe
            stripe.Subscription.delete(stripe_subscription_id)
        
        # Update local subscription
        subscription.cancel_subscription()
        
        # Log event
        log_security_event('subscription_cancelled', str(user.id), {
            'plan': subscription.plan,
            'ip_address': request.remote_addr
        })
        
        return jsonify({'message': 'Subscription cancelled successfully'}), 200
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe cancellation error: {str(e)}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500
    except Exception as e:
        current_app.logger.error(f"Cancel subscription error: {str(e)}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500

def _handle_successful_payment(session):
    """Handle successful payment from Stripe"""
    try:
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']
        
        # Get Stripe subscription
        stripe_subscription = stripe.Subscription.retrieve(session['subscription'])
        
        # Update user subscription
        user = User.query.get(user_id)
        if user and user.subscription:
            user.subscription.upgrade_subscription(plan_id, stripe_subscription.id)
        else:
            # Create new subscription if user doesn't have one
            subscription = Subscription(
                user_id=user_id,
                plan=plan_id,
                stripe_subscription_id=stripe_subscription.id,
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()
        
        # Log event
        logger.log_security_event('subscription_upgraded', user_id, {
            'plan': plan_id,
            'stripe_subscription_id': stripe_subscription.id
        })
        
        current_app.logger.info(f"Subscription upgraded for user {user_id} to {plan_id}")
        
    except Exception as e:
        current_app.logger.error(f"Handle successful payment error: {str(e)}")

def _handle_successful_renewal(invoice):
    """Handle successful subscription renewal"""
    try:
        customer_id = invoice['customer']
        
        # Find user by Stripe customer ID
        users = User.get_collection()
        user = users.find_one({'stripe_customer_id': customer_id})
        
        if user:
            # Update next billing date
            from datetime import timedelta
            next_billing = datetime.utcnow() + timedelta(days=30)
            
            Subscription.update_by_user_id(str(user['_id']), {
                'status': 'active',
                'next_billing_date': next_billing
            })
            
            current_app.logger.info(f"Subscription renewed for user {user['_id']}")
        
    except Exception as e:
        current_app.logger.error(f"Handle successful renewal error: {str(e)}")

def _handle_failed_payment(invoice):
    """Handle failed payment"""
    try:
        customer_id = invoice['customer']
        
        # Find user by Stripe customer ID
        users = User.get_collection()
        user = users.find_one({'stripe_customer_id': customer_id})
        
        if user:
            # Update subscription status
            Subscription.update_by_user_id(str(user['_id']), {
                'status': 'past_due'
            })
            
            # Log event
            log_security_event('payment_failed', str(user['_id']), {
                'invoice_id': invoice['id']
            })
            
            current_app.logger.warning(f"Payment failed for user {user['_id']}")
        
    except Exception as e:
        current_app.logger.error(f"Handle failed payment error: {str(e)}")

def _handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription['customer']
        
        # Find user by Stripe customer ID
        users = User.get_collection()
        user = users.find_one({'stripe_customer_id': customer_id})
        
        if user:
            # Cancel local subscription
            Subscription.cancel_subscription(str(user['_id']))
            
            current_app.logger.info(f"Subscription cancelled for user {user['_id']}")
        
    except Exception as e:
        current_app.logger.error(f"Handle subscription cancelled error: {str(e)}")