import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import { loadStripe } from '@stripe/stripe-js';
import {
  CreditCardIcon,
  CheckIcon,
  XMarkIcon,
  ArrowUpIcon,
  ExternalLinkIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import classNames from 'classnames';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const Billing = () => {
  const { user, subscription, fetchSubscription } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get('/api/billing/plans');
      setPlans(response.data.plans || []);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      toast.error('Failed to load subscription plans');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId) => {
    if (planId === 'free') {
      toast.error('Cannot upgrade to free plan');
      return;
    }

    setUpgrading(true);
    setSelectedPlan(planId);

    try {
      const response = await axios.post('/api/billing/create-checkout-session', {
        plan_id: planId
      });

      const stripe = await stripePromise;
      window.location.href = response.data.checkout_url;
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to create checkout session';
      toast.error(message);
    } finally {
      setUpgrading(false);
      setSelectedPlan(null);
    }
  };

  const handleManageBilling = async () => {
    try {
      const response = await axios.post('/api/billing/portal-session');
      window.location.href = response.data.portal_url;
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to open billing portal';
      toast.error(message);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.')) {
      return;
    }

    try {
      await axios.post('/api/billing/cancel-subscription');
      toast.success('Subscription cancelled successfully');
      await fetchSubscription();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to cancel subscription';
      toast.error(message);
    }
  };

  const getPlanFeatures = (planId) => {
    const features = {
      free: [
        '1 Trading Bot',
        '1 API Key',
        'Basic Strategies',
        'Email Support',
        'Trade History (30 days)'
      ],
      pro: [
        '5 Trading Bots',
        '3 API Keys',
        'Advanced Strategies',
        'Priority Support',
        'Trade History (1 year)',
        'Custom Indicators',
        'Risk Management Tools'
      ],
      enterprise: [
        'Unlimited Trading Bots',
        'Unlimited API Keys',
        'All Strategies',
        '24/7 Phone Support',
        'Unlimited Trade History',
        'Custom Indicators',
        'Advanced Risk Management',
        'White-label Options',
        'Dedicated Account Manager'
      ]
    };
    return features[planId] || [];
  };

  const isCurrentPlan = (planId) => {
    return subscription?.plan === planId;
  };

  const canUpgradeTo = (planId) => {
    const planOrder = { free: 0, pro: 1, enterprise: 2 };
    const currentOrder = planOrder[subscription?.plan] || 0;
    const targetOrder = planOrder[planId] || 0;
    return targetOrder > currentOrder;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Billing & Subscription
          </h1>
          <p className="text-gray-600 mt-2">
            Manage your subscription and billing information
          </p>
        </div>

        {/* Current Subscription */}
        {subscription && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Current Subscription
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center mb-2">
                    <CreditCardIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <span className="text-sm text-gray-600">Plan:</span>
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded capitalize">
                      {subscription.plan}
                    </span>
                  </div>
                  
                  <div className="flex items-center mb-2">
                    <span className="text-sm text-gray-600">Status:</span>
                    <span className={classNames(
                      'ml-2 px-2 py-1 text-sm font-medium rounded capitalize',
                      subscription.status === 'active' ? 'bg-green-100 text-green-800' :
                      subscription.status === 'past_due' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    )}>
                      {subscription.status}
                    </span>
                  </div>
                  
                  {subscription.next_billing_date && subscription.plan !== 'free' && (
                    <div className="flex items-center">
                      <span className="text-sm text-gray-600">Next billing:</span>
                      <span className="ml-2 text-sm font-medium text-gray-900">
                        {format(new Date(subscription.next_billing_date), 'MMMM dd, yyyy')}
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col space-y-2">
                  {subscription.plan !== 'free' && (
                    <button
                      onClick={handleManageBilling}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <ExternalLinkIcon className="h-4 w-4 mr-2" />
                      Manage Billing
                    </button>
                  )}
                  
                  {subscription.plan !== 'free' && subscription.status === 'active' && (
                    <button
                      onClick={handleCancelSubscription}
                      className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
                    >
                      <XMarkIcon className="h-4 w-4 mr-2" />
                      Cancel Subscription
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Subscription Plans */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Choose Your Plan
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan) => {
              const features = getPlanFeatures(plan.id);
              const isCurrent = isCurrentPlan(plan.id);
              const canUpgrade = canUpgradeTo(plan.id);
              const isPopular = plan.id === 'pro';
              
              return (
                <div
                  key={plan.id}
                  className={classNames(
                    'relative bg-white rounded-lg shadow-lg overflow-hidden',
                    isPopular ? 'ring-2 ring-blue-500' : '',
                    isCurrent ? 'ring-2 ring-green-500' : ''
                  )}
                >
                  {isPopular && (
                    <div className="absolute top-0 left-0 right-0 bg-blue-500 text-white text-center py-1 text-sm font-medium">
                      Most Popular
                    </div>
                  )}
                  
                  {isCurrent && (
                    <div className="absolute top-0 left-0 right-0 bg-green-500 text-white text-center py-1 text-sm font-medium">
                      Current Plan
                    </div>
                  )}
                  
                  <div className={classNames('p-6', isPopular || isCurrent ? 'pt-10' : '')}>
                    <h3 className="text-xl font-semibold text-gray-900 capitalize">
                      {plan.name}
                    </h3>
                    
                    <div className="mt-4">
                      <span className="text-4xl font-bold text-gray-900">
                        ${plan.price}
                      </span>
                      {plan.price > 0 && (
                        <span className="text-gray-600">/{plan.interval}</span>
                      )}
                    </div>
                    
                    <ul className="mt-6 space-y-3">
                      {features.map((feature, index) => (
                        <li key={index} className="flex items-start">
                          <CheckIcon className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    
                    <div className="mt-8">
                      {isCurrent ? (
                        <button
                          disabled
                          className="w-full bg-green-100 text-green-800 py-2 px-4 rounded-md font-medium cursor-not-allowed"
                        >
                          Current Plan
                        </button>
                      ) : canUpgrade ? (
                        <button
                          onClick={() => handleUpgrade(plan.id)}
                          disabled={upgrading}
                          className={classNames(
                            'w-full py-2 px-4 rounded-md font-medium transition-colors',
                            upgrading && selectedPlan === plan.id
                              ? 'bg-gray-400 text-white cursor-not-allowed'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          )}
                        >
                          {upgrading && selectedPlan === plan.id ? (
                            'Processing...'
                          ) : (
                            <>
                              <ArrowUpIcon className="h-4 w-4 inline mr-2" />
                              Upgrade to {plan.name}
                            </>
                          )}
                        </button>
                      ) : (
                        <button
                          disabled
                          className="w-full bg-gray-100 text-gray-500 py-2 px-4 rounded-md font-medium cursor-not-allowed"
                        >
                          Cannot Downgrade
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* FAQ Section */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Frequently Asked Questions
            </h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Can I change my plan anytime?
                </h3>
                <p className="text-gray-600">
                  Yes, you can upgrade your plan at any time. Downgrades will take effect at the end of your current billing period.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  What happens if I cancel my subscription?
                </h3>
                <p className="text-gray-600">
                  You'll continue to have access to premium features until the end of your current billing period. After that, your account will be downgraded to the free plan.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Are there any setup fees?
                </h3>
                <p className="text-gray-600">
                  No, there are no setup fees. You only pay the monthly subscription fee for your chosen plan.
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Is my payment information secure?
                </h3>
                <p className="text-gray-600">
                  Yes, all payments are processed securely through Stripe. We never store your payment information on our servers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Billing;