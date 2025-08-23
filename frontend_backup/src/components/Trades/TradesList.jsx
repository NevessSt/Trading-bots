import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Collapse,
  Tooltip
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Search as SearchIcon,
  ArrowUpward as BuyIcon,
  ArrowDownward as SellIcon,
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import useTradingStore from '../../stores/useTradingStore';

const TradesList = () => {
  const { 
    trades, 
    tradePagination, 
    tradeFilters,
    symbols, 
    bots, 
    isLoading, 
    error, 
    fetchTrades, 
    fetchSymbols, 
    fetchBots, 
    setTradeFilters 
  } = useTradingStore();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [localFilters, setLocalFilters] = useState({
    symbol: '',
    botId: '',
    type: '',
    startDate: null,
    endDate: null
  });

  // Initialize local filters from store
  useEffect(() => {
    setLocalFilters(tradeFilters);
  }, [tradeFilters]);

  // Load initial data
  useEffect(() => {
    fetchTrades(1, rowsPerPage);
    fetchSymbols();
    fetchBots();
  }, [fetchTrades, fetchSymbols, fetchBots, rowsPerPage]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
    fetchTrades(newPage + 1, rowsPerPage, tradeFilters);
  };

  const handleChangeRowsPerPage = (event) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    setRowsPerPage(newRowsPerPage);
    setPage(0);
    fetchTrades(1, newRowsPerPage, tradeFilters);
  };

  const handleFilterChange = (field, value) => {
    setLocalFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleApplyFilters = () => {
    setPage(0);
    setTradeFilters(localFilters);
    fetchTrades(1, rowsPerPage, localFilters);
  };

  const handleClearFilters = () => {
    const emptyFilters = {
      symbol: '',
      botId: '',
      type: '',
      startDate: null,
      endDate: null
    };
    setLocalFilters(emptyFilters);
    setTradeFilters(emptyFilters);
    fetchTrades(1, rowsPerPage, emptyFilters);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, 'MMM dd, yyyy HH:mm:ss');
  };

  const formatProfit = (profit) => {
    if (profit === undefined || profit === null) return 'N/A';
    
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

  const renderFilters = () => {
    return (
      <Collapse in={filtersOpen}>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="symbol-filter-label">Symbol</InputLabel>
                <Select
                  labelId="symbol-filter-label"
                  value={localFilters.symbol}
                  onChange={(e) => handleFilterChange('symbol', e.target.value)}
                  label="Symbol"
                >
                  <MenuItem value="">All Symbols</MenuItem>
                  {symbols.map((symbol) => (
                    <MenuItem key={symbol} value={symbol}>
                      {symbol}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="bot-filter-label">Bot</InputLabel>
                <Select
                  labelId="bot-filter-label"
                  value={localFilters.botId}
                  onChange={(e) => handleFilterChange('botId', e.target.value)}
                  label="Bot"
                >
                  <MenuItem value="">All Bots</MenuItem>
                  {bots.map((bot) => (
                    <MenuItem key={bot.id} value={bot.id}>
                      {bot.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="type-filter-label">Type</InputLabel>
                <Select
                  labelId="type-filter-label"
                  value={localFilters.type}
                  onChange={(e) => handleFilterChange('type', e.target.value)}
                  label="Type"
                >
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="buy">Buy</MenuItem>
                  <MenuItem value="sell">Sell</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="Start Date"
                  value={localFilters.startDate}
                  onChange={(date) => handleFilterChange('startDate', date)}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="End Date"
                  value={localFilters.endDate}
                  onChange={(date) => handleFilterChange('endDate', date)}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </Grid>
            </LocalizationProvider>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<SearchIcon />}
                onClick={handleApplyFilters}
                fullWidth
              >
                Apply Filters
              </Button>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={handleClearFilters}
                fullWidth
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Collapse>
    );
  };

  if (isLoading && trades.length === 0) {
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
          Trading History
        </Typography>
        <Tooltip title="Toggle Filters">
          <IconButton 
            onClick={() => setFiltersOpen(!filtersOpen)}
            color={filtersOpen ? 'primary' : 'default'}
          >
            <FilterIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {renderFilters()}

      {trades.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Trades Found
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {Object.values(tradeFilters).some(v => v !== '' && v !== null) 
              ? 'Try adjusting your filters to see more results.'
              : 'Start trading to see your history here.'}
          </Typography>
        </Paper>
      ) : (
        <Paper>
          <TableContainer>
            <Table sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Bot</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell>Profit/Loss</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trades.map((trade) => (
                  <TableRow key={trade.id} hover>
                    <TableCell>{formatDate(trade.timestamp)}</TableCell>
                    <TableCell>{trade.symbol}</TableCell>
                    <TableCell>{getTradeTypeChip(trade.type)}</TableCell>
                    <TableCell>{trade.bot_name || 'Manual'}</TableCell>
                    <TableCell align="right">${trade.price.toFixed(2)}</TableCell>
                    <TableCell align="right">${trade.amount.toFixed(2)}</TableCell>
                    <TableCell align="right">${(trade.price * trade.amount).toFixed(2)}</TableCell>
                    <TableCell>{formatProfit(trade.profit_loss)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25, 50]}
            component="div"
            count={tradePagination.total}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </Paper>
      )}
    </Box>
  );
};

export default TradesList;