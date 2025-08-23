import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Slider,
  Grid,
  Tabs,
  Tab,
  Divider,
  Alert,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Paper
} from '@mui/material';
import {
  Security,
  TrendingUp,
  Notifications,
  Api,
  Save,
  Visibility,
  VisibilityOff,
  Delete,
  Add,
  Warning,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { toast } from 'react-hot-toast';
import axios from 'axios';

const ProSettings = () => {
  const { user, token } = useAuth();
  const { isDark } = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [apiKeyToDelete, setApiKeyToDelete] = useState(null);

  // Risk Management Settings
  const [riskSettings, setRiskSettings] = useState({
    max_risk_per_trade: 2.0,
    max_daily_loss: 5.0,
    max_drawdown: 10.0,
    position_size_method: 'fixed_percentage',
    stop_loss_percentage: 2.0,
    take_profit_percentage: 4.0,
    trailing_stop: false,
    trailing_stop_percentage: 1.0,
    max_open_positions: 5,
    risk_reward_ratio: 2.0,
    enable_emergency_stop: true,
    emergency_stop_loss: 15.0
  });

  // API Keys Management
  const [apiKeys, setApiKeys] = useState([]);
  const [newApiKey, setNewApiKey] = useState({
    name: '',
    exchange: 'binance',
    api_key: '',
    secret_key: '',
    testnet: false,
    permissions: []
  });

  // Notification Settings
  const [notificationSettings, setNotificationSettings] = useState({
    email_notifications: true,
    telegram_notifications: false,
    telegram_chat_id: '',
    telegram_bot_token: '',
    trade_notifications: true,
    profit_loss_alerts: true,
    system_alerts: true,
    daily_summary: true,
    weekly_report: false,
    alert_thresholds: {
      profit_threshold: 100,
      loss_threshold: -50,
      volume_threshold: 1000
    }
  });

  // Trading Preferences
  const [tradingPreferences, setTradingPreferences] = useState({
    auto_trading: false,
    preferred_pairs: ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
    trading_hours: {
      enabled: false,
      start_time: '09:00',
      end_time: '17:00',
      timezone: 'UTC'
    },
    blacklisted_pairs: [],
    min_volume_filter: 1000000,
    max_spread_percentage: 0.1,
    enable_news_filter: true
  });

  useEffect(() => {
    if (token) {
      fetchSettings();
      fetchApiKeys();
    }
  }, [token]);

  const fetchSettings = async () => {
    try {
      const response = await axios.get('/api/user/settings', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const settings = response.data;
      if (settings.risk_settings) setRiskSettings(settings.risk_settings);
      if (settings.notification_settings) setNotificationSettings(settings.notification_settings);
      if (settings.trading_preferences) setTradingPreferences(settings.trading_preferences);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await axios.get('/api/user/api-keys', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setApiKeys(response.data.api_keys || []);
    } catch (error) {
      console.error('Error fetching API keys:', error);
    }
  };

  const saveRiskSettings = async () => {
    setLoading(true);
    try {
      await axios.put('/api/user/settings/risk', riskSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Risk settings saved successfully');
    } catch (error) {
      console.error('Error saving risk settings:', error);
      toast.error('Failed to save risk settings');
    } finally {
      setLoading(false);
    }
  };

  const saveNotificationSettings = async () => {
    setLoading(true);
    try {
      await axios.put('/api/user/settings/notifications', notificationSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Notification settings saved successfully');
    } catch (error) {
      console.error('Error saving notification settings:', error);
      toast.error('Failed to save notification settings');
    } finally {
      setLoading(false);
    }
  };

  const saveTradingPreferences = async () => {
    setLoading(true);
    try {
      await axios.put('/api/user/settings/trading', tradingPreferences, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Trading preferences saved successfully');
    } catch (error) {
      console.error('Error saving trading preferences:', error);
      toast.error('Failed to save trading preferences');
    } finally {
      setLoading(false);
    }
  };

  const addApiKey = async () => {
    if (!newApiKey.name || !newApiKey.api_key || !newApiKey.secret_key) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      await axios.post('/api/user/api-keys', newApiKey, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('API key added successfully');
      setNewApiKey({
        name: '',
        exchange: 'binance',
        api_key: '',
        secret_key: '',
        testnet: false,
        permissions: []
      });
      fetchApiKeys();
    } catch (error) {
      console.error('Error adding API key:', error);
      toast.error('Failed to add API key');
    } finally {
      setLoading(false);
    }
  };

  const deleteApiKey = async (keyId) => {
    setLoading(true);
    try {
      await axios.delete(`/api/user/api-keys/${keyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('API key deleted successfully');
      fetchApiKeys();
    } catch (error) {
      console.error('Error deleting API key:', error);
      toast.error('Failed to delete API key');
    } finally {
      setLoading(false);
      setDeleteConfirmOpen(false);
      setApiKeyToDelete(null);
    }
  };

  const testApiKey = async (keyId) => {
    setLoading(true);
    try {
      const response = await axios.post(`/api/user/api-keys/${keyId}/test`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        toast.success('API key test successful');
      } else {
        toast.error('API key test failed');
      }
    } catch (error) {
      console.error('Error testing API key:', error);
      toast.error('API key test failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const renderRiskManagement = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Security color="primary" />
        Risk Management
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Position Sizing
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Max Risk Per Trade: {riskSettings.max_risk_per_trade}%</Typography>
                <Slider
                  value={riskSettings.max_risk_per_trade}
                  onChange={(e, value) => setRiskSettings({...riskSettings, max_risk_per_trade: value})}
                  min={0.1}
                  max={10}
                  step={0.1}
                  marks={[{value: 1, label: '1%'}, {value: 5, label: '5%'}, {value: 10, label: '10%'}]}
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Max Daily Loss: {riskSettings.max_daily_loss}%</Typography>
                <Slider
                  value={riskSettings.max_daily_loss}
                  onChange={(e, value) => setRiskSettings({...riskSettings, max_daily_loss: value})}
                  min={1}
                  max={20}
                  step={0.5}
                  marks={[{value: 5, label: '5%'}, {value: 10, label: '10%'}, {value: 20, label: '20%'}]}
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <TextField
                fullWidth
                label="Max Open Positions"
                type="number"
                value={riskSettings.max_open_positions}
                onChange={(e) => setRiskSettings({...riskSettings, max_open_positions: parseInt(e.target.value)})}
                sx={{ mb: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Stop Loss & Take Profit
              </Typography>
              
              <TextField
                fullWidth
                label="Stop Loss %"
                type="number"
                value={riskSettings.stop_loss_percentage}
                onChange={(e) => setRiskSettings({...riskSettings, stop_loss_percentage: parseFloat(e.target.value)})}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Take Profit %"
                type="number"
                value={riskSettings.take_profit_percentage}
                onChange={(e) => setRiskSettings({...riskSettings, take_profit_percentage: parseFloat(e.target.value)})}
                sx={{ mb: 2 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={riskSettings.trailing_stop}
                    onChange={(e) => setRiskSettings({...riskSettings, trailing_stop: e.target.checked})}
                  />
                }
                label="Enable Trailing Stop"
                sx={{ mb: 2 }}
              />
              
              {riskSettings.trailing_stop && (
                <TextField
                  fullWidth
                  label="Trailing Stop %"
                  type="number"
                  value={riskSettings.trailing_stop_percentage}
                  onChange={(e) => setRiskSettings({...riskSettings, trailing_stop_percentage: parseFloat(e.target.value)})}
                  sx={{ mb: 2 }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Emergency Controls
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={riskSettings.enable_emergency_stop}
                    onChange={(e) => setRiskSettings({...riskSettings, enable_emergency_stop: e.target.checked})}
                  />
                }
                label="Enable Emergency Stop Loss"
                sx={{ mb: 2 }}
              />
              
              {riskSettings.enable_emergency_stop && (
                <TextField
                  label="Emergency Stop Loss %"
                  type="number"
                  value={riskSettings.emergency_stop_loss}
                  onChange={(e) => setRiskSettings({...riskSettings, emergency_stop_loss: parseFloat(e.target.value)})}
                  sx={{ width: 200 }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={saveRiskSettings}
          disabled={loading}
          startIcon={<Save />}
        >
          Save Risk Settings
        </Button>
      </Box>
    </Box>
  );

  const renderApiKeyManagement = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Api color="primary" />
        API Key Management
      </Typography>
      
      {/* Add New API Key */}
      <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Add New API Key
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Key Name"
                value={newApiKey.name}
                onChange={(e) => setNewApiKey({...newApiKey, name: e.target.value})}
                sx={{ mb: 2 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Exchange</InputLabel>
                <Select
                  value={newApiKey.exchange}
                  onChange={(e) => setNewApiKey({...newApiKey, exchange: e.target.value})}
                  label="Exchange"
                >
                  <MenuItem value="binance">Binance</MenuItem>
                  <MenuItem value="coinbase">Coinbase Pro</MenuItem>
                  <MenuItem value="kraken">Kraken</MenuItem>
                  <MenuItem value="bybit">Bybit</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="API Key"
                type={showApiKey ? 'text' : 'password'}
                value={newApiKey.api_key}
                onChange={(e) => setNewApiKey({...newApiKey, api_key: e.target.value})}
                InputProps={{
                  endAdornment: (
                    <IconButton onClick={() => setShowApiKey(!showApiKey)}>
                      {showApiKey ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  )
                }}
                sx={{ mb: 2 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Secret Key"
                type="password"
                value={newApiKey.secret_key}
                onChange={(e) => setNewApiKey({...newApiKey, secret_key: e.target.value})}
                sx={{ mb: 2 }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newApiKey.testnet}
                    onChange={(e) => setNewApiKey({...newApiKey, testnet: e.target.checked})}
                  />
                }
                label="Testnet/Sandbox Mode"
                sx={{ mb: 2 }}
              />
            </Grid>
          </Grid>
          
          <Button
            variant="contained"
            onClick={addApiKey}
            disabled={loading}
            startIcon={<Add />}
          >
            Add API Key
          </Button>
        </CardContent>
      </Card>
      
      {/* Existing API Keys */}
      <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Existing API Keys
          </Typography>
          
          <List>
            {apiKeys.map((key) => (
              <ListItem key={key.id} divider>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle2">{key.name}</Typography>
                      <Chip 
                        label={key.exchange} 
                        size="small" 
                        color="primary" 
                        variant="outlined" 
                      />
                      {key.testnet && (
                        <Chip 
                          label="Testnet" 
                          size="small" 
                          color="warning" 
                          variant="outlined" 
                        />
                      )}
                      {key.status === 'active' ? (
                        <CheckCircle color="success" fontSize="small" />
                      ) : (
                        <Error color="error" fontSize="small" />
                      )}
                    </Box>
                  }
                  secondary={`Created: ${new Date(key.created_at).toLocaleDateString()}`}
                />
                <ListItemSecondaryAction>
                  <Tooltip title="Test Connection">
                    <IconButton onClick={() => testApiKey(key.id)} disabled={loading}>
                      <CheckCircle />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton 
                      onClick={() => {
                        setApiKeyToDelete(key);
                        setDeleteConfirmOpen(true);
                      }}
                      disabled={loading}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
          
          {apiKeys.length === 0 && (
            <Alert severity="info">
              No API keys configured. Add your first API key to start trading.
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );

  const renderNotifications = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Notifications color="primary" />
        Notification Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Email Notifications
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.email_notifications}
                    onChange={(e) => setNotificationSettings({...notificationSettings, email_notifications: e.target.checked})}
                  />
                }
                label="Enable Email Notifications"
                sx={{ mb: 2 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.trade_notifications}
                    onChange={(e) => setNotificationSettings({...notificationSettings, trade_notifications: e.target.checked})}
                  />
                }
                label="Trade Notifications"
                sx={{ mb: 2 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.daily_summary}
                    onChange={(e) => setNotificationSettings({...notificationSettings, daily_summary: e.target.checked})}
                  />
                }
                label="Daily Summary"
                sx={{ mb: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Telegram Notifications
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.telegram_notifications}
                    onChange={(e) => setNotificationSettings({...notificationSettings, telegram_notifications: e.target.checked})}
                  />
                }
                label="Enable Telegram Notifications"
                sx={{ mb: 2 }}
              />
              
              {notificationSettings.telegram_notifications && (
                <>
                  <TextField
                    fullWidth
                    label="Telegram Bot Token"
                    value={notificationSettings.telegram_bot_token}
                    onChange={(e) => setNotificationSettings({...notificationSettings, telegram_bot_token: e.target.value})}
                    sx={{ mb: 2 }}
                  />
                  
                  <TextField
                    fullWidth
                    label="Telegram Chat ID"
                    value={notificationSettings.telegram_chat_id}
                    onChange={(e) => setNotificationSettings({...notificationSettings, telegram_chat_id: e.target.value})}
                    sx={{ mb: 2 }}
                  />
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Alert Thresholds
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Profit Alert Threshold ($)"
                    type="number"
                    value={notificationSettings.alert_thresholds.profit_threshold}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      alert_thresholds: {
                        ...notificationSettings.alert_thresholds,
                        profit_threshold: parseFloat(e.target.value)
                      }
                    })}
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Loss Alert Threshold ($)"
                    type="number"
                    value={notificationSettings.alert_thresholds.loss_threshold}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      alert_thresholds: {
                        ...notificationSettings.alert_thresholds,
                        loss_threshold: parseFloat(e.target.value)
                      }
                    })}
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Volume Alert Threshold ($)"
                    type="number"
                    value={notificationSettings.alert_thresholds.volume_threshold}
                    onChange={(e) => setNotificationSettings({
                      ...notificationSettings,
                      alert_thresholds: {
                        ...notificationSettings.alert_thresholds,
                        volume_threshold: parseFloat(e.target.value)
                      }
                    })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={saveNotificationSettings}
          disabled={loading}
          startIcon={<Save />}
        >
          Save Notification Settings
        </Button>
      </Box>
    </Box>
  );

  const renderTradingPreferences = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUp color="primary" />
        Trading Preferences
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                General Settings
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={tradingPreferences.auto_trading}
                    onChange={(e) => setTradingPreferences({...tradingPreferences, auto_trading: e.target.checked})}
                  />
                }
                label="Enable Auto Trading"
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Minimum Volume Filter"
                type="number"
                value={tradingPreferences.min_volume_filter}
                onChange={(e) => setTradingPreferences({...tradingPreferences, min_volume_filter: parseFloat(e.target.value)})}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Max Spread Percentage"
                type="number"
                value={tradingPreferences.max_spread_percentage}
                onChange={(e) => setTradingPreferences({...tradingPreferences, max_spread_percentage: parseFloat(e.target.value)})}
                sx={{ mb: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Trading Hours
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={tradingPreferences.trading_hours.enabled}
                    onChange={(e) => setTradingPreferences({
                      ...tradingPreferences,
                      trading_hours: {
                        ...tradingPreferences.trading_hours,
                        enabled: e.target.checked
                      }
                    })}
                  />
                }
                label="Enable Trading Hours Restriction"
                sx={{ mb: 2 }}
              />
              
              {tradingPreferences.trading_hours.enabled && (
                <>
                  <TextField
                    fullWidth
                    label="Start Time"
                    type="time"
                    value={tradingPreferences.trading_hours.start_time}
                    onChange={(e) => setTradingPreferences({
                      ...tradingPreferences,
                      trading_hours: {
                        ...tradingPreferences.trading_hours,
                        start_time: e.target.value
                      }
                    })}
                    sx={{ mb: 2 }}
                  />
                  
                  <TextField
                    fullWidth
                    label="End Time"
                    type="time"
                    value={tradingPreferences.trading_hours.end_time}
                    onChange={(e) => setTradingPreferences({
                      ...tradingPreferences,
                      trading_hours: {
                        ...tradingPreferences.trading_hours,
                        end_time: e.target.value
                      }
                    })}
                    sx={{ mb: 2 }}
                  />
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={saveTradingPreferences}
          disabled={loading}
          startIcon={<Save />}
        >
          Save Trading Preferences
        </Button>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ p: 3, minHeight: '100vh', bgcolor: isDark ? '#0f172a' : '#f8fafc' }}>
      <Typography variant="h4" fontWeight="bold" color={isDark ? '#f1f5f9' : '#0f172a'} mb={3}>
        Pro Settings
      </Typography>
      
      <Paper sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Risk Management" />
          <Tab label="API Keys" />
          <Tab label="Notifications" />
          <Tab label="Trading Preferences" />
        </Tabs>
        
        <Box sx={{ p: 3 }}>
          {activeTab === 0 && renderRiskManagement()}
          {activeTab === 1 && renderApiKeyManagement()}
          {activeTab === 2 && renderNotifications()}
          {activeTab === 3 && renderTradingPreferences()}
        </Box>
      </Paper>
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the API key "{apiKeyToDelete?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => deleteApiKey(apiKeyToDelete?.id)} 
            color="error" 
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProSettings;