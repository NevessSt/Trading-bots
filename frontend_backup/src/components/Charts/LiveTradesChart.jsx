import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Badge,
  Avatar
} from '@mui/material';
import {
  Search,
  FilterList,
  TrendingUp,
  TrendingDown,
  Refresh,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import { format } from 'date-fns';

const LiveTradesChart = ({ 
  trades = [], 
  onRefresh,
  autoRefresh = true,
  maxDisplayTrades = 50
}) => {
  const [filteredTrades, setFilteredTrades] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, buy, sell, profit, loss
  const [showDetails, setShowDetails] = useState(true);
  const [newTradeCount, setNewTradeCount] = useState(0);

  useEffect(() => {
    let filtered = [...trades];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(trade => 
        trade.symbol?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        trade.bot_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        trade.strategy?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply type filter
    switch (filterType) {
      case 'buy':
        filtered = filtered.filter(trade => trade.side?.toLowerCase() === 'buy');
        break;
      case 'sell':
        filtered = filtered.filter(trade => trade.side?.toLowerCase() === 'sell');
        break;
      case 'profit':
        filtered = filtered.filter(trade => parseFloat(trade.pnl || 0) > 0);
        break;
      case 'loss':
        filtered = filtered.filter(trade => parseFloat(trade.pnl || 0) < 0);
        break;
      default:
        break;
    }

    // Sort by timestamp (newest first) and limit
    filtered = filtered
      .sort((a, b) => new Date(b.timestamp || b.created_at) - new Date(a.timestamp || a.created_at))
      .slice(0, maxDisplayTrades);

    setFilteredTrades(filtered);
  }, [trades, searchTerm, filterType, maxDisplayTrades]);

  useEffect(() => {
    // Count new trades (trades from last 5 minutes)
    const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
    const recentTrades = trades.filter(trade => 
      new Date(trade.timestamp || trade.created_at).getTime() > fiveMinutesAgo
    );
    setNewTradeCount(recentTrades.length);
  }, [trades]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(value || 0);
  };

  const formatTime = (timestamp) => {
    return format(new Date(timestamp), 'HH:mm:ss');
  };

  const formatDate = (timestamp) => {
    return format(new Date(timestamp), 'MMM dd, yyyy');
  };

  const getSideColor = (side) => {
    return side?.toLowerCase() === 'buy' ? 'success' : 'error';
  };

  const getPnLColor = (pnl) => {
    const value = parseFloat(pnl || 0);
    if (value > 0) return 'success';
    if (value < 0) return 'error';
    return 'default';
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'filled':
      case 'completed':
        return 'success';
      case 'pending':
      case 'partial':
        return 'warning';
      case 'cancelled':
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ 
      border: 1,
      borderColor: 'divider',
      borderRadius: 1,
      bgcolor: 'background.paper'
    }}>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider' 
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6" component="h3">
            Live Trades
          </Typography>
          {newTradeCount > 0 && (
            <Badge badgeContent={newTradeCount} color="primary">
              <Chip 
                label="New" 
                color="primary" 
                size="small" 
                variant="outlined"
              />
            </Badge>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title={showDetails ? 'Hide Details' : 'Show Details'}>
            <IconButton onClick={() => setShowDetails(!showDetails)} size="small">
              {showDetails ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Refresh">
            <IconButton onClick={onRefresh} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Filters */}
      <Box sx={{ 
        display: 'flex', 
        gap: 2, 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider',
        flexWrap: 'wrap'
      }}>
        <TextField
          size="small"
          placeholder="Search symbol, bot, strategy..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 250 }}
        />
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Filter</InputLabel>
          <Select
            value={filterType}
            label="Filter"
            onChange={(e) => setFilterType(e.target.value)}
            startAdornment={<FilterList fontSize="small" sx={{ mr: 1 }} />}
          >
            <MenuItem value="all">All Trades</MenuItem>
            <MenuItem value="buy">Buy Orders</MenuItem>
            <MenuItem value="sell">Sell Orders</MenuItem>
            <MenuItem value="profit">Profitable</MenuItem>
            <MenuItem value="loss">Loss Making</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Trades Table */}
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell>Side</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Value</TableCell>
              {showDetails && (
                <>
                  <TableCell>Bot</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">P&L</TableCell>
                </>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTrades.length === 0 ? (
              <TableRow>
                <TableCell colSpan={showDetails ? 9 : 6} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No trades found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredTrades.map((trade, index) => {
                const isRecent = Date.now() - new Date(trade.timestamp || trade.created_at).getTime() < 60000; // 1 minute
                
                return (
                  <TableRow 
                    key={trade.id || index}
                    sx={{ 
                      bgcolor: isRecent ? 'action.hover' : 'inherit',
                      '&:hover': { bgcolor: 'action.selected' }
                    }}
                  >
                    <TableCell>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {formatTime(trade.timestamp || trade.created_at)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(trade.timestamp || trade.created_at)}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>
                          {trade.symbol?.substring(0, 2) || 'BT'}
                        </Avatar>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {trade.symbol || 'N/A'}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Chip
                        label={trade.side?.toUpperCase() || 'N/A'}
                        color={getSideColor(trade.side)}
                        size="small"
                        icon={trade.side?.toLowerCase() === 'buy' ? <TrendingUp /> : <TrendingDown />}
                      />
                    </TableCell>
                    
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {formatCurrency(trade.price)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {parseFloat(trade.quantity || 0).toFixed(6)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'medium' }}>
                        {formatCurrency((trade.price || 0) * (trade.quantity || 0))}
                      </Typography>
                    </TableCell>
                    
                    {showDetails && (
                      <>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {trade.bot_name || trade.strategy || 'Manual'}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Chip
                            label={trade.status || 'Filled'}
                            color={getStatusColor(trade.status)}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontFamily: 'monospace',
                              fontWeight: 'medium',
                              color: getPnLColor(trade.pnl) === 'success' ? 'success.main' : 
                                     getPnLColor(trade.pnl) === 'error' ? 'error.main' : 'text.primary'
                            }}
                          >
                            {trade.pnl ? formatCurrency(trade.pnl) : '-'}
                          </Typography>
                        </TableCell>
                      </>
                    )}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Footer Stats */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        p: 2, 
        bgcolor: 'grey.50',
        borderTop: 1,
        borderColor: 'divider'
      }}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredTrades.length} of {trades.length} trades
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {autoRefresh && (
            <Chip 
              label="Auto-refresh ON" 
              color="success" 
              size="small" 
              variant="outlined"
            />
          )}
          <Chip 
            label={`${newTradeCount} new`} 
            color="primary" 
            size="small" 
            variant="outlined"
          />
        </Box>
      </Box>
    </Box>
  );
};

export default LiveTradesChart;