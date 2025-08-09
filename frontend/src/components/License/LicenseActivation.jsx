import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { CheckCircle, XCircle, Key, Shield, Clock, AlertTriangle } from 'lucide-react';
import { useTradingStore } from '../../stores/useTradingStore';

const LicenseActivation = () => {
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [licenseStatus, setLicenseStatus] = useState(null);
  const { user } = useTradingStore();

  useEffect(() => {
    checkLicenseStatus();
  }, []);

  const checkLicenseStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/license/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLicenseStatus(data);
      }
    } catch (err) {
      console.error('Failed to check license status:', err);
    }
  };

  const handleActivation = async (e) => {
    e.preventDefault();
    if (!licenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/license/activate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ license_key: licenseKey })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('License activated successfully!');
        setLicenseKey('');
        await checkLicenseStatus();
      } else {
        setError(data.error || 'Failed to activate license');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivation = async () => {
    if (!window.confirm('Are you sure you want to deactivate your license?')) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/license/deactivate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('License deactivated successfully');
        await checkLicenseStatus();
      } else {
        setError(data.error || 'Failed to deactivate license');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'expired':
        return <Clock className="h-5 w-5 text-orange-500" />;
      case 'invalid':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      expired: 'bg-orange-100 text-orange-800',
      invalid: 'bg-red-100 text-red-800',
      inactive: 'bg-gray-100 text-gray-800'
    };

    return (
      <Badge className={variants[status] || variants.inactive}>
        {status?.toUpperCase() || 'INACTIVE'}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isLicenseActive = licenseStatus?.status === 'active';

  return (
    <div className="space-y-6">
      {/* License Status Card */}
      {licenseStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              License Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon(licenseStatus.status)}
                <span className="font-medium">Status:</span>
              </div>
              {getStatusBadge(licenseStatus.status)}
            </div>

            {licenseStatus.license_type && (
              <div className="flex items-center justify-between">
                <span className="font-medium">License Type:</span>
                <Badge variant="outline">{licenseStatus.license_type.toUpperCase()}</Badge>
              </div>
            )}

            {licenseStatus.activated_at && (
              <div className="flex items-center justify-between">
                <span className="font-medium">Activated:</span>
                <span className="text-sm text-gray-600">
                  {formatDate(licenseStatus.activated_at)}
                </span>
              </div>
            )}

            {licenseStatus.expires_at && (
              <div className="flex items-center justify-between">
                <span className="font-medium">Expires:</span>
                <span className="text-sm text-gray-600">
                  {formatDate(licenseStatus.expires_at)}
                </span>
              </div>
            )}

            {licenseStatus.features && licenseStatus.features.length > 0 && (
              <div>
                <span className="font-medium block mb-2">Available Features:</span>
                <div className="flex flex-wrap gap-2">
                  {licenseStatus.features.map((feature, index) => (
                    <Badge key={index} variant="secondary">
                      {feature.replace('_', ' ').toUpperCase()}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {isLicenseActive && (
              <Button
                onClick={handleDeactivation}
                variant="outline"
                className="w-full mt-4"
                disabled={loading}
              >
                Deactivate License
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* License Activation Card */}
      {!isLicenseActive && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Activate License
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleActivation} className="space-y-4">
              <div>
                <label htmlFor="licenseKey" className="block text-sm font-medium mb-2">
                  License Key
                </label>
                <Input
                  id="licenseKey"
                  type="text"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  placeholder="Enter your license key"
                  className="font-mono"
                  disabled={loading}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading || !licenseKey.trim()}
              >
                {loading ? 'Activating...' : 'Activate License'}
              </Button>
            </form>

            {error && (
              <Alert className="mt-4 border-red-200 bg-red-50">
                <XCircle className="h-4 w-4 text-red-500" />
                <AlertDescription className="text-red-700">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="mt-4 border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <AlertDescription className="text-green-700">
                  {success}
                </AlertDescription>
              </Alert>
            )}

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Need a License?</h4>
              <p className="text-sm text-blue-700 mb-3">
                Purchase a license to unlock all trading features including live trading, 
                advanced strategies, and premium support.
              </p>
              <div className="text-xs text-blue-600">
                <p>• Demo mode: Limited to testnet trading</p>
                <p>• Full license: Live trading + all features</p>
                <p>• Enterprise: Custom solutions available</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LicenseActivation;