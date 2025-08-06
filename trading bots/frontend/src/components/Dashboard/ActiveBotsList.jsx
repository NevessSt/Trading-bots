import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Divider,
  Button,
  CircularProgress,
  Tooltip
} from '@mui/material';
import { 
  Stop as StopIcon,
  Visibility as ViewIcon,
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import useTradingStore from '../../stores/useTradingStore';

const ActiveBotsList = ({ bots, isLoading }) => {
  const navigate = useNavigate();
  const { stopBot } = useTradingStore();

  const handleStopBot = async (botId, event) => {
    event.stopPropagation();
    await stopBot(botId);
  };

  const handleViewBot = (botId) => {
    navigate(`/bots/${botId}`);
  };

  const formatProfitLoss = (value) => {
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

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress size={30} />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" component="h2" gutterBottom>
        Active Trading Bots
      </Typography>
      
      {bots.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 3 }}>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            No active bots running
          </Typography>
          <Button 
            variant="outlined" 
            color="primary"
            onClick={() => navigate('/bots')}
            sx={{ mt: 1 }}
          >
            View All Bots
          </Button>
        </Box>
      ) : (
        <List sx={{ width: '100%' }}>
          {bots.map((bot, index) => (
            <React.Fragment key={bot.id}>
              {index > 0 && <Divider component="li" />}
              <ListItem 
                button 
                onClick={() => handleViewBot(bot.id)}
                sx={{ py: 1.5 }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="subtitle1">
                        {bot.name}
                      </Typography>
                      <Chip 
                        label={bot.symbol} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', flexDirection: 'column', mt: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                        Strategy: {bot.strategy.name}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                          Amount: ${bot.amount.toFixed(2)}
                        </Typography>
                        {formatProfitLoss(bot.performance?.total_profit_loss || 0)}
                      </Box>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Box sx={{ display: 'flex' }}>
                    <Tooltip title="View Details">
                      <IconButton 
                        edge="end" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewBot(bot.id);
                        }}
                        size="small"
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Stop Bot">
                      <IconButton 
                        edge="end" 
                        onClick={(e) => handleStopBot(bot.id, e)}
                        color="error"
                        size="small"
                        sx={{ ml: 1 }}
                      >
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </ListItemSecondaryAction>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
      
      {bots.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button 
            variant="text" 
            color="primary"
            onClick={() => navigate('/bots')}
            size="small"
          >
            View All Bots
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default ActiveBotsList;