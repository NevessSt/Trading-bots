import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, PlayIcon, StopIcon, ChartBarIcon, CogIcon } from '@heroicons/react/24/outline';
import { useTradingStore } from '../stores/tradingStore';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const BotDetail = () => {
  const { botId } = useParams();
  const navigate = useNavigate();
  
  const { 
    bots, 
    botStatus,
    tradeHistory,
    performance,
    loading, 
    error, 
    fetchBots, 
    fetchBotStatus,
    fetchTradeHistory,
    fetchPerformance,
    startBot, 
    stopBot,
    updateBot
  } = useTradingStore();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    strategy: '',
    symbol: '',
    risk_level: '',
    parameters: {}
  });
  
  useEffect(() => {
    fetchBots();
    if (botId) {
      fetchBotStatus(botId);
      fetchTradeHistory(botId);
      fetchPerformance(botId);
    }
  }, [botId, fetchBots, fetchBotStatus, fetchTradeHistory, fetchPerformance]);
  
  useEffect(() => {
    const bot = bots.find(b => b.id === botId);
    if (bot) {
      setFormData({
        name: bot.name,
        strategy: bot.strategy,
        symbol: bot.symbol,
        risk_level: bot.risk_level,
        parameters: bot.parameters || {}
      });
    }
  }, [bots, botId]);
  
  const bot = bots.find(b => b.id === botId);
  
  const handleStartBot = async () => {
    await startBot(botId);
  };

  const handleStopBot = async () => {
    await stopBot(botId);
  };
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleParameterChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [name]: value
      }
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await updateBot(botId, formData);
    setIsEditing(false);
  };
  
  const getBotStatusClass = (status) => {
    switch (status) {
      case 'running':
        return 'bg-success-100 text-success-800';
      case 'stopped':
        return 'bg-danger-100 text-danger-800';
      case 'paused':
        return 'bg-warning-100 text-warning-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getPerformanceChartData = () => {
    if (!performance || !performance.length) {
      return {
        labels: [],
        datasets: [{
          label: 'Bot Performance',
          data: [],
          borderColor: '#4F46E5',
          backgroundColor: 'rgba(79, 70, 229, 0.1)',
          tension: 0.1
        }]
      };
    }
    
    return {
      labels: performance.map(p => new Date(p.timestamp).toLocaleDateString()),
      datasets: [{
        label: 'Bot Performance (%)',
        data: performance.map(p => p.profit_percentage),
        borderColor: '#4F46E5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        tension: 0.1
      }]
    };
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-danger-50 border border-danger-200 text-danger-800 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error!</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }
  
  if (!bot) {
    return (
      <div className="bg-warning-50 border border-warning-200 text-warning-800 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Bot not found!</strong>
        <span className="block sm:inline"> The requested trading bot could not be found.</span>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center mb-6">
        <button 
          onClick={() => navigate('/dashboard/bots')} 
          className="mr-4 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </button>
        <h1 className="text-2xl font-semibold text-gray-900">{bot.name}</h1>
        <span className={`ml-4 px-2 py-1 text-xs font-semibold rounded-full ${getBotStatusClass(bot.status)}`}>
          {bot.status.charAt(0).toUpperCase() + bot.status.slice(1)}
        </span>
      </div>
      
      <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              className={`${activeTab === 'overview' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`${activeTab === 'trades' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('trades')}
            >
              Trade History
            </button>
            <button
              className={`${activeTab === 'performance' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('performance')}
            >
              Performance
            </button>
            <button
              className={`${activeTab === 'settings' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm`}
              onClick={() => setActiveTab('settings')}
            >
              Settings
            </button>
          </nav>
        </div>
        
        <div className="p-6">
          {activeTab === 'overview' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Strategy</h3>
                  <p className="text-lg font-semibold">{bot.strategy}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Symbol</h3>
                  <p className="text-lg font-semibold">{bot.symbol}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Risk Level</h3>
                  <p className="text-lg font-semibold">{bot.risk_level}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Total Profit</h3>
                  <p className={`text-lg font-semibold ${parseFloat(bot.profit) >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                    {parseFloat(bot.profit) >= 0 ? '+' : ''}{bot.profit}%
                  </p>
                </div>
              </div>
              
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Bot Status</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  {botStatus ? (
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Last Signal:</span>
                        <span className="font-medium">{botStatus.last_signal || 'None'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Last Trade:</span>
                        <span className="font-medium">{botStatus.last_trade_time ? new Date(botStatus.last_trade_time).toLocaleString() : 'None'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Current Position:</span>
                        <span className="font-medium">{botStatus.current_position || 'None'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Running Since:</span>
                        <span className="font-medium">{botStatus.running_since ? new Date(botStatus.running_since).toLocaleString() : 'Not running'}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500">Status information not available</p>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-4">
                {bot.status === 'running' ? (
                  <button
                    onClick={handleStopBot}
                    className="btn btn-danger flex items-center"
                  >
                    <StopIcon className="h-5 w-5 mr-2" />
                    Stop Bot
                  </button>
                ) : (
                  <button
                    onClick={handleStartBot}
                    className="btn btn-success flex items-center"
                  >
                    <PlayIcon className="h-5 w-5 mr-2" />
                    Start Bot
                  </button>
                )}
                
                <button
                  onClick={() => setActiveTab('performance')}
                  className="btn btn-outline-primary flex items-center"
                >
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  View Performance
                </button>
                
                <button
                  onClick={() => setActiveTab('settings')}
                  className="btn btn-outline-secondary flex items-center"
                >
                  <CogIcon className="h-5 w-5 mr-2" />
                  Bot Settings
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'trades' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Trade History</h3>
              
              {tradeHistory && tradeHistory.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Symbol
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Price
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Profit/Loss
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {tradeHistory.map((trade) => (
                        <tr key={trade.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(trade.timestamp).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${trade.type === 'buy' ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'}`}>
                              {trade.type.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {trade.symbol}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${trade.price}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {trade.amount}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <span className={trade.profit >= 0 ? 'text-success-600' : 'text-danger-600'}>
                              {trade.profit >= 0 ? '+' : ''}{trade.profit}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <p className="text-gray-500">No trade history available for this bot.</p>
                </div>
              )}
            </div>
          )}
          
          {activeTab === 'performance' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Analysis</h3>
              
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <div className="h-80">
                  <Line 
                    data={getPerformanceChartData()} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: true,
                          text: 'Bot Performance Over Time'
                        },
                      },
                      scales: {
                        y: {
                          ticks: {
                            callback: function(value) {
                              return value + '%';
                            }
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Total Trades</h3>
                  <p className="text-lg font-semibold">{tradeHistory ? tradeHistory.length : 0}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Win Rate</h3>
                  <p className="text-lg font-semibold">
                    {tradeHistory && tradeHistory.length > 0 ? 
                      `${((tradeHistory.filter(t => t.profit > 0).length / tradeHistory.length) * 100).toFixed(2)}%` : 
                      '0%'}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Best Trade</h3>
                  <p className="text-lg font-semibold text-success-600">
                    {tradeHistory && tradeHistory.length > 0 ? 
                      `+${Math.max(...tradeHistory.map(t => t.profit))}%` : 
                      '0%'}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-500 mb-1">Worst Trade</h3>
                  <p className="text-lg font-semibold text-danger-600">
                    {tradeHistory && tradeHistory.length > 0 ? 
                      `${Math.min(...tradeHistory.map(t => t.profit))}%` : 
                      '0%'}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'settings' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Bot Settings</h3>
                {!isEditing && (
                  <button 
                    onClick={() => setIsEditing(true)}
                    className="btn btn-outline-primary"
                  >
                    Edit Settings
                  </button>
                )}
              </div>
              
              {isEditing ? (
                <form onSubmit={handleSubmit}>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700">Bot Name</label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        required
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="risk_level" className="block text-sm font-medium text-gray-700">Risk Level</label>
                      <select
                        id="risk_level"
                        name="risk_level"
                        value={formData.risk_level}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        required
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    
                    <div className="border-t border-gray-200 pt-4">
                      <h4 className="text-md font-medium text-gray-900 mb-2">Strategy Parameters</h4>
                      
                      {formData.strategy === 'RSI' && (
                        <div className="space-y-4">
                          <div>
                            <label htmlFor="rsi_period" className="block text-sm font-medium text-gray-700">RSI Period</label>
                            <input
                              type="number"
                              id="rsi_period"
                              name="rsi_period"
                              value={formData.parameters.rsi_period || 14}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="1"
                              required
                            />
                          </div>
                          <div>
                            <label htmlFor="overbought" className="block text-sm font-medium text-gray-700">Overbought Level</label>
                            <input
                              type="number"
                              id="overbought"
                              name="overbought"
                              value={formData.parameters.overbought || 70}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="50"
                              max="100"
                              required
                            />
                          </div>
                          <div>
                            <label htmlFor="oversold" className="block text-sm font-medium text-gray-700">Oversold Level</label>
                            <input
                              type="number"
                              id="oversold"
                              name="oversold"
                              value={formData.parameters.oversold || 30}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="0"
                              max="50"
                              required
                            />
                          </div>
                        </div>
                      )}
                      
                      {formData.strategy === 'MACD' && (
                        <div className="space-y-4">
                          <div>
                            <label htmlFor="fast_period" className="block text-sm font-medium text-gray-700">Fast Period</label>
                            <input
                              type="number"
                              id="fast_period"
                              name="fast_period"
                              value={formData.parameters.fast_period || 12}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="1"
                              required
                            />
                          </div>
                          <div>
                            <label htmlFor="slow_period" className="block text-sm font-medium text-gray-700">Slow Period</label>
                            <input
                              type="number"
                              id="slow_period"
                              name="slow_period"
                              value={formData.parameters.slow_period || 26}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="1"
                              required
                            />
                          </div>
                          <div>
                            <label htmlFor="signal_period" className="block text-sm font-medium text-gray-700">Signal Period</label>
                            <input
                              type="number"
                              id="signal_period"
                              name="signal_period"
                              value={formData.parameters.signal_period || 9}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="1"
                              required
                            />
                          </div>
                        </div>
                      )}
                      
                      {formData.strategy === 'EMA Crossover' && (
                        <div className="space-y-4">
                          <div>
                            <label htmlFor="fast_ema" className="block text-sm font-medium text-gray-700">Fast EMA Period</label>
                            <input
                              type="number"
                              id="fast_ema"
                              name="fast_ema"
                              value={formData.parameters.fast_ema || 9}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="1"
                              required
                            />
                          </div>
                          <div>
                            <label htmlFor="slow_ema" className="block text-sm font-medium text-gray-700">Slow EMA Period</label>
                            <input
                              type="number"
                              id="slow_ema"
                              name="slow_ema"
                              value={formData.parameters.slow_ema || 21}
                              onChange={handleParameterChange}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                              min="1"
                              required
                            />
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex justify-end space-x-3 pt-4">
                      <button
                        type="button"
                        onClick={() => setIsEditing(false)}
                        className="btn btn-outline-secondary"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="btn btn-primary"
                      >
                        Save Changes
                      </button>
                    </div>
                  </div>
                </form>
              ) : (
                <div className="space-y-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-500 mb-2">General Settings</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Bot Name:</span>
                        <span className="font-medium">{bot.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Trading Pair:</span>
                        <span className="font-medium">{bot.symbol}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Strategy:</span>
                        <span className="font-medium">{bot.strategy}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Risk Level:</span>
                        <span className="font-medium">{bot.risk_level}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Created:</span>
                        <span className="font-medium">{new Date(bot.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-500 mb-2">Strategy Parameters</h4>
                    {bot.parameters && Object.keys(bot.parameters).length > 0 ? (
                      <div className="space-y-2">
                        {Object.entries(bot.parameters).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-gray-600">{key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                            <span className="font-medium">{value}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">No parameters available</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BotDetail;