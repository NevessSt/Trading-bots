import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
} from '@mui/material';
import {
  Visibility,
  TrendingUp,
  TrendingDown,
  FilterList,
  Download,
  Refresh,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

const History = () => {
  const [trades, setTrades] = useState([]);
  const [filteredTrades, setFilteredTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(10);
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    pair: '',
    strategy: '',
    status: '',
    dateFrom: null,
    dateTo: null,
    minPnL: '',
    maxPnL: ''
  });

  useEffect(() => {
    fetchTradeHistory();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [trades, filters]);

  const fetchTradeHistory = async () => {
    try {
      setLoading(true);
      
      // Mock trade history data
      const mockTrades = [
        {
          id: 'T001',
          timestamp: '2024-01-15 14:30:25',
          pair: 'BTC/USDT',
          strategy: 'Momentum Scalping',
          side: 'BUY',
          type: 'MARKET',
          amount: 0.025,
          entryPrice: 43250.00,
          exitPrice: 43890.50,
          pnl: 16.01,
          pnlPercent: 1.48,
          fee: 2.15,
          status: 'CLOSED',
          duration: '4m 32s',
          notes: 'Strong momentum breakout'
        },
        {
          id: 'T002',
          timestamp: '2024-01-15 13:45:12',
          pair: 'ETH/USDT',
          strategy: 'Mean Reversion',
          side: 'SELL',
          type: 'LIMIT',
          amount: 1.5,
          entryPrice: 2680.00,
          exitPrice: 2645.25,
          pnl: -52.13,
          pnlPercent: -1.30,
          fee: 4.02,
          status: 'CLOSED',
          duration: '12m 18s',
          notes: 'Stop loss triggered'
        },
        {
          id: 'T003',
          timestamp: '2024-01-15 12:20:45',
          pair: 'ADA/USDT',
          strategy: 'Breakout Trading',
          side: 'BUY',
          type: 'MARKET',
          amount: 1000,
          entryPrice: 0.4850,
          exitPrice: 0.4925,
          pnl: 75.00,
          pnlPercent: 1.55,
          fee: 0.97,
          status: 'CLOSED',
          duration: '8m 45s',
          notes: 'Clean breakout above resistance'
        },
        {
          id: 'T004',
          timestamp: '2024-01-15 11:15:30',
          pair: 'SOL/USDT',
          strategy: 'Momentum Scalping',
          side: 'BUY',
          type: 'LIMIT',
          amount: 5,
          entryPrice: 98.50,
          exitPrice: null,
          pnl: 0,
          pnlPercent: 0,
          fee: 0,
          status: 'OPEN',
          duration: '2h 45m',
          notes: 'Waiting for target'
        },
        {
          id: 'T005',
          timestamp: '2024-01-15 10:30:15',
          pair: 'BTC/USDT',
          strategy: 'Mean Reversion',
          side: 'SELL',
          type: 'MARKET',
          amount: 0.05,
          entryPrice: 43100.00,
          exitPrice: 43350.00,
          pnl: 12.50,
          pnlPercent: 0.58,
          fee: 2.16,
          status: 'CLOSED',
          duration: '15m 22s',
          notes: 'Quick scalp on rebound'
        }
      ];
      
      setTrades(mockTrades);
    } catch (error) {
      console.error('Failed to fetch trade history:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...trades];

    if (filters.pair) {
      filtered = filtered.filter(trade => trade.pair.includes(filters.pair));
    }
    if (filters.strategy) {
      filtered = filtered.filter(trade => trade.strategy === filters.strategy);
    }
    if (filters.status) {
      filtered = filtered.filter(trade => trade.status === filters.status);
    }
    if (filters.minPnL) {
      filtered = filtered.filter(trade => trade.pnl >= parseFloat(filters.minPnL));
    }
    if (filters.maxPnL) {
      filtered = filtered.filter(trade => trade.pnl <= parseFloat(filters.maxPnL));
    }

    setFilteredTrades(filtered);
    setPage(1);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const clearFilters = () => {
    setFilters({
      pair: '',
      strategy: '',
      status: '',
      dateFrom: null,
      dateTo: null,
      minPnL: '',
      maxPnL: ''
    });
  };

  const handleTradeDetails = (trade) => {
    setSelectedTrade(trade);
    setDetailsOpen(true);
  };

  const exportTrades = () => {
    // Mock export functionality
    const csvContent = [
      ['ID', 'Timestamp', 'Pair', 'Strategy', 'Side', 'Type', 'Amount', 'Entry Price', 'Exit Price', 'P&L', 'P&L %', 'Fee', 'Status', 'Duration'].join(','),
      ...filteredTrades.map(trade => [
        trade.id,
        trade.timestamp,
        trade.pair,
        trade.strategy,
        trade.side,
        trade.type,
        trade.amount,
        trade.entryPrice,
        trade.exitPrice || 'N/A',
        trade.pnl,
        trade.pnlPercent,
        trade.fee,
        trade.status,
        trade.duration
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade_history_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatPercent = (percent) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getPnLColor = (value) => {
    if (value > 0) return 'success.main';
    if (value < 0) return 'error.main';
    return 'text.primary';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OPEN': return 'info';
      case 'CLOSED': return 'success';
      case 'CANCELLED': return 'error';
      default: return 'default';
    }
  };

  const getSideColor = (side) => {
    return side === 'BUY' ? 'success' : 'error';
  };

  const paginatedTrades = filteredTrades.slice(
    (page - 1) * rowsPerPage,
    page * rowsPerPage
  );

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ flexGrow: 1 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 300 }}>
            Trade History
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Export CSV">
              <IconButton onClick={exportTrades}>
                <Download />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton onClick={fetchTradeHistory}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <FilterList sx={{ mr: 1 }} />
              <Typography variant="h6">Filters</Typography>
              <Button 
                size="small" 
                onClick={clearFilters} 
                sx={{ ml: 'auto' }}
              >
                Clear All
              </Button>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={2}>
                <TextField
                  fullWidth
                  size="small"
                  label="Trading Pair"
                  value={filters.pair}
                  onChange={(e) => handleFilterChange('pair', e.target.value)}
                  placeholder="e.g. BTC"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Strategy</InputLabel>
                  <Select
                    value={filters.strategy}
                    label="Strategy"
                    onChange={(e) => handleFilterChange('strategy', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="Momentum Scalping">Momentum Scalping</MenuItem>
                    <MenuItem value="Mean Reversion">Mean Reversion</MenuItem>
                    <MenuItem value="Breakout Trading">Breakout Trading</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status}
                    label="Status"
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="OPEN">Open</MenuItem>
                    <MenuItem value="CLOSED">Closed</MenuItem>
                    <MenuItem value="CANCELLED">Cancelled</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <TextField
                  fullWidth
                  size="small"
                  label="Min P&L ($)"
                  type="number"
                  value={filters.minPnL}
                  onChange={(e) => handleFilterChange('minPnL', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <TextField
                  fullWidth
                  size="small"
                  label="Max P&L ($)"
                  type="number"
                  value={filters.maxPnL}
                  onChange={(e) => handleFilterChange('maxPnL', e.target.value)}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Trade History Table */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Trade History ({filteredTrades.length} trades)
              </Typography>
            </Box>
            
            <TableContainer component={Paper} className="data-table">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Trade ID</TableCell>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Pair</TableCell>
                    <TableCell>Strategy</TableCell>
                    <TableCell align="center">Side</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Entry Price</TableCell>
                    <TableCell align="right">Exit Price</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right">P&L %</TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell align="right">Duration</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedTrades.map((trade) => (
                    <TableRow key={trade.id}>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontFamily: 'monospace' }}>
                          {trade.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {trade.timestamp}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="subtitle2" className="trading-pair">
                          {trade.pair}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {trade.strategy}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={trade.side} 
                          color={getSideColor(trade.side)}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {trade.amount.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatCurrency(trade.entryPrice)}
                      </TableCell>
                      <TableCell align="right">
                        {trade.exitPrice ? formatCurrency(trade.exitPrice) : '-'}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {trade.pnl !== 0 && (
                            trade.pnl > 0 ? (
                              <TrendingUp sx={{ color: 'success.main', mr: 0.5, fontSize: 16 }} />
                            ) : (
                              <TrendingDown sx={{ color: 'error.main', mr: 0.5, fontSize: 16 }} />
                            )
                          )}
                          <Typography 
                            variant="body2" 
                            sx={{ color: getPnLColor(trade.pnl) }}
                          >
                            {trade.pnl !== 0 ? formatCurrency(trade.pnl) : '-'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          sx={{ color: getPnLColor(trade.pnl) }}
                        >
                          {trade.pnlPercent !== 0 ? formatPercent(trade.pnlPercent) : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={trade.status} 
                          color={getStatusColor(trade.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {trade.duration}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton 
                            size="small" 
                            onClick={() => handleTradeDetails(trade)}
                          >
                            <Visibility fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={Math.ceil(filteredTrades.length / rowsPerPage)}
                page={page}
                onChange={(event, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          </CardContent>
        </Card>

        {/* Trade Details Dialog */}
        <Dialog 
          open={detailsOpen} 
          onClose={() => setDetailsOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Trade Details - {selectedTrade?.id}
          </DialogTitle>
          <DialogContent>
            {selectedTrade && (
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Trading Pair</Typography>
                  <Typography variant="body1" className="trading-pair">{selectedTrade.pair}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Strategy</Typography>
                  <Typography variant="body1">{selectedTrade.strategy}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Side</Typography>
                  <Chip 
                    label={selectedTrade.side} 
                    color={getSideColor(selectedTrade.side)}
                    size="small"
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Order Type</Typography>
                  <Typography variant="body1">{selectedTrade.type}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Amount</Typography>
                  <Typography variant="body1">{selectedTrade.amount.toLocaleString()}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Entry Price</Typography>
                  <Typography variant="body1">{formatCurrency(selectedTrade.entryPrice)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Exit Price</Typography>
                  <Typography variant="body1">
                    {selectedTrade.exitPrice ? formatCurrency(selectedTrade.exitPrice) : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Duration</Typography>
                  <Typography variant="body1">{selectedTrade.duration}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">P&L</Typography>
                  <Typography variant="body1" sx={{ color: getPnLColor(selectedTrade.pnl) }}>
                    {selectedTrade.pnl !== 0 ? formatCurrency(selectedTrade.pnl) : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">P&L %</Typography>
                  <Typography variant="body1" sx={{ color: getPnLColor(selectedTrade.pnl) }}>
                    {selectedTrade.pnlPercent !== 0 ? formatPercent(selectedTrade.pnlPercent) : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Fee</Typography>
                  <Typography variant="body1">{formatCurrency(selectedTrade.fee)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                  <Chip 
                    label={selectedTrade.status} 
                    color={getStatusColor(selectedTrade.status)}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary">Notes</Typography>
                  <Typography variant="body1">{selectedTrade.notes}</Typography>
                </Grid>
              </Grid>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default History;