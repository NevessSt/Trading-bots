import React, { useState } from 'react';
import { useLicense } from '../../contexts/LicenseContext';

const LicenseActivation = ({ onActivationSuccess }) => {
  const { activateLicense, validateLicenseKey, loading } = useLicense();
  const [licenseKey, setLicenseKey] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isValidating, setIsValidating] = useState(false);

  const handleValidate = async () => {
    if (!licenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setIsValidating(true);
    setError('');
    setValidationResult(null);

    try {
      const result = await validateLicenseKey(licenseKey.trim());
      setValidationResult(result);
      
      if (!result.valid) {
        setError(result.error || 'Invalid license key');
      }
    } catch (err) {
      setError('Failed to validate license key');
    } finally {
      setIsValidating(false);
    }
  };

  const handleActivate = async () => {
    if (!licenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setError('');
    setSuccess('');

    try {
      const result = await activateLicense(licenseKey.trim());
      
      if (result.success) {
        setSuccess(result.message || 'License activated successfully!');
        setLicenseKey('');
        setValidationResult(null);
        
        // Call success callback if provided
        if (onActivationSuccess) {
          onActivationSuccess();
        }
      } else {
        setError(result.message || 'License activation failed');
      }
    } catch (err) {
      setError('Failed to activate license');
    }
  };

  const handleLicenseKeyChange = (e) => {
    setLicenseKey(e.target.value);
    setValidationResult(null);
    setError('');
    setSuccess('');
  };

  const formatExpirationDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="bg-white shadow-sm rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Activate License
      </h3>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="license-key" className="block text-sm font-medium text-gray-700 mb-2">
            License Key
          </label>
          <textarea
            id="license-key"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
            placeholder="Paste your license key here..."
            value={licenseKey}
            onChange={handleLicenseKeyChange}
            disabled={loading}
          />
        </div>

        {/* Validation Result */}
        {validationResult && validationResult.valid && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-green-800">
                  Valid License Key
                </h4>
                <div className="mt-2 text-sm text-green-700">
                  <p><strong>Type:</strong> {validationResult.licenseData?.type}</p>
                  <p><strong>Expires:</strong> {formatExpirationDate(validationResult.licenseData?.expires)}</p>
                  <div className="mt-2">
                    <p><strong>Features:</strong></p>
                    <ul className="list-disc list-inside ml-4 mt-1">
                      {validationResult.licenseData?.features && Object.entries(validationResult.licenseData.features).map(([key, value]) => (
                        <li key={key} className={value ? 'text-green-700' : 'text-gray-500'}>
                          {key.replace('_', ' ')}: {value ? '✓' : '✗'}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

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
                <h4 className="text-sm font-medium text-red-800">
                  Error
                </h4>
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
                <h4 className="text-sm font-medium text-green-800">
                  Success
                </h4>
                <p className="mt-1 text-sm text-green-700">{success}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={handleValidate}
            disabled={!licenseKey.trim() || isValidating || loading}
            className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isValidating ? 'Validating...' : 'Validate Key'}
          </button>
          
          <button
            onClick={handleActivate}
            disabled={!licenseKey.trim() || loading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Activating...' : 'Activate License'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LicenseActivation;