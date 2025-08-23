import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useLicense } from '../contexts/LicenseContext';
import { useAuth } from '../contexts/AuthContext';

const LicenseGuard = ({ children, feature = null, redirectTo = '/license' }) => {
  const { user } = useAuth();
  const { licenseInfo, hasFeature, hasValidLicense, loading } = useLicense();
  const location = useLocation();

  // Show loading while checking license
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If user is not authenticated, redirect to login
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If no specific feature is required, just check for valid license
  if (!feature) {
    if (!hasValidLicense()) {
      return <Navigate to={redirectTo} state={{ from: location }} replace />;
    }
    return children;
  }

  // Check specific feature access
  if (!hasFeature(feature)) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg
                  className="h-6 w-6 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                License Required
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                This feature requires a {feature.replace('_', ' ')} license.
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Current license: {licenseInfo.type}
              </p>
              <div className="mt-6">
                <button
                  onClick={() => window.location.href = redirectTo}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Upgrade License
                </button>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => window.history.back()}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  Go Back
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return children;
};

export default LicenseGuard;