import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Badge,
  Divider,
  Button,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Grid,
  Paper,
  Tooltip,
} from '@mui/material';
import {
  Notifications,
  TrendingUp,
  TrendingDown,
  Warning,
  Info,
  Error,
  CheckCircle,
  Delete,
  MoreVert,
  Clear,
  Settings,
  FilterList,
  MarkAsUnread,
  Schedule,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filterAnchor, setFilterAnchor] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState({
    trades: true,
    profits: true,
    losses: true,
    system: true,
    warnings: true,
    sound: true,
    desktop: true
  });

  useEffect(() => {
    loadNotifications();
    
    // Simulate real-time notifications
    const interval = setInterval(() => {
      if (Math.random() > 0.8) { // 20% chance every 10 seconds
        addRandomNotification();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const unread = notifications.filter(n => !n.read).length;
    setUnreadCount(unread);
  }, [notifications]);

  const loadNotifications = () => {
    // Mock notification data
    const mockNotifications = [
      {
        id: 'n001',
        type: 'trade',
        title: 'Trade Executed',
        message: 'BUY order for 0.025 BTC at $43,250.00 has been filled',
        timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        read: false,
        priority: 'medium',
        data: { pair: 'BTC/USDT', amount: 0.025, price: 43250 }
      },
      {
        id: 'n002',
        type: 'profit',
        title: 'Profitable Trade Closed',
        message: 'ETH/USDT position closed with +$125.50 profit (+2.34%)',
        timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
        read: false,
        priority: 'high',
        data: { pair: 'ETH/USDT', profit: 125.50, percentage: 2.34 }
      },
      {
        id: 'n003',
        type: 'warning',
        title: 'High Volatility Alert',
        message: 'BTC/USDT showing unusual volatility (+15% in 1 hour)',
        timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
        read: true,
        priority: 'high',
        data: { pair: 'BTC/USDT', change: 15 }
      },
      {
        id: 'n004',
        type: 'loss',
        title: 'Stop Loss Triggered',
        message: 'ADA/USDT position closed with -$45.20 loss (-1.85%)',
        timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
        read: true,
        priority: 'medium',
        data: { pair: 'ADA/USDT', loss: -45.20, percentage: -1.85 }
      },
      {
        id: 'n005',
        type: 'system',
        title: 'Strategy Updated',
        message: 'Momentum Scalping strategy parameters have been updated',
        timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
        read: true,
        priority: 'low',
        data: { strategy: 'Momentum Scalping' }
      },
      {
        id: 'n006',
        type: 'system',
        title: 'Connection Restored',
        message: 'Connection to Binance API has been restored',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        read: true,
        priority: 'medium',
        data: { exchange: 'Binance' }
      }
    ];

    setNotifications(mockNotifications);
  };

  const addRandomNotification = () => {
    const types = ['trade', 'profit', 'loss', 'warning', 'system'];
    const type = types[Math.floor(Math.random() * types.length)];
    
    const messages = {
      trade: [
        'New BUY order for 0.1 ETH at $2,680.00',
        'SELL order for 500 ADA at $0.485 executed',
        'Limit order for SOL/USDT has been placed'
      ],
      profit: [
        'BTC/USDT position closed with +$89.50 profit',
        'Successful scalp on ETH/USDT: +$45.20',
        'Take profit hit on ADA/USDT: +$67.80'
      ],
      loss: [
        'Stop loss triggered on BTC/USDT: -$32.10',
        'ETH/USDT position closed at loss: -$28.50',
        'Risk management activated on SOL/USDT'
      ],
      warning: [
        'High volatility detected on BTC/USDT',
        'Unusual volume spike on ETH/USDT',
        'Market correlation alert: Risk level increased'
      ],
      system: [
        'Strategy performance update available',
        'New market data received',
        'System health check completed'
      ]
    };

    const newNotification = {
      id: `n${Date.now()}`,
      type,
      title: type.charAt(0).toUpperCase() + type.slice(1) + ' Alert',
      message: messages[type][Math.floor(Math.random() * messages[type].length)],
      timestamp: new Date(),
      read: false,
      priority: Math.random() > 0.7 ? 'high' : 'medium'
    };

    setNotifications(prev => [newNotification, ...prev]);

    // Show desktop notification if enabled
    if (notificationSettings.desktop && 'Notification' in window) {
      new Notification(newNotification.title, {
        body: newNotification.message,
        icon: '/icon.png'
      });
    }
  };

  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(n => ({ ...n, read: true }))
    );
  };

  const deleteNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'trade': return <TrendingUp color="primary" />;
      case 'profit': return <TrendingUp color="success" />;
      case 'loss': return <TrendingDown color="error" />;
      case 'warning': return <Warning color="warning" />;
      case 'system': return <Info color="info" />;
      case 'error': return <Error color="error" />;
      default: return <Notifications />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getFilteredNotifications = () => {
    if (selectedFilter === 'all') return notifications;
    if (selectedFilter === 'unread') return notifications.filter(n => !n.read);
    return notifications.filter(n => n.type === selectedFilter);
  };

  const handleSettingChange = (setting, value) => {
    setNotificationSettings(prev => ({ ...prev, [setting]: value }));
  };

  const filteredNotifications = getFilteredNotifications();

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Badge badgeContent={unreadCount} color="error" sx={{ mr: 2 }}>
            <Notifications fontSize="large" />
          </Badge>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 300 }}>
            Notifications
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<FilterList />}
            onClick={(e) => setFilterAnchor(e.currentTarget)}
          >
            Filter
          </Button>
          <Button
            startIcon={<Settings />}
            onClick={() => setSettingsOpen(true)}
          >
            Settings
          </Button>
          <Button
            startIcon={<Clear />}
            onClick={clearAllNotifications}
            color="error"
          >
            Clear All
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {notifications.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Notifications
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="error">
              {unreadCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Unread
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success">
              {notifications.filter(n => n.type === 'profit').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Profit Alerts
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="warning">
              {notifications.filter(n => n.type === 'warning').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Warnings
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      {unreadCount > 0 && (
        <Box sx={{ mb: 2 }}>
          <Button 
            startIcon={<CheckCircle />} 
            onClick={markAllAsRead}
            variant="outlined"
          >
            Mark All as Read ({unreadCount})
          </Button>
        </Box>
      )}

      {/* Notifications List */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {selectedFilter === 'all' ? 'All Notifications' : 
             selectedFilter === 'unread' ? 'Unread Notifications' :
             `${selectedFilter.charAt(0).toUpperCase() + selectedFilter.slice(1)} Notifications`}
            {filteredNotifications.length > 0 && ` (${filteredNotifications.length})`}
          </Typography>
          
          {filteredNotifications.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Notifications sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No notifications found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedFilter === 'unread' ? 
                  'All notifications have been read' :
                  'You\'re all caught up!'}
              </Typography>
            </Box>
          ) : (
            <List>
              {filteredNotifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <ListItem
                    sx={{
                      backgroundColor: notification.read ? 'transparent' : 'action.hover',
                      borderRadius: 1,
                      mb: 1
                    }}
                  >
                    <ListItemIcon>
                      {getNotificationIcon(notification.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography 
                            variant="subtitle2" 
                            sx={{ fontWeight: notification.read ? 'normal' : 'bold' }}
                          >
                            {notification.title}
                          </Typography>
                          <Chip 
                            label={notification.priority} 
                            size="small" 
                            color={getPriorityColor(notification.priority)}
                            variant="outlined"
                          />
                          {!notification.read && (
                            <Chip label="New" size="small" color="primary" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" sx={{ mb: 0.5 }}>
                            {notification.message}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Schedule sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                              {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {!notification.read && (
                          <Tooltip title="Mark as read">
                            <IconButton 
                              size="small" 
                              onClick={() => markAsRead(notification.id)}
                            >
                              <CheckCircle fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Delete">
                          <IconButton 
                            size="small" 
                            onClick={() => deleteNotification(notification.id)}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < filteredNotifications.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Filter Menu */}
      <Menu
        anchorEl={filterAnchor}
        open={Boolean(filterAnchor)}
        onClose={() => setFilterAnchor(null)}
      >
        <MenuItem 
          onClick={() => { setSelectedFilter('all'); setFilterAnchor(null); }}
          selected={selectedFilter === 'all'}
        >
          All Notifications
        </MenuItem>
        <MenuItem 
          onClick={() => { setSelectedFilter('unread'); setFilterAnchor(null); }}
          selected={selectedFilter === 'unread'}
        >
          Unread Only
        </MenuItem>
        <Divider />
        <MenuItem 
          onClick={() => { setSelectedFilter('trade'); setFilterAnchor(null); }}
          selected={selectedFilter === 'trade'}
        >
          Trade Alerts
        </MenuItem>
        <MenuItem 
          onClick={() => { setSelectedFilter('profit'); setFilterAnchor(null); }}
          selected={selectedFilter === 'profit'}
        >
          Profit Alerts
        </MenuItem>
        <MenuItem 
          onClick={() => { setSelectedFilter('loss'); setFilterAnchor(null); }}
          selected={selectedFilter === 'loss'}
        >
          Loss Alerts
        </MenuItem>
        <MenuItem 
          onClick={() => { setSelectedFilter('warning'); setFilterAnchor(null); }}
          selected={selectedFilter === 'warning'}
        >
          Warnings
        </MenuItem>
        <MenuItem 
          onClick={() => { setSelectedFilter('system'); setFilterAnchor(null); }}
          selected={selectedFilter === 'system'}
        >
          System Alerts
        </MenuItem>
      </Menu>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Notification Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>Alert Types</Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.trades}
                  onChange={(e) => handleSettingChange('trades', e.target.checked)}
                />
              }
              label="Trade Notifications"
              sx={{ display: 'block', mb: 1 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.profits}
                  onChange={(e) => handleSettingChange('profits', e.target.checked)}
                />
              }
              label="Profit Notifications"
              sx={{ display: 'block', mb: 1 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.losses}
                  onChange={(e) => handleSettingChange('losses', e.target.checked)}
                />
              }
              label="Loss Notifications"
              sx={{ display: 'block', mb: 1 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.system}
                  onChange={(e) => handleSettingChange('system', e.target.checked)}
                />
              }
              label="System Notifications"
              sx={{ display: 'block', mb: 1 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.warnings}
                  onChange={(e) => handleSettingChange('warnings', e.target.checked)}
                />
              }
              label="Warning Notifications"
              sx={{ display: 'block', mb: 3 }}
            />
            
            <Typography variant="subtitle1" sx={{ mb: 2 }}>Delivery Methods</Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.sound}
                  onChange={(e) => handleSettingChange('sound', e.target.checked)}
                />
              }
              label="Sound Alerts"
              sx={{ display: 'block', mb: 1 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notificationSettings.desktop}
                  onChange={(e) => handleSettingChange('desktop', e.target.checked)}
                />
              }
              label="Desktop Notifications"
              sx={{ display: 'block' }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
          <Button onClick={() => setSettingsOpen(false)} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NotificationCenter;