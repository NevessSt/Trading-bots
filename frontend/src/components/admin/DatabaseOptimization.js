import React, { useState, useEffect } from 'react';
import {
  Button,
  Badge,
  Alert,
  Table
} from '../ui';
import { RefreshCw, Database, Zap, BarChart3, Settings } from 'lucide-react';
import api from '../../services/api';

const DatabaseOptimization = () => {
  const [optimizationStatus, setOptimizationStatus] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [cacheStats, setCacheStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('status');

  const fetchOptimizationStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/optimization/status');
      setOptimizationStatus(response.data);
    } catch (err) {
      setError('Failed to fetch optimization status');
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      const response = await api.get('/optimization/performance/queries');
      setPerformanceData(response.data);
    } catch (err) {
      setError('Failed to fetch performance data');
    }
  };

  const applyOptimizations = async () => {
    try {
      setApplying(true);
      await api.post('/optimization/apply');
      await fetchOptimizationStatus();
    } catch (err) {
      setError('Failed to apply optimizations');
    } finally {
      setApplying(false);
    }
  };

  const clearCache = async (pattern = '*') => {
    try {
      setLoading(true);
      await api.post('/optimization/cache/clear', { pattern });
      await fetchOptimizationStatus();
    } catch (err) {
      setError('Failed to clear cache');
    } finally {
      setLoading(false);
    }
  };

  const testPerformance = async () => {
    try {
      setLoading(true);
      const response = await api.post('/optimization/test/performance');
      setPerformanceData(response.data);
    } catch (err) {
      setError('Failed to test performance');
    } finally {
      setLoading(false);
    }
  };

  const fetchCacheStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/optimization/cache/stats');
      setCacheStats(response.data);
    } catch (err) {
      setError('Failed to fetch cache stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOptimizationStatus();
    fetchPerformanceData();
  }, []);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Database Optimization</h2>
          <p className="text-muted-foreground">
            Monitor and optimize database performance
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={fetchOptimizationStatus}
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={applyOptimizations}
            disabled={applying}
            size="sm"
          >
            <Zap className="h-4 w-4 mr-2" />
            {applying ? 'Applying...' : 'Apply Optimizations'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert className="bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200">
          <div className="text-sm">{error}</div>
        </Alert>
      )}

      <div className="space-y-4">
        {/* Navigation Tabs */}
        <div className="border-b border-slate-200 dark:border-slate-700">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'status', label: 'Status' },
              { id: 'performance', label: 'Performance' },
              { id: 'cache', label: 'Cache' },
              { id: 'tables', label: 'Tables' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {activeTab === 'status' && (
          <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                <h3 className="text-sm font-medium">Database Indexes</h3>
                <Database className="h-4 w-4 text-slate-500" />
              </div>
              <div className="text-2xl font-bold">
                {optimizationStatus?.indexes_count || 0}
              </div>
              <p className="text-xs text-slate-500">
                Optimization indexes created
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                <h3 className="text-sm font-medium">Redis Connection</h3>
                <Zap className="h-4 w-4 text-slate-500" />
              </div>
              <div className="flex items-center space-x-2">
                <Badge 
                  className={optimizationStatus?.redis_connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
                >
                  {optimizationStatus?.redis_connected ? 'Connected' : 'Disconnected'}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Cache system status
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                <h3 className="text-sm font-medium">Cache Hit Rate</h3>
                <BarChart3 className="h-4 w-4 text-slate-500" />
              </div>
              <div className="text-2xl font-bold">
                {optimizationStatus?.cache_stats?.hit_rate || '0'}%
              </div>
              <p className="text-xs text-slate-500">
                Cache efficiency
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                <h3 className="text-sm font-medium">Memory Usage</h3>
                <Settings className="h-4 w-4 text-slate-500" />
              </div>
              <div className="text-2xl font-bold">
                {optimizationStatus?.cache_stats?.memory_usage || '0'} MB
              </div>
              <p className="text-xs text-slate-500">
                Cache memory consumption
              </p>
            </div>
          </div>

          {optimizationStatus?.cache_stats && (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <h3 className="text-lg font-semibold mb-4">Cache Statistics</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-sm font-medium">Connected Clients</p>
                  <p className="text-2xl font-bold">{optimizationStatus.cache_stats.connected_clients}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Keyspace Hits</p>
                  <p className="text-2xl font-bold">{optimizationStatus.cache_stats.keyspace_hits}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Keyspace Misses</p>
                  <p className="text-2xl font-bold">{optimizationStatus.cache_stats.keyspace_misses}</p>
                </div>
              </div>
            </div>
          )}
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="space-y-4">
          <div className="flex space-x-2 mb-4">
            <Button
              onClick={() => testPerformance('user_trades')}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              Test User Trades Query
            </Button>
            <Button
              onClick={() => testPerformance('user_stats')}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              Test User Stats Query
            </Button>
          </div>

          {performanceData?.slow_queries && performanceData.slow_queries.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <h3 className="text-lg font-semibold mb-4">Slow Queries</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                  <thead className="bg-slate-50 dark:bg-slate-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Query</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Calls</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Mean Time (ms)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Total Time (ms)</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                    {performanceData.slow_queries.map((query, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-900 dark:text-slate-100">{query.query}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">{query.calls}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">{query.mean_time}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">{query.total_time}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          </div>
        )}

        {activeTab === 'cache' && (
          <div className="space-y-4">
          <div className="flex space-x-2 mb-4">
            <Button
              onClick={() => clearCache('*')}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              Clear All Cache
            </Button>
            <Button
              onClick={() => clearCache('user_*')}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              Clear User Cache
            </Button>
            <Button
              onClick={() => clearCache('bot_*')}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              Clear Bot Cache
            </Button>
          </div>

          <Alert className="bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200">
            <div className="text-sm">
              Cache operations help improve query performance by storing frequently accessed data in memory.
              {!optimizationStatus?.redis_connected && ' Redis is currently not connected.'}
            </div>
          </Alert>
          </div>
        )}

        {activeTab === 'tables' && (
          <div className="space-y-4">
          {optimizationStatus?.table_sizes && (
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <h3 className="text-lg font-semibold mb-4">Table Sizes</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                  <thead className="bg-slate-50 dark:bg-slate-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Table</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider">Size</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                    {Object.entries(optimizationStatus.table_sizes).map(([table, size]) => (
                      <tr key={table}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-slate-100">{table}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">{size}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DatabaseOptimization;