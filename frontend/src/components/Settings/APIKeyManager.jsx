import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  EyeOff, 
  TestTube, 
  CheckCircle, 
  XCircle, 
  Key, 
  Shield,
  AlertTriangle,
  Clock
} from 'lucide-react';
import { useTradingStore } from '../../stores/useTradingStore';

const APIKeyManager = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [testingKey, setTestingKey] = useState(null);
  const { user } = useTradingStore();

  const [formData, setFormData] = useState({
    key_name: '',
    exchange: '',
    api_key: '',
    api_secret: '',
    passphrase: '',
    testnet: true,
    permissions: ['read', 'trade'],
    validate_keys: true
  });

  const [showSecrets, setShowSecrets] = useState({});

  const exchanges = [
    { value: 'binance', label: 'Binance', requiresPassphrase: false },
    { value: 'coinbase', label: 'Coinbase Pro', requiresPassphrase: true },
    { value: 'kraken', label: 'Kraken', requiresPassphrase: false },
    { value: 'bitfinex', label: 'Bitfinex', requiresPassphrase: false },
    { value: 'okx', label: 'OKX', requiresPassphrase: true },
    { value: 'kucoin', label: 'KuCoin', requiresPassphrase: true }
  ];

  const permissions = [
    { value: 'read', label: 'Read (View balances & orders)' },
    { value: 'trade', label: 'Trade (Place & cancel orders)' },
    { value: 'withdraw', label: 'Withdraw (Transfer funds)' }
  ];

  useEffect(() => {
    fetchAPIKeys();
  }, []);

  const fetchAPIKeys = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/api-keys/list', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.api_keys || []);
      } else {
        setError('Failed to fetch API keys');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const url = editingKey ? `/api/api-keys/update/${editingKey.id}` : '/api/api-keys/add';
      const method = editingKey ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(editingKey ? 'API key updated successfully!' : 'API key added successfully!');
        resetForm();
        setShowAddDialog(false);
        setEditingKey(null);
        await fetchAPIKeys();
      } else {
        setError(data.error || 'Failed to save API key');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (keyId, keyName) => {
    if (!window.confirm(`Are you sure you want to delete the API key "${keyName}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/api-keys/remove/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setSuccess('API key deleted successfully');
        await fetchAPIKeys();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to delete API key');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleTest = async (keyId) => {
    setTestingKey(keyId);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/api-keys/test/${keyId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(`API key test successful for ${data.exchange}`);
        await fetchAPIKeys(); // Refresh to update last_used
      } else {
        setError(data.error || 'API key test failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setTestingKey(null);
    }
  };

  const resetForm = () => {
    setFormData({
      key_name: '',
      exchange: '',
      api_key: '',
      api_secret: '',
      passphrase: '',
      testnet: true,
      permissions: ['read', 'trade'],
      validate_keys: true
    });
  };

  const handleEdit = (apiKey) => {
    setEditingKey(apiKey);
    setFormData({
      key_name: apiKey.key_name,
      exchange: apiKey.exchange,
      api_key: '', // Don't pre-fill for security
      api_secret: '', // Don't pre-fill for security
      passphrase: '',
      testnet: apiKey.testnet,
      permissions: apiKey.permissions || ['read', 'trade'],
      validate_keys: false // Don't validate by default when editing
    });
    setShowAddDialog(true);
  };

  const toggleShowSecret = (keyId) => {
    setShowSecrets(prev => ({
      ...prev,
      [keyId]: !prev[keyId]
    }));
  };

  const getExchangeInfo = (exchange) => {
    return exchanges.find(ex => ex.value === exchange) || { label: exchange, requiresPassphrase: false };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const selectedExchange = exchanges.find(ex => ex.value === formData.exchange);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">API Key Management</h2>
          <p className="text-gray-600">Securely manage your exchange API keys with encrypted storage</p>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="h-4 w-4 mr-2" />
              Add API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {editingKey ? 'Edit API Key' : 'Add New API Key'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="key_name">Key Name *</Label>
                  <Input
                    id="key_name"
                    value={formData.key_name}
                    onChange={(e) => setFormData({...formData, key_name: e.target.value})}
                    placeholder="My Trading Key"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="exchange">Exchange *</Label>
                  <Select
                    value={formData.exchange}
                    onValueChange={(value) => setFormData({...formData, exchange: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select exchange" />
                    </SelectTrigger>
                    <SelectContent>
                      {exchanges.map(exchange => (
                        <SelectItem key={exchange.value} value={exchange.value}>
                          {exchange.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="api_key">API Key *</Label>
                <Input
                  id="api_key"
                  type="text"
                  value={formData.api_key}
                  onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                  placeholder="Your API key"
                  className="font-mono"
                  required={!editingKey}
                />
              </div>

              <div>
                <Label htmlFor="api_secret">API Secret *</Label>
                <Input
                  id="api_secret"
                  type="password"
                  value={formData.api_secret}
                  onChange={(e) => setFormData({...formData, api_secret: e.target.value})}
                  placeholder="Your API secret"
                  className="font-mono"
                  required={!editingKey}
                />
              </div>

              {selectedExchange?.requiresPassphrase && (
                <div>
                  <Label htmlFor="passphrase">Passphrase</Label>
                  <Input
                    id="passphrase"
                    type="password"
                    value={formData.passphrase}
                    onChange={(e) => setFormData({...formData, passphrase: e.target.value})}
                    placeholder="Passphrase (if required)"
                    className="font-mono"
                  />
                </div>
              )}

              <div>
                <Label>Permissions</Label>
                <div className="space-y-2 mt-2">
                  {permissions.map(permission => (
                    <div key={permission.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={permission.value}
                        checked={formData.permissions.includes(permission.value)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              permissions: [...formData.permissions, permission.value]
                            });
                          } else {
                            setFormData({
                              ...formData,
                              permissions: formData.permissions.filter(p => p !== permission.value)
                            });
                          }
                        }}
                      />
                      <Label htmlFor={permission.value} className="text-sm">
                        {permission.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="testnet"
                  checked={formData.testnet}
                  onCheckedChange={(checked) => setFormData({...formData, testnet: checked})}
                />
                <Label htmlFor="testnet">Use Testnet (Recommended for testing)</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="validate_keys"
                  checked={formData.validate_keys}
                  onCheckedChange={(checked) => setFormData({...formData, validate_keys: checked})}
                />
                <Label htmlFor="validate_keys">Validate API keys before saving</Label>
              </div>

              <div className="flex gap-2 pt-4">
                <Button type="submit" disabled={loading} className="flex-1">
                  {loading ? 'Saving...' : (editingKey ? 'Update' : 'Add')} API Key
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowAddDialog(false);
                    setEditingKey(null);
                    resetForm();
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Alerts */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <XCircle className="h-4 w-4 text-red-500" />
          <AlertDescription className="text-red-700">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-500" />
          <AlertDescription className="text-green-700">{success}</AlertDescription>
        </Alert>
      )}

      {/* API Keys List */}
      <div className="grid gap-4">
        {apiKeys.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Key className="h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No API Keys</h3>
              <p className="text-gray-600 text-center mb-4">
                Add your first API key to start trading. All keys are encrypted and stored securely.
              </p>
              <Button onClick={() => setShowAddDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First API Key
              </Button>
            </CardContent>
          </Card>
        ) : (
          apiKeys.map((apiKey) => (
            <Card key={apiKey.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-medium">{apiKey.key_name}</h3>
                      <Badge variant="outline">
                        {getExchangeInfo(apiKey.exchange).label}
                      </Badge>
                      {apiKey.testnet && (
                        <Badge className="bg-blue-100 text-blue-800">TESTNET</Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-600">API Key:</span>
                        <div className="flex items-center gap-2 mt-1">
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                            {showSecrets[apiKey.id] 
                              ? apiKey.api_key_preview?.replace('...', '••••••••')
                              : apiKey.api_key_preview
                            }
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => toggleShowSecret(apiKey.id)}
                          >
                            {showSecrets[apiKey.id] ? 
                              <EyeOff className="h-3 w-3" /> : 
                              <Eye className="h-3 w-3" />
                            }
                          </Button>
                        </div>
                      </div>

                      <div>
                        <span className="font-medium text-gray-600">Permissions:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {apiKey.permissions?.map(perm => (
                            <Badge key={perm} variant="secondary" className="text-xs">
                              {perm}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div>
                        <span className="font-medium text-gray-600">Created:</span>
                        <p className="text-gray-800 mt-1">{formatDate(apiKey.created_at)}</p>
                      </div>

                      <div>
                        <span className="font-medium text-gray-600">Last Used:</span>
                        <p className="text-gray-800 mt-1">{formatDate(apiKey.last_used)}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mt-4 text-sm text-gray-600">
                      <Shield className="h-4 w-4" />
                      <span>Encrypted and stored securely</span>
                      <span>•</span>
                      <span>Used {apiKey.usage_count || 0} times</span>
                    </div>
                  </div>

                  <div className="flex gap-2 ml-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleTest(apiKey.id)}
                      disabled={testingKey === apiKey.id}
                    >
                      {testingKey === apiKey.id ? (
                        <Clock className="h-4 w-4" />
                      ) : (
                        <TestTube className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEdit(apiKey)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(apiKey.id, apiKey.key_name)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Security Notice */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900 mb-1">Security Information</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>• All API keys are encrypted using AES-256 encryption before storage</p>
                <p>• Keys are only decrypted when needed for trading operations</p>
                <p>• We recommend using testnet keys for initial setup and testing</p>
                <p>• Only grant minimum required permissions (avoid 'withdraw' unless necessary)</p>
                <p>• Regularly rotate your API keys for enhanced security</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default APIKeyManager;