import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useTradingStore } from '../stores/tradingStore';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  ClockIcon,
  CubeIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
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

const Dashboard = () => {
  const { user } = useAuthStore();
  const { 
    bots, 
    tradeHistory, 
    performance, 
    fetchBots, 
    fetchTradeHistory, 
    fetchPerformance 
  } = useTradingStore();
  const [isLoading, setIsLoading] = useState(true);
  
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
  
  // Placeholder data for the chart
  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    datasets: [
      {
        label: 'Portfolio Value',
        data: [10000, 10200, 10150, 10400, 10300, 10600, 10800],
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };
  
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Portfolio Performance',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  };
  
  // Placeholder stats
  const stats = [
    { name: 'Total Profit', value: '$800.00', icon: CurrencyDollarIcon, color: 'bg-success-100 text-success-800' },
    { name: 'Active Bots', value: bots?.length || '0', icon: CubeIcon, color: 'bg-primary-100 text-primary-800' },
    { name: 'Total Trades', value: '42', icon: ClockIcon, color: 'bg-secondary-100 text-secondary-800' },
    { name: 'Win Rate', value: '68%', icon: ChartBarIcon, color: 'bg-warning-100 text-warning-800' },
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
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-6 bg-gray-200 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
          <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
            <div className="p-5">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Welcome back, {user?.name || 'Trader'}!</h1>
        <p className="mt-1 text-sm text-gray-500">
          Here's an overview of your trading performance and activity.
        </p>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className={`flex-shrink-0 rounded-md p-3 ${stat.color}`}>
                  <stat.icon className="h-6 w-6" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                    <dd>
                      <div className="text-lg font-medium text-gray-900">{stat.value}</div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Chart */}
      <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
        <div className="p-5">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Performance Overview</h2>
          <div className="h-64">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>
      </div>
      
      {/* Recent trades */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Recent Trades</h2>
            <Link to="/history" className="text-sm font-medium text-primary-600 hover:text-primary-500">
              View all
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Profit/Loss
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentTrades.map((trade) => (
                <tr key={trade._id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {trade.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${trade.type === 'buy' ? 'bg-success-100 text-success-800' : 'bg-danger-100 text-danger-800'}`}>
                      {trade.type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {trade.amount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${trade.price.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {trade.profit !== null ? (
                      <span className={`inline-flex items-center ${trade.profit >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                        {trade.profit >= 0 ? (
                          <ArrowTrendingUpIcon className="mr-1.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
                        ) : (
                          <ArrowTrendingDownIcon className="mr-1.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
                        )}
                        ${Math.abs(trade.profit).toLocaleString()}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(trade.createdAt).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;