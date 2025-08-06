import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../stores/tradingStore';
import { FunnelIcon, ArrowDownIcon, ArrowUpIcon } from '@heroicons/react/24/outline';

const TradeHistory = () => {
  const { tradeHistory, loading, error, fetchTradeHistory } = useTradingStore();
  const [filters, setFilters] = useState({
    botId: 'all',
    symbol: 'all',
    type: 'all',
    dateRange: 'all'
  });
  const [sortConfig, setSortConfig] = useState({
    key: 'timestamp',
    direction: 'desc'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [availableBots, setAvailableBots] = useState([]);
  const [availableSymbols, setAvailableSymbols] = useState([]);
  
  useEffect(() => {
    fetchTradeHistory();
  }, [fetchTradeHistory]);
  
  useEffect(() => {
    if (tradeHistory && tradeHistory.length > 0) {
      // Extract unique bot IDs and names
      const bots = [...new Set(tradeHistory.map(trade => trade.bot_id))]
        .map(botId => {
          const trade = tradeHistory.find(t => t.bot_id === botId);
          return {
            id: botId,
            name: trade.bot_name || `Bot ${botId}`
          };
        });
      
      // Extract unique symbols
      const symbols = [...new Set(tradeHistory.map(trade => trade.symbol))];
      
      setAvailableBots(bots);
      setAvailableSymbols(symbols);
    }
  }, [tradeHistory]);
  
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };
  
  const getFilteredTrades = () => {
    if (!tradeHistory) return [];
    
    return tradeHistory.filter(trade => {
      // Filter by bot
      if (filters.botId !== 'all' && trade.bot_id !== filters.botId) {
        return false;
      }
      
      // Filter by symbol
      if (filters.symbol !== 'all' && trade.symbol !== filters.symbol) {
        return false;
      }
      
      // Filter by type
      if (filters.type !== 'all' && trade.type !== filters.type) {
        return false;
      }
      
      // Filter by date range
      if (filters.dateRange !== 'all') {
        const tradeDate = new Date(trade.timestamp);
        const now = new Date();
        
        if (filters.dateRange === 'today') {
          const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          return tradeDate >= today;
        }
        
        if (filters.dateRange === 'week') {
          const weekAgo = new Date(now);
          weekAgo.setDate(now.getDate() - 7);
          return tradeDate >= weekAgo;
        }
        
        if (filters.dateRange === 'month') {
          const monthAgo = new Date(now);
          monthAgo.setMonth(now.getMonth() - 1);
          return tradeDate >= monthAgo;
        }
      }
      
      return true;
    });
  };
  
  const getSortedTrades = () => {
    const filteredTrades = getFilteredTrades();
    
    return [...filteredTrades].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  };
  
  const renderSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return null;
    }
    
    return sortConfig.direction === 'asc' ? (
      <ArrowUpIcon className="h-4 w-4 ml-1" />
    ) : (
      <ArrowDownIcon className="h-4 w-4 ml-1" />
    );
  };
  
  const calculateTotalProfit = () => {
    const filteredTrades = getFilteredTrades();
    if (!filteredTrades.length) return 0;
    
    return filteredTrades.reduce((sum, trade) => sum + parseFloat(trade.profit || 0), 0).toFixed(2);
  };
  
  const calculateWinRate = () => {
    const filteredTrades = getFilteredTrades();
    if (!filteredTrades.length) return 0;
    
    const winningTrades = filteredTrades.filter(trade => parseFloat(trade.profit || 0) > 0).length;
    return ((winningTrades / filteredTrades.length) * 100).toFixed(2);
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
  
  const sortedTrades = getSortedTrades();
  
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Trade History</h1>
        <button 
          onClick={() => setShowFilters(!showFilters)}
          className="btn btn-outline-secondary flex items-center"
        >
          <FunnelIcon className="h-5 w-5 mr-2" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </button>
      </div>
      
      {showFilters && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label htmlFor="botId" className="block text-sm font-medium text-gray-700 mb-1">Bot</label>
              <select
                id="botId"
                name="botId"
                value={filters.botId}
                onChange={handleFilterChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="all">All Bots</option>
                {availableBots.map(bot => (
                  <option key={bot.id} value={bot.id}>{bot.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
              <select
                id="symbol"
                name="symbol"
                value={filters.symbol}
                onChange={handleFilterChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="all">All Symbols</option>
                {availableSymbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                id="type"
                name="type"
                value={filters.type}
                onChange={handleFilterChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="all">All Types</option>
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="dateRange" className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
              <select
                id="dateRange"
                name="dateRange"
                value={filters.dateRange}
                onChange={handleFilterChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">Last 7 Days</option>
                <option value="month">Last 30 Days</option>
              </select>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="text-sm text-gray-500">Total Trades</span>
              <p className="text-lg font-semibold">{sortedTrades.length}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Total Profit</span>
              <p className={`text-lg font-semibold ${parseFloat(calculateTotalProfit()) >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {parseFloat(calculateTotalProfit()) >= 0 ? '+' : ''}{calculateTotalProfit()}%
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Win Rate</span>
              <p className="text-lg font-semibold">{calculateWinRate()}%</p>
            </div>
          </div>
        </div>
        
        {sortedTrades.length === 0 ? (
          <div className="p-6 text-center">
            <p className="text-gray-500">No trades found matching your filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('timestamp')}
                  >
                    <div className="flex items-center">
                      Date/Time
                      {renderSortIcon('timestamp')}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('bot_name')}
                  >
                    <div className="flex items-center">
                      Bot
                      {renderSortIcon('bot_name')}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('type')}
                  >
                    <div className="flex items-center">
                      Type
                      {renderSortIcon('type')}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('symbol')}
                  >
                    <div className="flex items-center">
                      Symbol
                      {renderSortIcon('symbol')}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('price')}
                  >
                    <div className="flex items-center">
                      Price
                      {renderSortIcon('price')}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('amount')}
                  >
                    <div className="flex items-center">
                      Amount
                      {renderSortIcon('amount')}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('profit')}
                  >
                    <div className="flex items-center">
                      Profit/Loss
                      {renderSortIcon('profit')}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedTrades.map((trade) => (
                  <tr key={trade.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.bot_name || `Bot ${trade.bot_id}`}
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
                      ${parseFloat(trade.price).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {parseFloat(trade.amount).toFixed(6)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {trade.profit ? (
                        <span className={parseFloat(trade.profit) >= 0 ? 'text-success-600' : 'text-danger-600'}>
                          {parseFloat(trade.profit) >= 0 ? '+' : ''}{parseFloat(trade.profit).toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradeHistory;