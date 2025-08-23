import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../stores/tradingStore';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Performance = () => {
  const { performance, loading, error, fetchPerformance } = useTradingStore();
  const [timeRange, setTimeRange] = useState('month');
  const [selectedBot, setSelectedBot] = useState('all');
  const [availableBots, setAvailableBots] = useState([]);
  
  useEffect(() => {
    fetchPerformance();
  }, [fetchPerformance]);
  
  useEffect(() => {
    if (performance && performance.bots && typeof performance.bots === 'object') {
      setAvailableBots(Object.keys(performance.bots).map(botId => ({
        id: botId,
        name: performance.bots[botId]?.name || `Bot ${botId}`
      })));
    } else {
      // If no bots data structure, clear available bots
      setAvailableBots([]);
    }
  }, [performance]);
  
  const handleTimeRangeChange = (e) => {
    setTimeRange(e.target.value);
  };
  
  const handleBotChange = (e) => {
    setSelectedBot(e.target.value);
  };
  
  const getFilteredData = () => {
    if (!performance) return null;
    
    let data;
    if (selectedBot === 'all') {
      data = performance.overall || [];
    } else {
      data = performance.bots?.[selectedBot]?.data || [];
    }
    
    // Ensure data is an array before filtering
    if (!Array.isArray(data)) {
      return [];
    }
    
    // Apply time range filter
    const now = new Date();
    let startDate;
    
    switch (timeRange) {
      case 'week':
        startDate = new Date(now);
        startDate.setDate(now.getDate() - 7);
        break;
      case 'month':
        startDate = new Date(now);
        startDate.setMonth(now.getMonth() - 1);
        break;
      case 'quarter':
        startDate = new Date(now);
        startDate.setMonth(now.getMonth() - 3);
        break;
      case 'year':
        startDate = new Date(now);
        startDate.setFullYear(now.getFullYear() - 1);
        break;
      default:
        startDate = new Date(0); // All time
    }
    
    return data.filter(item => item.timestamp && new Date(item.timestamp) >= startDate);
  };
  
  const getProfitChartData = () => {
    const filteredData = getFilteredData();
    if (!filteredData || filteredData.length === 0) {
      return {
        labels: [],
        datasets: [{
          label: 'Profit',
          data: [],
          borderColor: '#4F46E5',
          backgroundColor: 'rgba(79, 70, 229, 0.1)',
          fill: true,
          tension: 0.1
        }]
      };
    }
    
    return {
      labels: filteredData.map(item => new Date(item.timestamp).toLocaleDateString()),
      datasets: [{
        label: 'Profit (%)',
        data: filteredData.map(item => item.profit_percentage),
        borderColor: '#4F46E5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        fill: true,
        tension: 0.1
      }]
    };
  };
  
  const getTradeCountChartData = () => {
    const filteredData = getFilteredData();
    if (!filteredData || filteredData.length === 0) {
      return {
        labels: [],
        datasets: [
          {
            label: 'Buy Trades',
            data: [],
            backgroundColor: 'rgba(52, 211, 153, 0.8)',
          },
          {
            label: 'Sell Trades',
            data: [],
            backgroundColor: 'rgba(239, 68, 68, 0.8)',
          }
        ]
      };
    }
    
    // Group by date and count buy/sell trades
    const tradesByDate = filteredData.reduce((acc, item) => {
      const date = new Date(item.timestamp).toLocaleDateString();
      if (!acc[date]) {
        acc[date] = { buy: 0, sell: 0 };
      }
      acc[date].buy += item.buy_count || 0;
      acc[date].sell += item.sell_count || 0;
      return acc;
    }, {});
    
    const dates = Object.keys(tradesByDate);
    
    return {
      labels: dates,
      datasets: [
        {
          label: 'Buy Trades',
          data: dates.map(date => tradesByDate[date].buy),
          backgroundColor: 'rgba(52, 211, 153, 0.8)',
        },
        {
          label: 'Sell Trades',
          data: dates.map(date => tradesByDate[date].sell),
          backgroundColor: 'rgba(239, 68, 68, 0.8)',
        }
      ]
    };
  };
  
  const getWinLossChartData = () => {
    const filteredData = getFilteredData();
    if (!filteredData || filteredData.length === 0) {
      return {
        labels: ['Winning Trades', 'Losing Trades'],
        datasets: [{
          data: [0, 0],
          backgroundColor: ['rgba(52, 211, 153, 0.8)', 'rgba(239, 68, 68, 0.8)'],
          borderColor: ['rgb(52, 211, 153)', 'rgb(239, 68, 68)'],
          borderWidth: 1,
        }]
      };
    }
    
    // Sum up winning and losing trades
    const winLossData = filteredData.reduce((acc, item) => {
      acc.win += item.winning_trades || 0;
      acc.loss += item.losing_trades || 0;
      return acc;
    }, { win: 0, loss: 0 });
    
    return {
      labels: ['Winning Trades', 'Losing Trades'],
      datasets: [{
        data: [winLossData.win, winLossData.loss],
        backgroundColor: ['rgba(52, 211, 153, 0.8)', 'rgba(239, 68, 68, 0.8)'],
        borderColor: ['rgb(52, 211, 153)', 'rgb(239, 68, 68)'],
        borderWidth: 1,
      }]
    };
  };
  
  const calculateSummaryStats = () => {
    const filteredData = getFilteredData();
    if (!filteredData || filteredData.length === 0) {
      return {
        totalProfit: 0,
        totalTrades: 0,
        winRate: 0,
        avgProfit: 0,
        bestTrade: 0,
        worstTrade: 0
      };
    }
    
    // Calculate summary statistics
    const totalProfit = filteredData.reduce((sum, item) => sum + (item.profit_amount || 0), 0);
    const totalTrades = filteredData.reduce((sum, item) => sum + ((item.buy_count || 0) + (item.sell_count || 0)), 0);
    const winningTrades = filteredData.reduce((sum, item) => sum + (item.winning_trades || 0), 0);
    const losingTrades = filteredData.reduce((sum, item) => sum + (item.losing_trades || 0), 0);
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
    const avgProfit = totalTrades > 0 ? totalProfit / totalTrades : 0;
    
    // Find best and worst trades
    const bestTrade = Math.max(...filteredData.map(item => item.best_trade || 0));
    const worstTrade = Math.min(...filteredData.map(item => item.worst_trade || 0));
    
    return {
      totalProfit,
      totalTrades,
      winRate,
      avgProfit,
      bestTrade,
      worstTrade
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
  
  const summaryStats = calculateSummaryStats();
  
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Performance Analytics</h1>
        <div className="flex space-x-4">
          <div>
            <select
              value={selectedBot}
              onChange={handleBotChange}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">All Bots</option>
              {availableBots.map(bot => (
                <option key={bot.id} value={bot.id}>{bot.name}</option>
              ))}
            </select>
          </div>
          <div>
            <select
              value={timeRange}
              onChange={handleTimeRangeChange}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
              <option value="quarter">Last 3 Months</option>
              <option value="year">Last Year</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Profit</h3>
          <p className={`text-3xl font-bold ${summaryStats.totalProfit >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {summaryStats.totalProfit >= 0 ? '+' : ''}{summaryStats.totalProfit.toFixed(2)}%
          </p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Win Rate</h3>
          <p className="text-3xl font-bold text-primary-600">
            {summaryStats.winRate.toFixed(2)}%
          </p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Trades</h3>
          <p className="text-3xl font-bold text-gray-800">
            {summaryStats.totalTrades}
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Profit Over Time</h3>
          <div className="h-80">
            <Line 
              data={getProfitChartData()} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        return `Profit: ${context.raw}%`;
                      }
                    }
                  }
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
        
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Trade Count</h3>
          <div className="h-80">
            <Bar 
              data={getTradeCountChartData()} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      precision: 0
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Win/Loss Ratio</h3>
          <div className="h-64">
            <Doughnut 
              data={getWinLossChartData()} 
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                  }
                }
              }}
            />
          </div>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6 col-span-1 lg:col-span-2">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-500 mb-1">Average Profit/Trade</h4>
              <p className={`text-xl font-semibold ${summaryStats.avgProfit >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {summaryStats.avgProfit >= 0 ? '+' : ''}{summaryStats.avgProfit.toFixed(2)}%
              </p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-500 mb-1">Best Trade</h4>
              <p className="text-xl font-semibold text-success-600">
                +{summaryStats.bestTrade.toFixed(2)}%
              </p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-500 mb-1">Worst Trade</h4>
              <p className="text-xl font-semibold text-danger-600">
                {summaryStats.worstTrade.toFixed(2)}%
              </p>
            </div>
          </div>
          
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Performance Tips</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                {summaryStats.winRate < 50 ? 
                  "Consider adjusting your strategy parameters to improve win rate." : 
                  "Your win rate is good! Focus on optimizing position sizing for better returns."}
              </li>
              <li className="flex items-start">
                <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                {summaryStats.avgProfit < 0 ? 
                  "Review your exit strategy to cut losses earlier and let profits run longer." : 
                  "Your average profit per trade is positive. Consider increasing position sizes."}
              </li>
              <li className="flex items-start">
                <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 text-primary-600 mr-2">•</span>
                "Regularly backtest your strategies to adapt to changing market conditions."
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Performance;