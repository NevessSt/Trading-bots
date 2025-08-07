import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  InputAdornment,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import useAuthStore from '../stores/useAuthStore';
import useTradingStore from '../stores/useTradingStore';

const Settings = () => {
  const { user } = useAuthStore();
  const { updateSettings } = useTradingStore();
  const [tab, setTab] = useState(0);
  
  // Settings state
  const [tradingSettings, setTradingSettings] = useState({
    maxDailyLoss: 5,
    maxTradeSize: 10,
    maxOpenPositions: 3,
    maxTradesPerDay: 10,
    defaultTakeProfit: 2,
    defaultStopLoss: 1
  });
  
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    telegramNotifications: false,
    telegramChatId: '',
    notifyOnTrade: true,
    notifyOnSignal: false,
    notifyOnStopLoss: true,
    notifyOnTakeProfit: true
  });
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  useEffect(() => {
    // In a real app, we would fetch the user's settings from the API
    // For now, we'll use placeholder data
    if (user) {
      // Simulating fetching user settings
      setTimeout(() => {
        // This would be replaced with actual API data
      }, 500);
    }
  }, [user]);
  
  const handleTabChange = (event, newValue) => {
    setTab(newValue);
    setError('');
    setSuccess('');
  };
  
  const handleTradingSettingsChange = (e) => {
    const { name, value } = e.target;
    setTradingSettings(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSliderChange = (name) => (e, value) => {
    setTradingSettings(prev => ({ ...prev, [name]: value }));
  };
  
  const handleNotificationSettingsChange = (e) => {
    const { name, value, checked } = e.target;
    const newValue = e.target.type === 'checkbox' ? checked : value;
    setNotificationSettings(prev => ({ ...prev, [name]: newValue }));
  };
  
  const handleTradingSettingsSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // In a real app, we would call the API to update the settings
      await updateSettings({ type: 'trading', settings: tradingSettings });
      setSuccess('Trading settings updated successfully');
    } catch (err) {
      setError(err.message || 'Failed to update trading settings');
    } finally {
      setLoading(false);
    }
  };
  
  const handleNotificationSettingsSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // In a real app, we would call the API to update the settings
      await updateSettings({ type: 'notifications', settings: notificationSettings });
      setSuccess('Notification settings updated successfully');
    } catch (err) {
      setError(err.message || 'Failed to update notification settings');
    } finally {
      setLoading(false);
    }
  };
  
  if (!user) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', py: 4 }}>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h4" gutterBottom>Settings</Typography>
        
        <Tabs value={tab} onChange={handleTabChange} sx={{ mb: 3 }}>
          <Tab label="Trading Parameters" />
          <Tab label="Notifications" />
          <Tab label="API Keys" />
        </Tabs>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        {tab === 0 && (
          <Box component="form" onSubmit={handleTradingSettingsSubmit}>
            <Typography variant="h6" gutterBottom>Risk Management</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Maximum Daily Loss (%)</Typography>
                <Slider
                  name="maxDailyLoss"
                  value={tradingSettings.maxDailyLoss}
                  onChange={handleSliderChange('maxDailyLoss')}
                  valueLabelDisplay="auto"
                  step={0.5}
                  marks
                  min={1}
                  max={20}
                />
                <Typography variant="body2" color="text.secondary">
                  Stop trading if daily loss exceeds {tradingSettings.maxDailyLoss}% of account balance
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Maximum Trade Size (%)</Typography>
                <Slider
                  name="maxTradeSize"
                  value={tradingSettings.maxTradeSize}
                  onChange={handleSliderChange('maxTradeSize')}
                  valueLabelDisplay="auto"
                  step={1}
                  marks
                  min={1}
                  max={50}
                />
                <Typography variant="body2" color="text.secondary">
                  Maximum size of a single trade as {tradingSettings.maxTradeSize}% of account balance
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Maximum Open Positions</Typography>
                <Slider
                  name="maxOpenPositions"
                  value={tradingSettings.maxOpenPositions}
                  onChange={handleSliderChange('maxOpenPositions')}
                  valueLabelDisplay="auto"
                  step={1}
                  marks
                  min={1}
                  max={10}
                />
                <Typography variant="body2" color="text.secondary">
                  Maximum number of open positions at any time
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Maximum Trades Per Day</Typography>
                <Slider
                  name="maxTradesPerDay"
                  value={tradingSettings.maxTradesPerDay}
                  onChange={handleSliderChange('maxTradesPerDay')}
                  valueLabelDisplay="auto"
                  step={1}
                  marks
                  min={1}
                  max={50}
                />
                <Typography variant="body2" color="text.secondary">
                  Maximum number of trades allowed per day
                </Typography>
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>Default Trade Parameters</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Default Take Profit (%)</Typography>
                <Slider
                  name="defaultTakeProfit"
                  value={tradingSettings.defaultTakeProfit}
                  onChange={handleSliderChange('defaultTakeProfit')}
                  valueLabelDisplay="auto"
                  step={0.1}
                  marks
                  min={0.5}
                  max={10}
                />
                <Typography variant="body2" color="text.secondary">
                  Default take profit percentage for new trades
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>Default Stop Loss (%)</Typography>
                <Slider
                  name="defaultStopLoss"
                  value={tradingSettings.defaultStopLoss}
                  onChange={handleSliderChange('defaultStopLoss')}
                  valueLabelDisplay="auto"
                  step={0.1}
                  marks
                  min={0.5}
                  max={5}
                />
                <Typography variant="body2" color="text.secondary">
                  Default stop loss percentage for new trades
                </Typography>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Trading Settings'}
              </Button>
            </Box>
          </Box>
        )}
        
        {tab === 1 && (
          <Box component="form" onSubmit={handleNotificationSettingsSubmit}>
            <Typography variant="h6" gutterBottom>Notification Channels</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.emailNotifications}
                      onChange={handleNotificationSettingsChange}
                      name="emailNotifications"
                      color="primary"
                    />
                  }
                  label="Email Notifications"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.telegramNotifications}
                      onChange={handleNotificationSettingsChange}
                      name="telegramNotifications"
                      color="primary"
                    />
                  }
                  label="Telegram Notifications"
                />
              </Grid>
              
              {notificationSettings.telegramNotifications && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Telegram Chat ID"
                    name="telegramChatId"
                    value={notificationSettings.telegramChatId}
                    onChange={handleNotificationSettingsChange}
                    helperText="Enter your Telegram Chat ID to receive notifications"
                  />
                </Grid>
              )}
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>Notification Events</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.notifyOnTrade}
                      onChange={handleNotificationSettingsChange}
                      name="notifyOnTrade"
                      color="primary"
                    />
                  }
                  label="Notify on Trade Execution"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.notifyOnSignal}
                      onChange={handleNotificationSettingsChange}
                      name="notifyOnSignal"
                      color="primary"
                    />
                  }
                  label="Notify on Signal Generation"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.notifyOnStopLoss}
                      onChange={handleNotificationSettingsChange}
                      name="notifyOnStopLoss"
                      color="primary"
                    />
                  }
                  label="Notify on Stop Loss Triggered"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notificationSettings.notifyOnTakeProfit}
                      onChange={handleNotificationSettingsChange}
                      name="notifyOnTakeProfit"
                      color="primary"
                    />
                  }
                  label="Notify on Take Profit Triggered"
                />
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Notification Settings'}
              </Button>
            </Box>
          </Box>
        )}
        
        {tab === 2 && (
          <Box component="form">
            <Typography variant="h6" gutterBottom>Exchange API Keys</Typography>
            <Alert severity="info" sx={{ mb: 3 }}>
              API keys are stored encrypted and are only used to connect to your exchange account.
              We never withdraw funds without your explicit permission.
            </Alert>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Exchange</InputLabel>
                  <Select
                    value="binance"
                    label="Exchange"
                  >
                    <MenuItem value="binance">Binance</MenuItem>
                    <MenuItem value="binance_us">Binance US</MenuItem>
                    <MenuItem value="coinbase">Coinbase Pro</MenuItem>
                    <MenuItem value="kucoin">KuCoin</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="API Key"
                  type="password"
                  placeholder="Enter your API key"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="API Secret"
                  type="password"
                  placeholder="Enter your API secret"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Alert severity="warning">
                  Important: Make sure your API key has trading permissions but NOT withdrawal permissions for security.
                </Alert>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
              >
                Save API Keys
              </Button>
            </Box>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Settings;