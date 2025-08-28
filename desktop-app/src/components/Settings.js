import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Button,
  Divider,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
} from '@mui/material';
import {
  Save,
  Restore,
  Security,
  Notifications,
  TrendingUp,
  Settings as SettingsIcon,
  Delete,
  Add,
  Edit,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';

const Settings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [settings, setSettings] = useState({
    // Trading Settings
    defaultRiskPercent: 2,
    maxPositions: 5,
    stopLossPercent: 3,
    takeProfitPercent: 6,
    enableAutoTrading: true,
    tradingMode: 'conservative',
    
    // API Settings
    exchanges: [
      { name: 'Binance', apiKey: 'your_api_key', secret: '***hidden***', enabled: true },
      { name: 'Coinbase Pro', apiKey: '', secret: '', enabled: false }
    ],
    
    // Notification Settings
    enableNotifications: true,
    tradeNotifications: true,
    profitNotifications: true,
    lossNotifications: true,
    systemNotifications: true,
    emailNotifications: false,
    
    // UI Settings
    theme: 'dark',
    language: 'en',
    currency: 'USD',
    refreshInterval: 5,
    soundEnabled: true,
    
    // Security Settings
    enableTwoFactor: false,
    sessionTimeout: 30,
    requirePasswordForTrades: false,
    
    // Advanced Settings
    logLevel: 'info',
    maxLogFiles: 10,
    enableTelemetry: true,
    autoUpdate: true
  });
  
  const [showApiDialog, setShowApiDialog] = useState(false);
  const [editingExchange, setEditingExchange] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // In a real app, this would load from the backend or local storage
      // For now, we'll use the default settings
      console.log('Settings loaded');
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSettingChange = (category, field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
    setUnsavedChanges(true);
  };

  const handleExchangeChange = (index, field, value) => {
    const newExchanges = [...settings.exchanges];
    newExchanges[index] = { ...newExchanges[index], [field]: value };
    setSettings(prev => ({ ...prev, exchanges: newExchanges }));
    setUnsavedChanges(true);
  };

  const saveSettings = async () => {
    try {
      // In a real app, this would save to the backend
      console.log('Saving settings:', settings);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setUnsavedChanges(false);
      setSnackbar({ 
        open: true, 
        message: 'Settings saved successfully!', 
        severity: 'success' 
      });
    } catch (error) {
      setSnackbar({ 
        open: true, 
        message: 'Failed to save settings', 
        severity: 'error' 
      });
    }
  };

  const resetSettings = () => {
    // Reset to default values
    setSettings({
      defaultRiskPercent: 2,
      maxPositions: 5,
      stopLossPercent: 3,
      takeProfitPercent: 6,
      enableAutoTrading: true,
      tradingMode: 'conservative',
      exchanges: [
        { name: 'Binance', apiKey: '', secret: '', enabled: false },
        { name: 'Coinbase Pro', apiKey: '', secret: '', enabled: false }
      ],
      enableNotifications: true,
      tradeNotifications: true,
      profitNotifications: true,
      lossNotifications: true,
      systemNotifications: true,
      emailNotifications: false,
      theme: 'dark',
      language: 'en',
      currency: 'USD',
      refreshInterval: 5,
      soundEnabled: true,
      enableTwoFactor: false,
      sessionTimeout: 30,
      requirePasswordForTrades: false,
      logLevel: 'info',
      maxLogFiles: 10,
      enableTelemetry: true,
      autoUpdate: true
    });
    setUnsavedChanges(true);
  };

  const handleEditExchange = (exchange, index) => {
    setEditingExchange({ ...exchange, index });
    setShowApiDialog(true);
  };

  const handleSaveExchange = () => {
    if (editingExchange) {
      handleExchangeChange(editingExchange.index, 'apiKey', editingExchange.apiKey);
      handleExchangeChange(editingExchange.index, 'secret', editingExchange.secret);
      handleExchangeChange(editingExchange.index, 'enabled', editingExchange.enabled);
    }
    setShowApiDialog(false);
    setEditingExchange(null);
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 300 }}>
          Settings
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button 
            variant="outlined" 
            startIcon={<Restore />} 
            onClick={resetSettings}
          >
            Reset
          </Button>
          <Button 
            variant="contained" 
            startIcon={<Save />} 
            onClick={saveSettings}
            disabled={!unsavedChanges}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      {unsavedChanges && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You have unsaved changes. Don't forget to save your settings.
        </Alert>
      )}

      {/* Settings Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<TrendingUp />} label="Trading" />
          <Tab icon={<Security />} label="API & Security" />
          <Tab icon={<Notifications />} label="Notifications" />
          <Tab icon={<SettingsIcon />} label="General" />
        </Tabs>

        {/* Trading Settings */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Risk Management</Typography>
                  
                  <Box sx={{ mb: 3 }}>
                    <Typography gutterBottom>Default Risk per Trade (%)</Typography>
                    <Slider
                      value={settings.defaultRiskPercent}
                      onChange={(e, value) => handleSettingChange('trading', 'defaultRiskPercent', value)}
                      min={0.1}
                      max={10}
                      step={0.1}
                      marks={[
                        { value: 1, label: '1%' },
                        { value: 5, label: '5%' },
                        { value: 10, label: '10%' }
                      ]}
                      valueLabelDisplay="on"
                    />
                  </Box>

                  <TextField
                    fullWidth
                    label="Maximum Positions"
                    type="number"
                    value={settings.maxPositions}
                    onChange={(e) => handleSettingChange('trading', 'maxPositions', parseInt(e.target.value))}
                    sx={{ mb: 2 }}
                  />

                  <Box sx={{ mb: 3 }}>
                    <Typography gutterBottom>Stop Loss (%)</Typography>
                    <Slider
                      value={settings.stopLossPercent}
                      onChange={(e, value) => handleSettingChange('trading', 'stopLossPercent', value)}
                      min={0.5}
                      max={20}
                      step={0.5}
                      marks={[
                        { value: 2, label: '2%' },
                        { value: 10, label: '10%' },
                        { value: 20, label: '20%' }
                      ]}
                      valueLabelDisplay="on"
                    />
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Typography gutterBottom>Take Profit (%)</Typography>
                    <Slider
                      value={settings.takeProfitPercent}
                      onChange={(e, value) => handleSettingChange('trading', 'takeProfitPercent', value)}
                      min={1}
                      max={50}
                      step={1}
                      marks={[
                        { value: 5, label: '5%' },
                        { value: 25, label: '25%' },
                        { value: 50, label: '50%' }
                      ]}
                      valueLabelDisplay="on"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Trading Preferences</Typography>
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enableAutoTrading}
                        onChange={(e) => handleSettingChange('trading', 'enableAutoTrading', e.target.checked)}
                      />
                    }
                    label="Enable Auto Trading"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Trading Mode</InputLabel>
                    <Select
                      value={settings.tradingMode}
                      label="Trading Mode"
                      onChange={(e) => handleSettingChange('trading', 'tradingMode', e.target.value)}
                    >
                      <MenuItem value="conservative">Conservative</MenuItem>
                      <MenuItem value="moderate">Moderate</MenuItem>
                      <MenuItem value="aggressive">Aggressive</MenuItem>
                    </Select>
                  </FormControl>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* API & Security Settings */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Exchange API Keys</Typography>
                  <List>
                    {settings.exchanges.map((exchange, index) => (
                      <ListItem key={index} divider>
                        <ListItemText
                          primary={exchange.name}
                          secondary={exchange.enabled ? 'Connected' : 'Not configured'}
                        />
                        <ListItemSecondaryAction>
                          <IconButton 
                            edge="end" 
                            onClick={() => handleEditExchange(exchange, index)}
                          >
                            <Edit />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Security</Typography>
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enableTwoFactor}
                        onChange={(e) => handleSettingChange('security', 'enableTwoFactor', e.target.checked)}
                      />
                    }
                    label="Enable Two-Factor Authentication"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.requirePasswordForTrades}
                        onChange={(e) => handleSettingChange('security', 'requirePasswordForTrades', e.target.checked)}
                      />
                    }
                    label="Require Password for Trades"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <TextField
                    fullWidth
                    label="Session Timeout (minutes)"
                    type="number"
                    value={settings.sessionTimeout}
                    onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notification Settings */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Push Notifications</Typography>
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enableNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'enableNotifications', e.target.checked)}
                      />
                    }
                    label="Enable Notifications"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.tradeNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'tradeNotifications', e.target.checked)}
                        disabled={!settings.enableNotifications}
                      />
                    }
                    label="Trade Notifications"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.profitNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'profitNotifications', e.target.checked)}
                        disabled={!settings.enableNotifications}
                      />
                    }
                    label="Profit Notifications"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.lossNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'lossNotifications', e.target.checked)}
                        disabled={!settings.enableNotifications}
                      />
                    }
                    label="Loss Notifications"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.systemNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'systemNotifications', e.target.checked)}
                        disabled={!settings.enableNotifications}
                      />
                    }
                    label="System Notifications"
                    sx={{ mb: 2, display: 'block' }}
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Email Notifications</Typography>
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.emailNotifications}
                        onChange={(e) => handleSettingChange('notifications', 'emailNotifications', e.target.checked)}
                      />
                    }
                    label="Enable Email Notifications"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  {settings.emailNotifications && (
                    <TextField
                      fullWidth
                      label="Email Address"
                      type="email"
                      placeholder="your@email.com"
                    />
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* General Settings */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Interface</Typography>
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Theme</InputLabel>
                    <Select
                      value={settings.theme}
                      label="Theme"
                      onChange={(e) => handleSettingChange('ui', 'theme', e.target.value)}
                    >
                      <MenuItem value="dark">Dark</MenuItem>
                      <MenuItem value="light">Light</MenuItem>
                      <MenuItem value="auto">Auto</MenuItem>
                    </Select>
                  </FormControl>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={settings.language}
                      label="Language"
                      onChange={(e) => handleSettingChange('ui', 'language', e.target.value)}
                    >
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="es">Español</MenuItem>
                      <MenuItem value="fr">Français</MenuItem>
                      <MenuItem value="de">Deutsch</MenuItem>
                    </Select>
                  </FormControl>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Currency</InputLabel>
                    <Select
                      value={settings.currency}
                      label="Currency"
                      onChange={(e) => handleSettingChange('ui', 'currency', e.target.value)}
                    >
                      <MenuItem value="USD">USD</MenuItem>
                      <MenuItem value="EUR">EUR</MenuItem>
                      <MenuItem value="GBP">GBP</MenuItem>
                      <MenuItem value="JPY">JPY</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField
                    fullWidth
                    label="Refresh Interval (seconds)"
                    type="number"
                    value={settings.refreshInterval}
                    onChange={(e) => handleSettingChange('ui', 'refreshInterval', parseInt(e.target.value))}
                    sx={{ mb: 2 }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.soundEnabled}
                        onChange={(e) => handleSettingChange('ui', 'soundEnabled', e.target.checked)}
                      />
                    }
                    label="Enable Sound Effects"
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>Advanced</Typography>
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Log Level</InputLabel>
                    <Select
                      value={settings.logLevel}
                      label="Log Level"
                      onChange={(e) => handleSettingChange('advanced', 'logLevel', e.target.value)}
                    >
                      <MenuItem value="error">Error</MenuItem>
                      <MenuItem value="warn">Warning</MenuItem>
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="debug">Debug</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField
                    fullWidth
                    label="Max Log Files"
                    type="number"
                    value={settings.maxLogFiles}
                    onChange={(e) => handleSettingChange('advanced', 'maxLogFiles', parseInt(e.target.value))}
                    sx={{ mb: 2 }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enableTelemetry}
                        onChange={(e) => handleSettingChange('advanced', 'enableTelemetry', e.target.checked)}
                      />
                    }
                    label="Enable Telemetry"
                    sx={{ mb: 2, display: 'block' }}
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.autoUpdate}
                        onChange={(e) => handleSettingChange('advanced', 'autoUpdate', e.target.checked)}
                      />
                    }
                    label="Auto Update"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* API Key Dialog */}
      <Dialog open={showApiDialog} onClose={() => setShowApiDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Configure {editingExchange?.name} API
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="API Key"
            value={editingExchange?.apiKey || ''}
            onChange={(e) => setEditingExchange(prev => ({ ...prev, apiKey: e.target.value }))}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            fullWidth
            label="Secret Key"
            type={showPassword ? 'text' : 'password'}
            value={editingExchange?.secret || ''}
            onChange={(e) => setEditingExchange(prev => ({ ...prev, secret: e.target.value }))}
            InputProps={{
              endAdornment: (
                <IconButton onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              )
            }}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={editingExchange?.enabled || false}
                onChange={(e) => setEditingExchange(prev => ({ ...prev, enabled: e.target.checked }))}
              />
            }
            label="Enable this exchange"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowApiDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveExchange} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;