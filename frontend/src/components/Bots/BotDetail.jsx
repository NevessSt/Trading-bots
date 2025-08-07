import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  Tabs,
  Tab,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as BackIcon,
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import useTradingStore from '../../stores/useTradingStore';
import PerformanceChart from '../Dashboard/PerformanceChart';
import RecentTradesList from '../Dashboard/RecentTradesList';

const BotDetail = () => {
  const { botId } = useParams();
  const navigate = useNavigate();
  
  const { 
    bots, 
    activeBots, 
    trades, 
    performance, 
    isLoading, 
    error, 
    fetchBots, 
    fetchActiveBots, 
    fetchTrades, 
    fetchPerformance, 
    startBot, 
    stopBot, 
    deleteBot 
  } = useTradingStore();

  const [bot, setBot] = useState(null);
  const [timeframe, setTimeframe] = useState('30d');
  const [tabValue, setTabValue] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  useEffect(() => {
    // Fetch bots if not already loaded
    if (bots.length === 0) {
      fetchBots();
    } else {
      // Find the bot in the existing list
      const foundBot = bots.find(b => b.id === botId);
      setBot(foundBot || null);
    }

    // Fetch active bots to determine status
    fetchActiveBots();
    
    // Fetch bot-specific performance data
    fetchPerformance(timeframe, botId);
    
    // Fetch bot-specific trades
    fetchTrades(1, 10, { botId });
  }, [botId, bots, fetchBots, fetchActiveBots, fetchPerformance, fetchTrades, timeframe]);

  // Update bot when bots list changes
  useEffect(() => {
    const foundBot = bots.find(b => b.id === botId);
    setBot(foundBot || null);
  }, [bots, botId]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
    fetchPerformance(newTimeframe, botId);
  };

  const isBotActive = () => {
    return activeBots.some(b => b.id === botId);
  };

  const handleStartBot = async () => {
    setActionInProgress(true);
    setActionError(null);
    setActionSuccess(null);
    
    try {
      const result = await startBot(botId);
      if (result.success) {
        setActionSuccess('Bot started successfully');
      } else {
        setActionError(result.error || 'Failed to start bot');
      }
    } catch (error) {
      setActionError('An unexpected error occurred');
      console.error('Error starting bot:', error);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleStopBot = async () => {
    setActionInProgress(true);
    setActionError(null);
    setActionSuccess(null);
    
    try {
      const result = await stopBot(botId);
      if (result.success) {
        setActionSuccess('Bot stopped successfully');
      } else {
        setActionError(result.error || 'Failed to stop bot');
      }
    } catch (error) {
      setActionError('An unexpected error occurred');
      console.error('Error stopping bot:', error);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleEditBot = () => {
    navigate(`/bots/${botId}/edit`);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const handleDeleteConfirm = async () => {
    setActionInProgress(true);
    setActionError(null);
    setActionSuccess(null);
    
    try {
      const result = await deleteBot(botId);
      if (result.success) {
        setActionSuccess(`Bot "${bot.name}" deleted successfully`);
        // Redirect after a short delay
        setTimeout(() => {
          navigate('/bots');
        }, 1500);
      } else {
        setActionError(result.error || 'Failed to delete bot');
      }
    } catch (error) {
      setActionError('An unexpected error occurred');
      console.error('Error deleting bot:', error);
    } finally {
      setActionInProgress(false);
      setDeleteDialogOpen(false);
    }
  };

  const formatProfitLoss = (value) => {
    if (value === undefined || value === null) return 'N/A';
    
    const isPositive = value >= 0;
    return (
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {isPositive ? (
          <ProfitIcon fontSize="small" color="success" sx={{ mr: 0.5 }} />
        ) : (
          <LossIcon fontSize="small" color="error" sx={{ mr: 0.5 }} />
        )}
        <Typography 
          variant="body2" 
          color={isPositive ? 'success.main' : 'error.main'}
          sx={{ fontWeight: 'bold' }}
        >
          {isPositive ? '+' : ''}{value.toFixed(2)}%
        </Typography>
      </Box>
    );
  };

  if (isLoading && !bot) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!bot && !isLoading) {
    return (
      <Box>
        <Button 
          startIcon={<BackIcon />} 
          onClick={() => navigate('/bots')}
          sx={{ mb: 2 }}
        >
          Back to Bots
        </Button>
        
        <Alert severity="error">
          Bot not found. It may have been deleted or you don't have access to it.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton 
          onClick={() => navigate('/bots')} 
          sx={{ mr: 1 }}
        >
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          {bot?.name}
        </Typography>
        <Chip 
          label={isBotActive() ? 'Active' : 'Inactive'} 
          color={isBotActive() ? 'success' : 'default'} 
          size="small" 
          sx={{ ml: 2 }}
        />
      </Box>

      {actionError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setActionError(null)}>
          {actionError}
        </Alert>
      )}

      {actionSuccess && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setActionSuccess(null)}>
          {actionSuccess}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Bot Info Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Bot Information" />
            <Divider />
            <CardContent>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Trading Pair" 
                    secondary={bot?.symbol} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Strategy" 
                    secondary={bot?.strategy?.name} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Time Interval" 
                    secondary={bot?.interval} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Trading Amount" 
                    secondary={`$${bot?.amount.toFixed(2)}`} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Take Profit" 
                    secondary={`${bot?.take_profit}%`} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Stop Loss" 
                    secondary={`${bot?.stop_loss}%`} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Created" 
                    secondary={new Date(bot?.created_at).toLocaleString()} 
                  />
                </ListItem>
                {bot?.last_active && (
                  <ListItem>
                    <ListItemText 
                      primary="Last Active" 
                      secondary={new Date(bot?.last_active).toLocaleString()} 
                    />
                  </ListItem>
                )}
              </List>

              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                Strategy Parameters
              </Typography>
              
              <List dense>
                {bot?.strategy_params && Object.entries(bot.strategy_params).map(([key, value]) => (
                  <ListItem key={key}>
                    <ListItemText 
                      primary={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                      secondary={value} 
                    />
                  </ListItem>
                ))}
              </List>

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                {isBotActive() ? (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={handleStopBot}
                    disabled={actionInProgress}
                    fullWidth
                  >
                    {actionInProgress ? 'Stopping...' : 'Stop Bot'}
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<StartIcon />}
                    onClick={handleStartBot}
                    disabled={actionInProgress}
                    fullWidth
                  >
                    {actionInProgress ? 'Starting...' : 'Start Bot'}
                  </Button>
                )}
              </Box>
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  startIcon={<EditIcon />}
                  onClick={handleEditBot}
                  sx={{ flex: 1, mr: 1 }}
                >
                  Edit
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={handleDeleteClick}
                  sx={{ flex: 1, ml: 1 }}
                >
                  Delete
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance and Trades */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ mb: 3 }}>
            <Box sx={{ p: 2 }}>
              <PerformanceChart 
                performance={performance} 
                isLoading={isLoading} 
                timeframe={timeframe}
                onTimeframeChange={handleTimeframeChange}
              />
            </Box>
          </Paper>

          <Paper>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange} 
                aria-label="bot details tabs"
              >
                <Tab label="Recent Trades" id="tab-0" />
                <Tab label="Bot Logs" id="tab-1" />
                <Tab label="Settings" id="tab-2" />
              </Tabs>
            </Box>
            
            <Box sx={{ p: 2 }}>
              {tabValue === 0 && (
                <RecentTradesList 
                  trades={trades} 
                  isLoading={isLoading} 
                />
              )}
              
              {tabValue === 1 && (
                <Box sx={{ p: 2 }}>
                  <Typography variant="body1" color="text.secondary" align="center">
                    Bot logs will be displayed here
                  </Typography>
                </Box>
              )}
              
              {tabValue === 2 && (
                <Box sx={{ p: 2 }}>
                  <Typography variant="body1" color="text.secondary" align="center">
                    Additional bot settings will be displayed here
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Trading Bot</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the bot "{bot?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={actionInProgress}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            disabled={actionInProgress}
            startIcon={actionInProgress ? <CircularProgress size={20} /> : null}
          >
            {actionInProgress ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BotDetail;