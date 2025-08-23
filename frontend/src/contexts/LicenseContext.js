import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import axios from 'axios';

const LicenseContext = createContext();

export const useLicense = () => {
  const context = useContext(LicenseContext);
  if (!context) {
    throw new Error('useLicense must be used within a LicenseProvider');
  }
  return context;
};

export const LicenseProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [licenseInfo, setLicenseInfo] = useState({
    type: 'free',
    active: false,
    expires: null,
    activated: null,
    features: {
      max_bots: 1,
      live_trading: false,
      advanced_strategies: false,
      api_access: false,
      priority_support: false,
      custom_indicators: false
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Check license status
  const checkLicenseStatus = async () => {
    if (!isAuthenticated) {
      setLicenseInfo({
        type: 'free',
        active: false,
        expires: null,
        activated: null,
        features: {
          max_bots: 1,
          live_trading: false,
          advanced_strategies: false,
          api_access: false,
          priority_support: false,
          custom_indicators: false
        }
      });
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get('/api/license/status');
      if (response.data && response.data.license) {
        setLicenseInfo(response.data.license);
      }
    } catch (err) {
      console.error('Error checking license status:', err);
      setError(err.response?.data?.error || 'Failed to check license status');
      
      // Set default free license on error
      setLicenseInfo({
        type: 'free',
        active: false,
        expires: null,
        activated: null,
        features: {
          max_bots: 1,
          live_trading: false,
          advanced_strategies: false,
          api_access: false,
          priority_support: false,
          custom_indicators: false
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Activate license
  const activateLicense = async (licenseKey) => {
    if (!isAuthenticated) {
      throw new Error('Authentication required');
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/license/activate', {
        license_key: licenseKey
      });
      
      if (response.data && response.data.license) {
        setLicenseInfo(response.data.license);
        return { success: true, message: response.data.message };
      }
      
      return { success: false, message: 'Unexpected response format' };
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'License activation failed';
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Deactivate license
  const deactivateLicense = async () => {
    if (!isAuthenticated) {
      throw new Error('Authentication required');
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/license/deactivate', {});
      
      if (response.data && response.data.license) {
        setLicenseInfo(response.data.license);
        return { success: true, message: response.data.message };
      }
      
      return { success: false, message: 'Unexpected response format' };
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'License deactivation failed';
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Validate license key
  const validateLicenseKey = async (licenseKey) => {
    if (!isAuthenticated) {
      throw new Error('Authentication required');
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/license/validate', {
        license_key: licenseKey
      });
      
      return {
        valid: response.data.valid,
        licenseData: response.data.license_data,
        error: response.data.error
      };
    } catch (err) {
      return {
        valid: false,
        licenseData: null,
        error: err.response?.data?.error || 'License validation failed'
      };
    } finally {
      setLoading(false);
    }
  };

  // Check feature access
  const hasFeature = (feature) => {
    return licenseInfo.features?.[feature] || false;
  };

  // Check if user has valid license
  const hasValidLicense = () => {
    return licenseInfo.active && licenseInfo.type !== 'free';
  };

  // Get license features
  const getLicenseFeatures = () => {
    return licenseInfo.features || {};
  };

  // Get license type
  const getLicenseType = () => {
    return licenseInfo.type || 'free';
  };

  // Get license expiration
  const getLicenseExpiration = () => {
    return licenseInfo.expires;
  };

  // Check if license is expired
  const isLicenseExpired = () => {
    if (!licenseInfo.expires) return false;
    return new Date() > new Date(licenseInfo.expires);
  };

  // Get days until expiration
  const getDaysUntilExpiration = () => {
    if (!licenseInfo.expires) return null;
    const expirationDate = new Date(licenseInfo.expires);
    const today = new Date();
    const diffTime = expirationDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  // Check if user has required license for a feature
  const requiresLicense = (feature) => {
    const hasAccess = hasFeature(feature);
    if (!hasAccess) {
      // Show upgrade prompt or toast message
      const currentType = getLicenseType();
      const message = currentType === 'free' 
        ? `This feature requires a premium license. Please upgrade your account.`
        : `This feature is not available in your ${currentType} license.`;
      
      // You can customize this to show a modal, toast, or other UI feedback
      console.warn(message);
      
      // For now, we'll use a simple alert, but this can be replaced with a proper modal
      if (typeof window !== 'undefined') {
        alert(message);
      }
    }
    return hasAccess;
  };

  // Effect to check license status when user changes
  useEffect(() => {
    if (user && isAuthenticated) {
      checkLicenseStatus();
    }
  }, [user, isAuthenticated]);

  const value = {
    // License info
    licenseInfo,
    loading,
    error,
    
    // Actions
    checkLicenseStatus,
    activateLicense,
    deactivateLicense,
    validateLicenseKey,
    
    // Helpers
    hasFeature,
    hasValidLicense,
    getLicenseFeatures,
    getLicenseType,
    getLicenseExpiration,
    isLicenseExpired,
    getDaysUntilExpiration,
    requiresLicense
  };

  return (
    <LicenseContext.Provider value={value}>
      {children}
    </LicenseContext.Provider>
  );
};

export default LicenseContext;