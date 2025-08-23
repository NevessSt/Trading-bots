import React from 'react';
import {
  PlayIcon,
  StopIcon,
  TrashIcon,
  ChartBarIcon,
  CogIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import classNames from 'classnames';
import { useLicense } from '../contexts/LicenseContext';

const BotCard = ({ bot, onStart, onStop, onDelete, onViewTrades }) => {
  const { requiresLicense } = useLicense();
  const isRunning = bot.status === 'running';
  const isPaused = bot.status === 'paused';
  const isStopped = bot.status === 'stopped';
  const hasError = bot.status === 'error';

  const getStatusColor = () => {
    switch (bot.status) {
      case 'running':
        return 'text-green-600 bg-green-100';
      case 'paused':
        return 'text-yellow-600 bg-yellow-100';
      case 'stopped':
        return 'text-gray-600 bg-gray-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  const formatPercentage = (value) => {
    const percentage = (value || 0) * 100;
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-300 hover-lift animate-fade-in-up hover:scale-105 transform-gpu">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            {bot.name}
          </h3>
          <span className={classNames(
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize',
            getStatusColor()
          )}>
            {bot.status}
          </span>
        </div>
        
        <div className="flex items-center text-sm text-gray-600">
          <span className="font-medium">{bot.strategy}</span>
          <span className="mx-2">•</span>
          <span>{bot.exchange}</span>
          <span className="mx-2">•</span>
          <span>{bot.symbol}</span>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="p-6">
        <div className="grid grid-cols-2 gap-4 mb-4 animate-stagger-1">
          <div className="animate-fade-in hover:scale-105 transition-transform duration-200">
            <p className="text-sm text-gray-600">Total P&L</p>
            <p className={classNames(
              'text-lg font-semibold transition-colors duration-200',
              (bot.total_pnl || 0) >= 0 ? 'text-green-600 hover:text-green-700' : 'text-red-600 hover:text-red-700'
            )}>
              {formatCurrency(bot.total_pnl)}
            </p>
          </div>
          
          <div className="animate-fade-in hover:scale-105 transition-transform duration-200">
            <p className="text-sm text-gray-600">ROI</p>
            <p className={classNames(
              'text-lg font-semibold transition-colors duration-200',
              (bot.roi || 0) >= 0 ? 'text-green-600 hover:text-green-700' : 'text-red-600 hover:text-red-700'
            )}>
              {formatPercentage(bot.roi)}
            </p>
          </div>
          
          <div className="animate-fade-in hover:scale-105 transition-transform duration-200">
            <p className="text-sm text-gray-600">Total Trades</p>
            <p className="text-lg font-semibold text-gray-900 hover:text-gray-700 transition-colors duration-200">
              {bot.total_trades || 0}
            </p>
          </div>
          
          <div className="animate-fade-in hover:scale-105 transition-transform duration-200">
            <p className="text-sm text-gray-600">Win Rate</p>
            <p className="text-lg font-semibold text-gray-900 hover:text-gray-700 transition-colors duration-200">
              {((bot.win_rate || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Additional Info */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Balance:</span>
            <span className="font-medium">{formatCurrency(bot.balance)}</span>
          </div>
          
          {bot.last_trade_at && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Last Trade:</span>
              <span className="font-medium">
                {format(new Date(bot.last_trade_at), 'MMM dd, HH:mm')}
              </span>
            </div>
          )}
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Created:</span>
            <span className="font-medium">
              {format(new Date(bot.created_at), 'MMM dd, yyyy')}
            </span>
          </div>
        </div>

        {/* Error Message */}
        {hasError && bot.error_message && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">
              <strong>Error:</strong> {bot.error_message}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 animate-stagger-2">
          {isStopped || isPaused || hasError ? (
            <button
              onClick={() => requiresLicense('bot_control') && onStart()}
              className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-all duration-200 hover:scale-105 hover:shadow-md transform-gpu"
            >
              <PlayIcon className="h-4 w-4 mr-1" />
              Start
            </button>
          ) : (
            <button
              onClick={() => requiresLicense('bot_control') && onStop()}
              className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-all duration-200 hover:scale-105 hover:shadow-md transform-gpu"
            >
              <StopIcon className="h-4 w-4 mr-1" />
              Stop
            </button>
          )}
          
          <button
            onClick={onViewTrades}
            className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 hover:scale-105 hover:shadow-md transform-gpu"
          >
            <ChartBarIcon className="h-4 w-4 mr-1" />
            Trades
          </button>
          
          <button
            onClick={() => requiresLicense('bot_management') && onDelete()}
            className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-all duration-200 hover:scale-105 hover:shadow-md transform-gpu"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Running Indicator */}
      {isRunning && (
        <div className="px-6 py-3 bg-green-50 border-t border-green-200 animate-fade-in-up">
          <div className="flex items-center text-sm text-green-700">
            <div className="flex-shrink-0">
              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse-glow"></div>
            </div>
            <span className="ml-2 font-medium animate-fade-in">Bot is actively trading</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default BotCard;