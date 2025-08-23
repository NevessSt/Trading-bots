import React from 'react';
import {
  CreditCardIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ArrowUpIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import classNames from 'classnames';

const SubscriptionCard = ({ subscription }) => {
  if (!subscription) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center">
          <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500" />
          <div className="ml-4">
            <h3 className="text-lg font-medium text-gray-900">
              No Subscription Found
            </h3>
            <p className="text-gray-600">
              Please contact support if this is an error.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const { plan, status, features, usage, next_billing_date } = subscription;
  
  const getPlanColor = () => {
    switch (plan) {
      case 'free':
        return 'bg-gray-100 text-gray-800';
      case 'pro':
        return 'bg-blue-100 text-blue-800';
      case 'enterprise':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'past_due':
        return 'text-yellow-600 bg-yellow-100';
      case 'cancelled':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getUsagePercentage = (current, max) => {
    if (max === -1) return 0; // Unlimited
    return Math.min((current / max) * 100, 100);
  };

  const getUsageColor = (current, max) => {
    const percentage = getUsagePercentage(current, max);
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <CreditCardIcon className="h-8 w-8 text-gray-400" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">
                Subscription Plan
              </h3>
              <div className="flex items-center mt-1">
                <span className={classNames(
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize mr-2',
                  getPlanColor()
                )}>
                  {plan} Plan
                </span>
                <span className={classNames(
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize',
                  getStatusColor()
                )}>
                  {status}
                </span>
              </div>
            </div>
          </div>
          
          {plan !== 'enterprise' && (
            <a
              href="/billing"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <ArrowUpIcon className="h-4 w-4 mr-2" />
              Upgrade
            </a>
          )}
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Bot Limit */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              Trading Bots
            </h4>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">
                {usage?.current_bots || 0} / {features?.max_bots === -1 ? '∞' : features?.max_bots || 1}
              </span>
              <span className="text-sm font-medium text-gray-900">
                {features?.max_bots === -1 ? 'Unlimited' : 
                 `${Math.max(0, (features?.max_bots || 1) - (usage?.current_bots || 0))} remaining`}
              </span>
            </div>
            {features?.max_bots !== -1 && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={classNames(
                    'h-2 rounded-full transition-all duration-300',
                    getUsageColor(usage?.current_bots || 0, features?.max_bots || 1)
                  )}
                  style={{
                    width: `${getUsagePercentage(usage?.current_bots || 0, features?.max_bots || 1)}%`
                  }}
                ></div>
              </div>
            )}
          </div>

          {/* API Keys */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              API Keys
            </h4>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">
                {usage?.current_api_keys || 0} / {features?.max_api_keys === -1 ? '∞' : features?.max_api_keys || 1}
              </span>
              <span className="text-sm font-medium text-gray-900">
                {features?.max_api_keys === -1 ? 'Unlimited' : 
                 `${Math.max(0, (features?.max_api_keys || 1) - (usage?.current_api_keys || 0))} remaining`}
              </span>
            </div>
            {features?.max_api_keys !== -1 && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={classNames(
                    'h-2 rounded-full transition-all duration-300',
                    getUsageColor(usage?.current_api_keys || 0, features?.max_api_keys || 1)
                  )}
                  style={{
                    width: `${getUsagePercentage(usage?.current_api_keys || 0, features?.max_api_keys || 1)}%`
                  }}
                ></div>
              </div>
            )}
          </div>

          {/* Features */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              Features
            </h4>
            <div className="space-y-1">
              {features?.advanced_strategies && (
                <div className="flex items-center text-sm text-green-600">
                  <CheckIcon className="h-4 w-4 mr-1" />
                  Advanced Strategies
                </div>
              )}
              {features?.priority_support && (
                <div className="flex items-center text-sm text-green-600">
                  <CheckIcon className="h-4 w-4 mr-1" />
                  Priority Support
                </div>
              )}
              {features?.custom_indicators && (
                <div className="flex items-center text-sm text-green-600">
                  <CheckIcon className="h-4 w-4 mr-1" />
                  Custom Indicators
                </div>
              )}
              {features?.api_access && (
                <div className="flex items-center text-sm text-green-600">
                  <CheckIcon className="h-4 w-4 mr-1" />
                  API Access
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Billing Info */}
        {plan !== 'free' && next_billing_date && (
          <div className="border-t border-gray-200 pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">
                  Next billing date
                </p>
                <p className="text-sm font-medium text-gray-900">
                  {format(new Date(next_billing_date), 'MMMM dd, yyyy')}
                </p>
              </div>
              <a
                href="/billing"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Manage Billing
              </a>
            </div>
          </div>
        )}

        {/* Warnings */}
        {status === 'past_due' && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Payment Past Due
                </h3>
                <p className="text-sm text-yellow-700 mt-1">
                  Your subscription payment is overdue. Please update your payment method to avoid service interruption.
                </p>
                <div className="mt-2">
                  <a
                    href="/billing"
                    className="text-sm font-medium text-yellow-800 underline"
                  >
                    Update Payment Method
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {status === 'cancelled' && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Subscription Cancelled
                </h3>
                <p className="text-sm text-red-700 mt-1">
                  Your subscription has been cancelled. You can continue using the service until your current billing period ends.
                </p>
                <div className="mt-2">
                  <a
                    href="/billing"
                    className="text-sm font-medium text-red-800 underline"
                  >
                    Reactivate Subscription
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionCard;