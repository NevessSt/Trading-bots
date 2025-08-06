import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
  Button,
  CircularProgress
} from '@mui/material';
import { 
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon,
  ArrowUpward as BuyIcon,
  ArrowDownward as SellIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';

const RecentTradesList = ({ trades, isLoading }) => {
  const navigate = useNavigate();

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, 'MMM dd, yyyy HH:mm');
  };

  const formatProfit = (profit) => {
    const isPositive = profit >= 0;
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
          {isPositive ? '+' : ''}{profit.toFixed(2)}%
        </Typography>
      </Box>
    );
  };

  const getTradeTypeChip = (type) => {
    return type === 'buy' ? (
      <Chip 
        icon={<BuyIcon />} 
        label="BUY" 
        size="small" 
        color="success" 
        variant="outlined"
      />
    ) : (
      <Chip 
        icon={<SellIcon />} 
        label="SELL" 
        size="small" 
        color="error" 
        variant="outlined"
      />
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
        Recent Trades
      </Typography>
      
      {trades.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 3 }}>
          <Typography variant="body1" color="text.secondary">
            No recent trades
          </Typography>
        </Box>
      ) : (
        <List sx={{ width: '100%' }}>
          {trades.map((trade, index) => (
            <React.Fragment key={trade.id}>
              {index > 0 && <Divider component="li" />}
              <ListItem sx={{ py: 1.5 }}>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="subtitle1">
                        {trade.symbol}
                      </Typography>
                      <Box sx={{ ml: 1 }}>
                        {getTradeTypeChip(trade.type)}
                      </Box>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', flexDirection: 'column', mt: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(trade.timestamp)}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                          Price: ${trade.price.toFixed(2)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                          Amount: ${trade.amount.toFixed(2)}
                        </Typography>
                        {trade.profit_loss && formatProfit(trade.profit_loss)}
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
      
      {trades.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button 
            variant="text" 
            color="primary"
            onClick={() => navigate('/trades')}
            size="small"
          >
            View All Trades
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default RecentTradesList;