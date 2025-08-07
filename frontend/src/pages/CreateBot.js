import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useTradingStore } from '../stores/tradingStore';

const CreateBot = () => {
  const navigate = useNavigate();
  const { 
    availableSymbols, 
    availableStrategies, 
    loading, 
    error, 
    fetchAvailableSymbols, 
    fetchAvailableStrategies,
    createBot,
    backtest
  } = useTradingStore();
  
  const [formData, setFormData] = useState({
    name: '',
    strategy: '',
    symbol: '',
    risk_level: 'medium',
    parameters: {}
  });
  
  const [backtestResults, setBacktestResults] = useState(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [step, setStep] = useState(1);
  const [errors, setErrors] = useState({});
  
  useEffect(() => {
    fetchAvailableSymbols();
    fetchAvailableStrategies();
  }, [fetchAvailableSymbols, fetchAvailableStrategies]);
  
  useEffect(() => {
    // Set default parameters when strategy changes
    if (formData.strategy && availableStrategies) {
      const selectedStrategy = availableStrategies.find(s => s.name === formData.strategy);
      if (selectedStrategy && selectedStrategy.default_parameters) {
        setFormData(prev => ({
          ...prev,
          parameters: { ...selectedStrategy.default_parameters }
        }));
      }
    }
  }, [formData.strategy, availableStrategies]);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear errors when input changes
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };
  
  const handleParameterChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [name]: parseFloat(value) || value
      }
    }));
  };
  
  const validateStep1 = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Bot name is required';
    }
    
    if (!formData.strategy) {
      newErrors.strategy = 'Please select a strategy';
    }
    
    if (!formData.symbol) {
      newErrors.symbol = 'Please select a trading pair';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleNextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };
  
  const handlePrevStep = () => {
    if (step === 2) {
      setStep(1);
    }
  };
  
  const handleBacktest = async () => {
    setIsBacktesting(true);
    try {
      const results = await backtest({
        strategy: formData.strategy,
        symbol: formData.symbol,
        parameters: formData.parameters,
        risk_level: formData.risk_level
      });
      setBacktestResults(results);
    } catch (err) {
      console.error('Backtest error:', err);
    } finally {
      setIsBacktesting(false);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await createBot(formData);
      navigate('/dashboard/bots');
    } catch (err) {
      console.error('Error creating bot:', err);
    }
  };
  
  const getStrategyParameters = () => {
    if (!formData.strategy || !availableStrategies) return null;
    
    const selectedStrategy = availableStrategies.find(s => s.name === formData.strategy);
    if (!selectedStrategy || !selectedStrategy.parameters) return null;
    
    return selectedStrategy.parameters;
  };
  
  if (loading && !availableStrategies && !availableSymbols) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
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
        <h1 className="text-2xl font-semibold text-gray-900">Create New Trading Bot</h1>
      </div>
      
      <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
        <div className="p-6">
          <div className="mb-8">
            <div className="flex items-center">
              <div className="flex items-center relative">
                <div className={`rounded-full h-10 w-10 flex items-center justify-center ${step >= 1 ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-600'}`}>
                  1
                </div>
                <div className="absolute top-0 -ml-10 text-center mt-14 w-32 text-xs font-medium">
                  Basic Settings
                </div>
              </div>
              <div className={`flex-1 border-t-2 ${step >= 2 ? 'border-primary-500' : 'border-gray-200'}`}></div>
              <div className="flex items-center relative">
                <div className={`rounded-full h-10 w-10 flex items-center justify-center ${step >= 2 ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-600'}`}>
                  2
                </div>
                <div className="absolute top-0 -ml-10 text-center mt-14 w-32 text-xs font-medium">
                  Strategy Parameters
                </div>
              </div>
            </div>
          </div>
          
          <form onSubmit={handleSubmit}>
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">Bot Name</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${errors.name ? 'border-danger-500' : 'border-gray-300'}`}
                    placeholder="My Trading Bot"
                  />
                  {errors.name && <p className="mt-1 text-sm text-danger-600">{errors.name}</p>}
                </div>
                
                <div>
                  <label htmlFor="strategy" className="block text-sm font-medium text-gray-700">Trading Strategy</label>
                  <select
                    id="strategy"
                    name="strategy"
                    value={formData.strategy}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${errors.strategy ? 'border-danger-500' : 'border-gray-300'}`}
                  >
                    <option value="">Select a strategy</option>
                    {availableStrategies && availableStrategies.map((strategy) => (
                      <option key={strategy.name} value={strategy.name}>{strategy.name}</option>
                    ))}
                  </select>
                  {errors.strategy && <p className="mt-1 text-sm text-danger-600">{errors.strategy}</p>}
                  {formData.strategy && availableStrategies && (
                    <p className="mt-1 text-sm text-gray-500">
                      {availableStrategies.find(s => s.name === formData.strategy)?.description}
                    </p>
                  )}
                </div>
                
                <div>
                  <label htmlFor="symbol" className="block text-sm font-medium text-gray-700">Trading Pair</label>
                  <select
                    id="symbol"
                    name="symbol"
                    value={formData.symbol}
                    onChange={handleInputChange}
                    className={`mt-1 block w-full rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 ${errors.symbol ? 'border-danger-500' : 'border-gray-300'}`}
                  >
                    <option value="">Select a trading pair</option>
                    {availableSymbols && availableSymbols.map((symbol) => (
                      <option key={symbol} value={symbol}>{symbol}</option>
                    ))}
                  </select>
                  {errors.symbol && <p className="mt-1 text-sm text-danger-600">{errors.symbol}</p>}
                </div>
                
                <div>
                  <label htmlFor="risk_level" className="block text-sm font-medium text-gray-700">Risk Level</label>
                  <select
                    id="risk_level"
                    name="risk_level"
                    value={formData.risk_level}
                    onChange={handleInputChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                  </select>
                  <p className="mt-1 text-sm text-gray-500">
                    {formData.risk_level === 'low' && 'Conservative approach with smaller position sizes and tighter stop losses.'}
                    {formData.risk_level === 'medium' && 'Balanced approach with moderate position sizes and stop losses.'}
                    {formData.risk_level === 'high' && 'Aggressive approach with larger position sizes and wider stop losses.'}
                  </p>
                </div>
                
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleNextStep}
                    className="btn btn-primary"
                  >
                    Next: Strategy Parameters
                  </button>
                </div>
              </div>
            )}
            
            {step === 2 && (
              <div>
                <div className="space-y-6 mb-8">
                  <h3 className="text-lg font-medium text-gray-900">Strategy Parameters</h3>
                  <p className="text-sm text-gray-500">
                    Customize the parameters for your selected strategy. The default values are recommended for beginners.
                  </p>
                  
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
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="1"
                        />
                        <p className="mt-1 text-sm text-gray-500">Number of periods used to calculate RSI</p>
                      </div>
                      <div>
                        <label htmlFor="overbought" className="block text-sm font-medium text-gray-700">Overbought Level</label>
                        <input
                          type="number"
                          id="overbought"
                          name="overbought"
                          value={formData.parameters.overbought || 70}
                          onChange={handleParameterChange}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="50"
                          max="100"
                        />
                        <p className="mt-1 text-sm text-gray-500">Level above which the market is considered overbought</p>
                      </div>
                      <div>
                        <label htmlFor="oversold" className="block text-sm font-medium text-gray-700">Oversold Level</label>
                        <input
                          type="number"
                          id="oversold"
                          name="oversold"
                          value={formData.parameters.oversold || 30}
                          onChange={handleParameterChange}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="0"
                          max="50"
                        />
                        <p className="mt-1 text-sm text-gray-500">Level below which the market is considered oversold</p>
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
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="1"
                        />
                        <p className="mt-1 text-sm text-gray-500">Number of periods for the fast EMA</p>
                      </div>
                      <div>
                        <label htmlFor="slow_period" className="block text-sm font-medium text-gray-700">Slow Period</label>
                        <input
                          type="number"
                          id="slow_period"
                          name="slow_period"
                          value={formData.parameters.slow_period || 26}
                          onChange={handleParameterChange}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="1"
                        />
                        <p className="mt-1 text-sm text-gray-500">Number of periods for the slow EMA</p>
                      </div>
                      <div>
                        <label htmlFor="signal_period" className="block text-sm font-medium text-gray-700">Signal Period</label>
                        <input
                          type="number"
                          id="signal_period"
                          name="signal_period"
                          value={formData.parameters.signal_period || 9}
                          onChange={handleParameterChange}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="1"
                        />
                        <p className="mt-1 text-sm text-gray-500">Number of periods for the signal line</p>
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
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="1"
                        />
                        <p className="mt-1 text-sm text-gray-500">Number of periods for the fast EMA</p>
                      </div>
                      <div>
                        <label htmlFor="slow_ema" className="block text-sm font-medium text-gray-700">Slow EMA Period</label>
                        <input
                          type="number"
                          id="slow_ema"
                          name="slow_ema"
                          value={formData.parameters.slow_ema || 21}
                          onChange={handleParameterChange}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          min="1"
                        />
                        <p className="mt-1 text-sm text-gray-500">Number of periods for the slow EMA</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Backtest Results */}
                {backtestResults && (
                  <div className="mb-8 p-4 bg-gray-50 rounded-lg">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">Backtest Results</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-3 bg-white rounded shadow">
                        <p className="text-sm text-gray-500">Total Profit</p>
                        <p className={`text-xl font-semibold ${backtestResults.total_profit >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                          {backtestResults.total_profit >= 0 ? '+' : ''}{backtestResults.total_profit}%
                        </p>
                      </div>
                      <div className="p-3 bg-white rounded shadow">
                        <p className="text-sm text-gray-500">Win Rate</p>
                        <p className="text-xl font-semibold">{backtestResults.win_rate}%</p>
                      </div>
                      <div className="p-3 bg-white rounded shadow">
                        <p className="text-sm text-gray-500">Total Trades</p>
                        <p className="text-xl font-semibold">{backtestResults.total_trades}</p>
                      </div>
                    </div>
                    <div className="mt-3 text-sm text-gray-500">
                      <p>Backtest period: {backtestResults.period}</p>
                      <p className="mt-1">Note: Past performance is not indicative of future results.</p>
                    </div>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <button
                    type="button"
                    onClick={handlePrevStep}
                    className="btn btn-outline-secondary"
                  >
                    Back
                  </button>
                  
                  <div className="space-x-3">
                    <button
                      type="button"
                      onClick={handleBacktest}
                      disabled={isBacktesting}
                      className="btn btn-outline-primary"
                    >
                      {isBacktesting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-primary-500 mr-2"></div>
                          Running Backtest...
                        </>
                      ) : 'Run Backtest'}
                    </button>
                    
                    <button
                      type="submit"
                      className="btn btn-primary"
                    >
                      Create Bot
                    </button>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateBot;