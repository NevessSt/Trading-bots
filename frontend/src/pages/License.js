import React, { useState, useEffect } from 'react';
import { useLicense } from '../contexts/LicenseContext';
import LicenseActivation from '../components/License/LicenseActivation';
import LicenseGenerator from '../components/License/LicenseGenerator';

const License = () => {
  const {
    licenseInfo,
    loading,
    error,
    checkLicenseStatus,
    deactivateLicense,
    hasValidLicense,
    getDaysUntilExpiration,
    isLicenseExpired
  } = useLicense();
  
  const [showActivation, setShowActivation] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [activeTab, setActiveTab] = useState('status');

  useEffect(() => {
    checkLicenseStatus();
  }, []);

  const handleDeactivate = async () => {
    if (!window.confirm('Are you sure you want to deactivate your license? This will revert your account to the free plan.')) {
      return;
    }

    setDeactivating(true);
    try {
      await deactivateLicense();
    } catch (err) {
      console.error('Deactivation error:', err);
    } finally {
      setDeactivating(false);
    }
  };

  const handleActivationSuccess = () => {
    setShowActivation(false);
    checkLicenseStatus();
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getLicenseStatusColor = () => {
    if (!hasValidLicense()) return 'text-gray-600';
    if (isLicenseExpired()) return 'text-red-600';
    
    const daysLeft = getDaysUntilExpiration();
    if (daysLeft <= 7) return 'text-orange-600';
    if (daysLeft <= 30) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getLicenseStatusBadge = () => {
    if (!hasValidLicense()) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Free</span>;
    }
    if (isLicenseExpired()) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Expired</span>;
    }
    
    const daysLeft = getDaysUntilExpiration();
    if (daysLeft <= 7) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Expires Soon</span>;
    }
    if (daysLeft <= 30) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Expires Soon</span>;
    }
    
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">License Management</h1>
          <p className="mt-2 text-gray-600">
            Manage your trading bot license and view available features.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('status')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'status'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 License Status
            </button>
            <button
              onClick={() => setActiveTab('generator')}
              className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'generator'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔑 Generate License
            </button>
          </nav>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'status' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current License Status */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Current License</h2>
              {getLicenseStatusBadge()}
            </div>
            
            <div className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">License Type</dt>
                <dd className={`mt-1 text-lg font-semibold ${getLicenseStatusColor()}`}>
                  {licenseInfo.type?.charAt(0).toUpperCase() + licenseInfo.type?.slice(1) || 'Free'}
                </dd>
              </div>
              
              {licenseInfo.activated && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Activated</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {formatDate(licenseInfo.activated)}
                  </dd>
                </div>
              )}
              
              {licenseInfo.expires && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Expires</dt>
                  <dd className={`mt-1 text-sm ${getLicenseStatusColor()}`}>
                    {formatDate(licenseInfo.expires)}
                    {getDaysUntilExpiration() !== null && (
                      <span className="ml-2 text-xs">
                        ({getDaysUntilExpiration()} days remaining)
                      </span>
                    )}
                  </dd>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex space-x-3">
              {!hasValidLicense() ? (
                <button
                  onClick={() => setShowActivation(!showActivation)}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  {showActivation ? 'Hide Activation' : 'Activate License'}
                </button>
              ) : (
                <button
                  onClick={handleDeactivate}
                  disabled={deactivating}
                  className="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deactivating ? 'Deactivating...' : 'Deactivate License'}
                </button>
              )}
              
              <button
                onClick={checkLicenseStatus}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Refresh
              </button>
            </div>
          </div>

          {/* License Features */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Features</h2>
            
            <div className="space-y-3">
              {licenseInfo.features && Object.entries(licenseInfo.features).map(([feature, enabled]) => (
                <div key={feature} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">
                    {feature.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    enabled 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {enabled ? '✓ Enabled' : '✗ Disabled'}
                  </span>
                </div>
              ))}
              
              {licenseInfo.features?.max_bots && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Maximum Bots</span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {licenseInfo.features.max_bots === -1 ? 'Unlimited' : licenseInfo.features.max_bots}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
        )}

        {activeTab === 'generator' && (
          <div className="space-y-6">
            <LicenseGenerator />
          </div>
        )}

        {/* License Activation */}
        {showActivation && activeTab === 'status' && (
          <div className="mt-6">
            <LicenseActivation onActivationSuccess={handleActivationSuccess} />
          </div>
        )}

        {/* License Plans Information */}
        {activeTab === 'status' && (
        <div className="mt-8 bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Available License Plans</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Free Plan */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Free</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 1 Trading Bot</li>
                <li>• Paper Trading Only</li>
                <li>• Basic Strategies</li>
                <li>• Community Support</li>
              </ul>
            </div>
            
            {/* Premium Plan */}
            <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
              <h3 className="text-lg font-medium text-blue-900 mb-2">Premium</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Up to 10 Trading Bots</li>
                <li>• Live Trading</li>
                <li>• Advanced Strategies</li>
                <li>• API Access</li>
                <li>• Priority Support</li>
                <li>• Custom Indicators</li>
              </ul>
            </div>
            
            {/* Enterprise Plan */}
            <div className="border border-purple-200 rounded-lg p-4 bg-purple-50">
              <h3 className="text-lg font-medium text-purple-900 mb-2">Enterprise</h3>
              <ul className="text-sm text-purple-700 space-y-1">
                <li>• Unlimited Trading Bots</li>
                <li>• Live Trading</li>
                <li>• Advanced Strategies</li>
                <li>• Full API Access</li>
                <li>• Priority Support</li>
                <li>• Custom Indicators</li>
                <li>• White-label Options</li>
              </ul>
            </div>
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

export default License;