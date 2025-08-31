import React, { useState, useEffect } from 'react';
import { FaGoogle, FaGithub, FaMicrosoft, FaSpinner } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { useAuth } from '../../contexts/AuthContext';
import { authAPI } from '../../services/api';

const OAuthLogin = ({ onSuccess, onError }) => {
  const [providers, setProviders] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingProvider, setLoadingProvider] = useState(null);
  const { login } = useAuth();

  // Provider icons mapping
  const providerIcons = {
    google: FaGoogle,
    github: FaGithub,
    microsoft: FaMicrosoft
  };

  // Load available OAuth providers
  useEffect(() => {
    const loadProviders = async () => {
      try {
        const response = await authAPI.get('/oauth/providers');
        setProviders(response.data.providers);
      } catch (error) {
        console.error('Failed to load OAuth providers:', error);
      }
    };

    loadProviders();
  }, []);

  // Handle OAuth callback from URL parameters
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const accessToken = urlParams.get('access_token');
      const refreshToken = urlParams.get('refresh_token');
      const userId = urlParams.get('user_id');
      const error = urlParams.get('error');

      if (error) {
        toast.error(`OAuth authentication failed: ${error}`);
        onError?.(error);
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }

      if (accessToken && refreshToken && userId) {
        try {
          // Store tokens and login user
          localStorage.setItem('access_token', accessToken);
          localStorage.setItem('refresh_token', refreshToken);
          
          // Get user info and complete login
          await login({ access_token: accessToken, refresh_token: refreshToken });
          
          toast.success('Successfully logged in with OAuth!');
          onSuccess?.();
        } catch (error) {
          console.error('OAuth login completion failed:', error);
          toast.error('Failed to complete OAuth login');
          onError?.(error);
        }
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    };

    handleOAuthCallback();
  }, [login, onSuccess, onError]);

  const handleOAuthLogin = async (provider) => {
    setLoading(true);
    setLoadingProvider(provider);

    try {
      // Get authorization URL
      const response = await authAPI.get(`/oauth/${provider}/authorize`);
      const { authorization_url } = response.data;

      // Redirect to OAuth provider
      window.location.href = authorization_url;
    } catch (error) {
      console.error(`OAuth ${provider} login failed:`, error);
      toast.error(`Failed to initiate ${provider} login`);
      onError?.(error);
    } finally {
      setLoading(false);
      setLoadingProvider(null);
    }
  };

  const getProviderDisplayName = (provider) => {
    return providers[provider]?.name || provider.charAt(0).toUpperCase() + provider.slice(1);
  };

  const getProviderColor = (provider) => {
    return providers[provider]?.color || '#6b7280';
  };

  if (Object.keys(providers).length === 0) {
    return null; // No OAuth providers configured
  }

  return (
    <div className="oauth-login">
      <div className="flex items-center my-6">
        <div className="flex-1 border-t border-gray-300"></div>
        <div className="px-4 text-sm text-gray-500 bg-white">
          Or continue with
        </div>
        <div className="flex-1 border-t border-gray-300"></div>
      </div>

      <div className="space-y-3">
        {Object.entries(providers).map(([provider, config]) => {
          const IconComponent = providerIcons[provider];
          const isLoading = loadingProvider === provider;
          
          return (
            <button
              key={provider}
              onClick={() => handleOAuthLogin(provider)}
              disabled={loading}
              className={`
                w-full flex items-center justify-center px-4 py-3 border border-gray-300 
                rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white 
                hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 
                focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors duration-200
              `}
              style={{
                borderColor: config.color,
                '--hover-bg': `${config.color}10`
              }}
            >
              {isLoading ? (
                <FaSpinner className="animate-spin mr-3 h-5 w-5" style={{ color: config.color }} />
              ) : (
                IconComponent && <IconComponent className="mr-3 h-5 w-5" style={{ color: config.color }} />
              )}
              {isLoading ? (
                `Connecting to ${getProviderDisplayName(provider)}...`
              ) : (
                `Continue with ${getProviderDisplayName(provider)}`
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        By continuing, you agree to our Terms of Service and Privacy Policy
      </div>
    </div>
  );
};

export default OAuthLogin;