import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Alert,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import useTradingStore from '../../stores/useTradingStore';

const BotList = () => {
  const navigate = useNavigate();
  const { 
    bots, 
    activeBots, 
    isLoading, 
    error, 
    fetchBots, 
    fetchActiveBots, 
    startBot, 
    stopBot, 
    deleteBot 
  } = useTradingStore();

  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedBot, setSelectedBot] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  useEffect(() => {
    fetchBots();
    fetchActiveBots();
  }, [fetchBots, fetchActiveBots]);

  const handleMenuOpen = (event, bot) => {
    setAnchorEl(event.currentTarget);
    setSelectedBot(bot);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleCreateBot = () => {
    navigate('/bots/new');
  };

  const handleViewBot = (botId) => {
    navigate(`/bots/${botId}`);
  };

  const handleEditBot = (botId) => {
    navigate(`/bots/${botId}/edit`);
    handleMenuClose();
  };

  const handleStartBot = async (botId) => {
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
      handleMenuClose();
    }
  };

  const handleStopBot = async (botId) => {
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
      handleMenuClose();
    }
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedBot) return;
    
    setActionInProgress(true);
    setActionError(null);
    setActionSuccess(null);
    
    try {
      const result = await deleteBot(selectedBot.id);
      if (result.success) {
        setActionSuccess(`Bot "${selectedBot.name}" deleted successfully`);
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

  const isBotActive = (botId) => {
    return activeBots.some(bot => bot.id === botId);
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
        >
          {isPositive ? '+' : ''}{value.toFixed(2)}%
        </Typography>
      </Box>
    );
  };

  const getStatusChip = (botId) => {
    const active = isBotActive(botId);
    return (
      <Chip 
        label={active ? 'Active' : 'Inactive'} 
        color={active ? 'success' : 'default'} 
        size="small" 
        variant={active ? 'filled' : 'outlined'}
      />
    );
  };

  if (isLoading && bots.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Trading Bots
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<AddIcon />}
          onClick={handleCreateBot}
        >
          Create New Bot
        </Button>
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

      {bots.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Trading Bots Found
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Create your first trading bot to start automated trading.
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
            onClick={handleCreateBot}
          >
            Create New Bot
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }}>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Symbol</TableCell>
                <TableCell>Strategy</TableCell>
                <TableCell>Interval</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell>Performance</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bots.map((bot) => (
                <TableRow 
                  key={bot.id}
                  hover
                  onClick={() => handleViewBot(bot.id)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell component="th" scope="row">
                    {bot.name}
                  </TableCell>
                  <TableCell>{bot.symbol}</TableCell>
                  <TableCell>{bot.strategy?.name || 'Unknown'}</TableCell>
                  <TableCell>{bot.interval}</TableCell>
                  <TableCell align="right">${bot.amount.toFixed(2)}</TableCell>
                  <TableCell>
                    {formatProfitLoss(bot.performance?.total_profit_loss)}
                  </TableCell>
                  <TableCell>
                    {getStatusChip(bot.id)}
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <Tooltip title="View Details">
                        <IconButton 
                          size="small" 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewBot(bot.id);
                          }}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      
                      {isBotActive(bot.id) ? (
                        <Tooltip title="Stop Bot">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStopBot(bot.id);
                            }}
                            disabled={actionInProgress}
                          >
                            <StopIcon />
                          </IconButton>
                        </Tooltip>
                      ) : (
                        <Tooltip title="Start Bot">
                          <IconButton 
                            size="small" 
                            color="success"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStartBot(bot.id);
                            }}
                            disabled={actionInProgress}
                          >
                            <StartIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      <IconButton 
                        size="small" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMenuOpen(e, bot);
                        }}
                      >
                        <MoreIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Bot Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => selectedBot && handleViewBot(selectedBot.id)}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => selectedBot && handleEditBot(selectedBot.id)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Bot</ListItemText>
        </MenuItem>
        {selectedBot && isBotActive(selectedBot.id) ? (
          <MenuItem onClick={() => selectedBot && handleStopBot(selectedBot.id)}>
            <ListItemIcon>
              <StopIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Stop Bot</ListItemText>
          </MenuItem>
        ) : (
          <MenuItem onClick={() => selectedBot && handleStartBot(selectedBot.id)}>
            <ListItemIcon>
              <StartIcon fontSize="small" color="success" />
            </ListItemIcon>
            <ListItemText>Start Bot</ListItemText>
          </MenuItem>
        )}
        <MenuItem onClick={handleDeleteClick}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete Bot</ListItemText>
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Trading Bot</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the bot "{selectedBot?.name}"? This action cannot be undone.
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

export default BotList;