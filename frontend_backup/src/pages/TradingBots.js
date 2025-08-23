import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PlusIcon, PlayIcon, StopIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline';
import { useTradingStore } from '../stores/tradingStore';

const TradingBots = () => {
  const { 
    bots, 
    isLoading, 
    error, 
    fetchBots, 
    startBot, 
    stopBot, 
    deleteBot, 
    setActiveBotId,
    clearError
  } = useTradingStore();
  
  const [isDeleting, setIsDeleting] = useState(false);
  const [botToDelete, setBotToDelete] = useState(null);
  
  useEffect(() => {
    console.log('TradingBots component mounted, fetching bots...');
    fetchBots().catch(err => {
      console.error('Failed to fetch bots in component:', err);
    });
  }, [fetchBots]);

  // Debug logs
  useEffect(() => {
    console.log('Bots state changed:', { bots, isArray: Array.isArray(bots), type: typeof bots });
  }, [bots]);

  const handleStartBot = async (botId) => {
    try {
      await startBot(botId);
    } catch (error) {
      console.error('Failed to start bot:', error);
    }
  };

  const handleStopBot = async (botId) => {
    try {
      await stopBot(botId);
    } catch (error) {
      console.error('Failed to stop bot:', error);
    }
  };

  const confirmDelete = (bot) => {
    setBotToDelete(bot);
    setIsDeleting(true);
  };

  const handleDeleteBot = async () => {
    if (botToDelete) {
      try {
        await deleteBot(botToDelete.id);
        setIsDeleting(false);
        setBotToDelete(null);
      } catch (error) {
        console.error('Failed to delete bot:', error);
      }
    }
  };

  const cancelDelete = () => {
    setIsDeleting(false);
    setBotToDelete(null);
  };

  // Ensure bots is always an array
  const safeBots = Array.isArray(bots) ? bots : [];
  
  console.log('Rendering with safeBots:', safeBots);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trading Bots</h1>
          <p className="text-gray-600">Manage your automated trading strategies</p>
        </div>
        <Link
          to="/bots/create"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
          Create Bot
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  className="bg-red-50 text-red-800 rounded-md p-2 inline-flex items-center text-sm font-medium hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  onClick={() => {
                    clearError();
                    fetchBots();
                  }}
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {safeBots.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No trading bots</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating your first trading bot.</p>
          <div className="mt-6">
            <Link
              to="/bots/create"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
              Create Bot
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {safeBots.map((bot) => (
            <div key={bot.id} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">{bot.name}</h3>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    bot.status === 'running' ? 'bg-green-100 text-green-800' :
                    bot.status === 'stopped' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {bot.status || 'inactive'}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-600">{bot.strategy || 'No strategy'}</p>
                <p className="text-sm text-gray-500">{bot.symbol || 'No symbol'}</p>
                
                <div className="mt-4 flex justify-between items-center">
                  <div className="flex space-x-2">
                    {bot.status === 'running' ? (
                      <button
                        onClick={() => handleStopBot(bot.id)}
                        className="inline-flex items-center p-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        <StopIcon className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStartBot(bot.id)}
                        className="inline-flex items-center p-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        <PlayIcon className="h-4 w-4" />
                      </button>
                    )}
                    
                    <Link
                      to={`/bots/${bot.id}/edit`}
                      className="inline-flex items-center p-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Link>
                  </div>
                  
                  <button
                    onClick={() => confirmDelete(bot)}
                    className="inline-flex items-center p-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleting && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900">Delete Trading Bot</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete "{botToDelete?.name}"? This action cannot be undone.
                </p>
              </div>
              <div className="flex justify-center space-x-4 px-4 py-3">
                <button
                  onClick={cancelDelete}
                  className="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteBot}
                  className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingBots;