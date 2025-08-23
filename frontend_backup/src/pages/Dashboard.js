import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
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
  Filler,
} from 'chart.js';
import {
  CurrencyDollarIcon,
  CubeIcon,
  ClockIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  PlusIcon,
  EyeIcon,
  Cog6ToothIcon,
  BoltIcon,
  TrendingUpIcon,
  TrendingDownIcon,
} from '@heroicons/react/24/outline';
import {
  CurrencyDollarIcon as CurrencyDollarIconSolid,
  CubeIcon as CubeIconSolid,
  ClockIcon as ClockIconSolid,
  ChartBarIcon as ChartBarIconSolid,
} from '@heroicons/react/24/solid';
import BotCard from '../components/BotCard';
import CreateBotModal from '../components/CreateBotModal';
import TradeHistoryModal from '../components/TradeHistoryModal';
import ApiKeysModal from '../components/ApiKeysModal';
import SubscriptionCard from '../components/SubscriptionCard';
import { format } from 'date-fns';
import axios from 'axios';
import { toast } from 'react-hot-toast';

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

const Dashboard = () => {
  const { user } = useAuth();
  const { isDark } = useTheme();
  const { 
    bots, 
    tradeHistory, 
    performance, 
    isLoading: storeLoading,
    fetchBots, 
    fetchTradeHistory, 
    fetchPerformance 
  } = useTradingStore();
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');
  
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        await Promise.all([
          fetchBots(),
          fetchTradeHistory({ limit: 5 }),
          fetchPerformance('1m')
        ]);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [fetchBots, fetchTradeHistory, fetchPerformance]);
  
  // Enhanced chart data with theme support
  const getChartData = () => {
    const timeframes = {
      '1D': {
        labels: ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
        data: [10000, 10120, 10080, 10200, 10150, 10300, 10280, 10400]
      },
      '1W': {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        data: [10000, 10200, 10150, 10400, 10300, 10600, 10800]
      },
      '1M': {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        data: [10000, 10500, 10200, 10800]
      },
      '1Y': {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        data: [8000, 8500, 9200, 9800, 10200, 10800, 11200, 10900, 11500, 12000, 11800, 12400]
      }
    };

    const currentData = timeframes[selectedTimeframe];
    const gradient = isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.05)';
    
    return {
      labels: currentData.labels,
      datasets: [
        {
          label: 'Portfolio Value',
          data: currentData.data,
          borderColor: '#3b82f6',
          backgroundColor: gradient,
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    };
  };
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
        titleColor: isDark ? '#f1f5f9' : '#0f172a',
        bodyColor: isDark ? '#cbd5e1' : '#475569',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          label: function(context) {
            return `$${context.parsed.y.toLocaleString()}`;
          }
        }
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: isDark ? '#94a3b8' : '#64748b',
          font: {
            size: 12,
          },
        },
      },
      y: {
        beginAtZero: false,
        grid: {
          color: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(148, 163, 184, 0.2)',
          drawBorder: false,
        },
        ticks: {
          color: isDark ? '#94a3b8' : '#64748b',
          font: {
            size: 12,
          },
          callback: function(value) {
            return '$' + value.toLocaleString();
          },
        },
      },
    },
  };
  
  // Enhanced stats with modern design
  const stats = [
    { 
      name: 'Total Profit', 
      value: '$2,847.50', 
      change: '+12.5%',
      changeType: 'positive',
      icon: CurrencyDollarIcon, 
      iconSolid: CurrencyDollarIconSolid,
      gradient: 'from-emerald-500 to-teal-600',
      bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
      textColor: 'text-emerald-700 dark:text-emerald-300'
    },
    { 
      name: 'Active Bots', 
      value: bots?.length || '0', 
      change: '+2',
      changeType: 'positive',
      icon: CubeIcon, 
      iconSolid: CubeIconSolid,
      gradient: 'from-blue-500 to-indigo-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      textColor: 'text-blue-700 dark:text-blue-300'
    },
    { 
      name: 'Total Trades', 
      value: '1,247', 
      change: '+89',
      changeType: 'positive',
      icon: ClockIcon, 
      iconSolid: ClockIconSolid,
      gradient: 'from-purple-500 to-pink-600',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      textColor: 'text-purple-700 dark:text-purple-300'
    },
    { 
      name: 'Win Rate', 
      value: '73.2%', 
      change: '+5.1%',
      changeType: 'positive',
      icon: ChartBarIcon, 
      iconSolid: ChartBarIconSolid,
      gradient: 'from-amber-500 to-orange-600',
      bgColor: 'bg-amber-50 dark:bg-amber-900/20',
      textColor: 'text-amber-700 dark:text-amber-300'
    },
  ];
  
  // Placeholder recent trades
  const recentTrades = tradeHistory || [
    { _id: '1', symbol: 'BTC/USDT', type: 'buy', amount: 0.01, price: 36000, profit: null, createdAt: new Date().toISOString() },
    { _id: '2', symbol: 'ETH/USDT', type: 'sell', amount: 0.5, price: 2400, profit: 120, createdAt: new Date(Date.now() - 3600000).toISOString() },
    { _id: '3', symbol: 'BNB/USDT', type: 'buy', amount: 1, price: 320, profit: null, createdAt: new Date(Date.now() - 7200000).toISOString() },
    { _id: '4', symbol: 'SOL/USDT', type: 'sell', amount: 5, price: 80, profit: -20, createdAt: new Date(Date.now() - 14400000).toISOString() },
    { _id: '5', symbol: 'ADA/USDT', type: 'buy', amount: 100, price: 0.5, profit: null, createdAt: new Date(Date.now() - 28800000).toISOString() },
  ];
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            {/* Header skeleton */}
            <div className="mb-8">
              <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg w-1/3 mb-2"></div>
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
            </div>
            
            {/* Stats skeleton */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
                    <div className="w-16 h-6 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </div>
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3 mb-2"></div>
                  <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
                </div>
              ))}
            </div>
            
            {/* Chart skeleton */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 mb-8">
              <div className="flex items-center justify-between mb-6">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
                <div className="flex space-x-2">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="w-12 h-8 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  ))}
                </div>
              </div>
              <div className="h-80 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
            </div>
            
            {/* Table skeleton */}
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
              <div className="p-6 border-b border-slate-200 dark:border-slate-700">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
              </div>
              <div className="p-6">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-4 py-3">
                    <div className="w-16 h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                    <div className="w-12 h-6 bg-slate-200 dark:bg-slate-700 rounded"></div>
                    <div className="w-20 h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                    <div className="w-24 h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                    <div className="w-16 h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                    <div className="w-32 h-4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                Welcome back, {user?.email?.split('@')[0] || 'Trader'}!
              </h1>
              <p className="mt-2 text-slate-600 dark:text-slate-400">
                Here's your trading performance overview for today.
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button className="inline-flex items-center px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors duration-200">
                <Cog6ToothIcon className="w-4 h-4 mr-2" />
                Settings
              </button>
              <button className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors duration-200">
                <PlusIcon className="w-4 h-4 mr-2" />
                New Bot
              </button>
            </div>
          </div>
        </div>
      
        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {stats.map((stat) => {
            const IconSolid = stat.iconSolid;
            return (
              <div key={stat.name} className="group bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-all duration-200 hover:-translate-y-1">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.gradient} shadow-lg`}>
                    <IconSolid className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex items-center space-x-1 text-sm">
                    {stat.changeType === 'positive' ? (
                      <TrendingUpIcon className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <TrendingDownIcon className="w-4 h-4 text-red-500" />
                    )}
                    <span className={`font-medium ${
                      stat.changeType === 'positive' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                    }`}>
                      {stat.change}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {stat.value}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      
        {/* Performance Chart */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Portfolio Performance</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Track your trading performance over time</p>
            </div>
            <div className="flex items-center space-x-2">
              {['1D', '1W', '1M', '1Y'].map((timeframe) => (
                <button
                  key={timeframe}
                  onClick={() => setSelectedTimeframe(timeframe)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                    selectedTimeframe === timeframe
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  {timeframe}
                </button>
              ))}
            </div>
          </div>
          <div className="h-80">
            <Line data={getChartData()} options={chartOptions} />
          </div>
        </div>
      
        {/* Recent Trades */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Recent Trades</h2>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Your latest trading activity</p>
              </div>
              <Link 
                to="/history" 
                className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors duration-200"
              >
                <EyeIcon className="w-4 h-4 mr-1" />
                View all
              </Link>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Profit/Loss
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {recentTrades.map((trade, index) => (
                  <tr key={trade._id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors duration-150">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                          <span className="text-white text-xs font-bold">
                            {trade.symbol.split('/')[0].charAt(0)}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {trade.symbol}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        trade.type === 'buy' 
                          ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800' 
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                      }`}>
                        <BoltIcon className="w-3 h-3 mr-1" />
                        {trade.type.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 dark:text-slate-400">
                      {trade.amount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-slate-100">
                      ${trade.price.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {trade.profit !== null ? (
                        <div className={`inline-flex items-center px-2 py-1 rounded-lg ${
                          trade.profit >= 0 
                            ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300' 
                            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                        }`}>
                          {trade.profit >= 0 ? (
                            <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
                          ) : (
                            <ArrowTrendingDownIcon className="w-4 h-4 mr-1" />
                          )}
                          <span className="font-medium">
                            ${Math.abs(trade.profit).toLocaleString()}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500">Pending</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 dark:text-slate-400">
                      {format(new Date(trade.createdAt), 'MMM dd, HH:mm')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;