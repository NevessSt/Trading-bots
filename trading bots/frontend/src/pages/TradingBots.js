import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PlusIcon, PlayIcon, StopIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline';
import { useTradingStore } from '../stores/tradingStore';

const TradingBots = () => {
  const { 
    bots, 
    loading, 
    error, 
    fetchBots, 
    startBot, 
    stopBot, 
    deleteBot, 
    setActiveBotId 
  } = useTradingStore();
  
  const [isDeleting, setIsDeleting] = useState(false);
  const [botToDelete, setBotToDelete] = useState(null);
  
  useEffect(() => {
    fetchBots();
  }, [fetchBots]);

  const handleStartBot = async (botId) => {
    await startBot(botId);
  };

  const handleStopBot = async (botId) => {
    await stopBot(botId);
  };

  const confirmDelete = (bot) => {
    setBotToDelete(bot);
    setIsDeleting(true);
  };

  const handleDeleteBot = async () => {
    if (botToDelete) {
      await deleteBot(botToDelete.id);
      setIsDeleting(false);
      setBotToDelete(null);
    }
  };

  const cancelDelete = () => {
    setIsDeleting(false);
    setBotToDelete(null);
  };

  const handleEditBot = (botId) => {
    setActiveBotId(botId);
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

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Trading Bots</h1>
        <Link 
          to="/dashboard/bots/new" 
          className="btn btn-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create New Bot
        </Link>
      </div>

      {bots.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-6 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Trading Bots Yet</h3>
          <p className="text-gray-600 mb-4">
            Create your first trading bot to start automated trading.
          </p>
          <Link 
            to="/dashboard/bots/new" 
            className="btn btn-primary inline-flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Create New Bot
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots.map((bot) => (
            <div key={bot.id} className="bg-white shadow rounded-lg overflow-hidden">
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{bot.name}</h3>
                    <p className="text-sm text-gray-500">{bot.symbol}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getBotStatusClass(bot.status)}`}>
                    {bot.status.charAt(0).toUpperCase() + bot.status.slice(1)}
                  </span>
                </div>
                
                <div className="mt-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Strategy:</span>
                    <span className="font-medium">{bot.strategy}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-gray-500">Risk Level:</span>
                    <span className="font-medium">{bot.risk_level}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-gray-500">Profit:</span>
                    <span className={`font-medium ${parseFloat(bot.profit) >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                      {parseFloat(bot.profit) >= 0 ? '+' : ''}{bot.profit}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-gray-500">Created:</span>
                    <span className="font-medium">{new Date(bot.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 px-5 py-3 border-t border-gray-200">
                <div className="flex justify-between">
                  <Link 
                    to={`/dashboard/bots/${bot.id}`}
                    className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                  >
                    View Details
                  </Link>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEditBot(bot.id)}
                      className="text-gray-600 hover:text-gray-900"
                      title="Edit Bot"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    
                    {bot.status === 'running' ? (
                      <button
                        onClick={() => handleStopBot(bot.id)}
                        className="text-danger-600 hover:text-danger-800"
                        title="Stop Bot"
                      >
                        <StopIcon className="h-5 w-5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStartBot(bot.id)}
                        className="text-success-600 hover:text-success-800"
                        title="Start Bot"
                      >
                        <PlayIcon className="h-5 w-5" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => confirmDelete(bot)}
                      className="text-danger-600 hover:text-danger-800"
                      title="Delete Bot"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleting && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Delete Trading Bot</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete the bot "{botToDelete?.name}"? This action cannot be undone.
                </p>
              </div>
              <div className="flex justify-center gap-4 mt-4">
                <button
                  onClick={cancelDelete}
                  className="btn btn-outline-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteBot}
                  className="btn btn-danger"
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