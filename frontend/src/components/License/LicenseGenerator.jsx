import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const LicenseGenerator = () => {
  const { isAuthenticated } = useAuth();
  const [licenseTypes, setLicenseTypes] = useState({});
  const [formData, setFormData] = useState({
    license_type: 'premium',
    duration_days: 365,
    user_email: ''
  });
  const [generatedLicense, setGeneratedLicense] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loadingTypes, setLoadingTypes] = useState(true);

  // Load available license types
  useEffect(() => {
    const fetchLicenseTypes = async () => {
      try {
        setLoadingTypes(true);
        const response = await axios.get('/api/license/types');
        setLicenseTypes(response.data.license_types || {});
      } catch (err) {
        console.error('Failed to load license types:', err);
        setError('Failed to load license types');
      } finally {
        setLoadingTypes(false);
      }
    };

    fetchLicenseTypes();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear messages when user starts typing
    if (error) setError('');
    if (success) setSuccess('');
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      setError('You must be logged in to generate licenses. Please log in first.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    setGeneratedLicense(null);

    try {
      const response = await axios.post('/api/license/generate', formData);

      if (response.data.success) {
        setGeneratedLicense(response.data);
        setSuccess('License generated successfully!');
        
        // Reset form
        setFormData({
          license_type: 'premium',
          duration_days: 365,
          user_email: ''
        });
      } else {
        setError('Failed to generate license');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'License generation failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setSuccess('License key copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy:', err);
      setError('Failed to copy to clipboard');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loadingTypes) {
    return (
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          🔑 License Generator
        </h3>
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Authentication Required
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>You must be logged in to generate license keys. Please log in to your account first.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-sm rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        🔑 License Generator
      </h3>
      <p className="text-sm text-gray-600 mb-6">
        Generate new license keys for different plans and durations.
      </p>

      <form onSubmit={handleGenerate} className="space-y-6">
        {/* License Type Selection */}
        <div>
          <label htmlFor="license_type" className="block text-sm font-medium text-gray-700 mb-2">
            License Type
          </label>
          <select
            id="license_type"
            name="license_type"
            value={formData.license_type}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          >
            {Object.entries(licenseTypes).map(([type, details]) => (
              <option key={type} value={type}>
                {details.name} - {details.description}
              </option>
            ))}
          </select>
        </div>

        {/* Selected License Features */}
        {formData.license_type && licenseTypes[formData.license_type] && (
          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              {licenseTypes[formData.license_type].name} Features:
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(licenseTypes[formData.license_type].features).map(([feature, value]) => (
                <div key={feature} className="flex items-center justify-between">
                  <span className="text-gray-600">
                    {feature.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className={`font-medium ${
                    typeof value === 'boolean' 
                      ? (value ? 'text-green-600' : 'text-red-600')
                      : 'text-blue-600'
                  }`}>
                    {typeof value === 'boolean' ? (value ? '✓' : '✗') : value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Duration */}
        <div>
          <label htmlFor="duration_days" className="block text-sm font-medium text-gray-700 mb-2">
            Duration (Days)
          </label>
          <select
            id="duration_days"
            name="duration_days"
            value={formData.duration_days}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          >
            <option value={30}>30 Days (1 Month)</option>
            <option value={90}>90 Days (3 Months)</option>
            <option value={180}>180 Days (6 Months)</option>
            <option value={365}>365 Days (1 Year)</option>
            <option value={730}>730 Days (2 Years)</option>
            <option value={1095}>1095 Days (3 Years)</option>
          </select>
        </div>

        {/* User Email */}
        <div>
          <label htmlFor="user_email" className="block text-sm font-medium text-gray-700 mb-2">
            User Email (Optional)
          </label>
          <input
            type="email"
            id="user_email"
            name="user_email"
            value={formData.user_email}
            onChange={handleInputChange}
            placeholder="user@example.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Optional: Associate this license with a specific user email
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800">Error</h4>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-green-800">Success</h4>
                <p className="mt-1 text-sm text-green-700">{success}</p>
              </div>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </div>
            ) : (
              '🔑 Generate License Key'
            )}
          </button>
        </div>
      </form>

      {/* Generated License Display */}
      {generatedLicense && (
        <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="text-lg font-medium text-green-900 mb-4">
            ✅ License Generated Successfully!
          </h4>
          
          {/* License Details */}
          <div className="bg-white border border-green-200 rounded-md p-4 mb-4">
            <h5 className="text-sm font-medium text-gray-900 mb-3">License Details:</h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="font-medium text-gray-700">Type:</span>
                <span className="ml-2 text-gray-900">{generatedLicense.license_data.type.toUpperCase()}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Duration:</span>
                <span className="ml-2 text-gray-900">{generatedLicense.license_data.duration_days} days</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Created:</span>
                <span className="ml-2 text-gray-900">{formatDate(generatedLicense.license_data.created)}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Expires:</span>
                <span className="ml-2 text-gray-900">{formatDate(generatedLicense.license_data.expires)}</span>
              </div>
              {generatedLicense.license_data.user_email && (
                <div className="md:col-span-2">
                  <span className="font-medium text-gray-700">User Email:</span>
                  <span className="ml-2 text-gray-900">{generatedLicense.license_data.user_email}</span>
                </div>
              )}
            </div>
          </div>

          {/* License Key */}
          <div className="bg-gray-900 rounded-md p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-white">License Key:</h5>
              <button
                onClick={() => copyToClipboard(generatedLicense.license_key)}
                className="text-xs bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                📋 Copy
              </button>
            </div>
            <div className="bg-gray-800 rounded p-3 font-mono text-xs text-green-400 break-all">
              {generatedLicense.license_key}
            </div>
          </div>

          {/* Usage Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h5 className="text-sm font-medium text-blue-900 mb-2">📋 Usage Instructions:</h5>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Copy the license key above</li>
              <li>Go to the License Activation section</li>
              <li>Paste the key and click "Activate License"</li>
              <li>Or share this key with the intended user</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
};

export default LicenseGenerator;