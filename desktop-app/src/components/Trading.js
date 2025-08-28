import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Slider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  SwapHoriz,
  AccountBalance,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';

const Trading = () => {
  const [selectedPair, setSelectedPair] = useState('BTC/USDT');
  const [orderType, setOrderType] = useState('market');
  const [orderSide, setOrderSide] = useState('buy');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  const [usePercentage, setUsePercentage] = useState(false);
  const [balancePercentage, setBalancePercentage] = useState(25);
  const [tabValue, setTabValue] = useState(0);
  const [marketData, setMarketData] = useState({});
  const [orderBook, setOrderBook] = useState({ bids: [], asks: [] });
  const [recentTrades, setRecentTrades] = useState([]);
  const [openOrders, setOpenOrders] = useState([]);
  const [balance, setBalance] = useState({ USDT: 10000, BTC: 0.5, ETH: 2.5 });

  const tradingPairs = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
    'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT'
  ];

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 5000);
    return () => clearInterval(interval);
  }, [selectedPair]);

  const fetchMarketData = async () => {
    // Mock market data - replace with actual API calls
    const mockData = {
      price: 43250.50,
      change24h: 1250.75,
      changePercent24h: 2.98,
      volume24h: 28450000,
      high24h: 44100.00,
      low24h: 42800.00,
      priceData: generateMockPriceData()
    };
    
    const mockOrderBook = {
      bids: [
        { price: 43249.50, amount: 0.125 },
        { price: 43248.00, amount: 0.250 },
        { price: 43247.25, amount: 0.180 },
        { price: 43246.75, amount: 0.320 },
        { price: 43245.50, amount: 0.095 }
      ],
      asks: [
        { price: 43251.00, amount: 0.150 },
        { price: 43252.25, amount: 0.200 },
        { price: 43253.50, amount: 0.175 },
        { price: 43254.75, amount: 0.280 },
        { price: 43256.00, amount: 0.110 }
      ]
    };
    
    const mockRecentTrades = [
      { id: 1, price: 43250.50, amount: 0.025, side: 'buy', time: '14:32:15' },
      { id: 2, price: 43249.75, amount: 0.050, side: 'sell', time: '14:32:12' },
      { id: 3, price: 43251.00, amount: 0.015, side: 'buy', time: '14:32:08' },
      { id: 4, price: 43248.25, amount: 0.080, side: 'sell', time: '14:32:05' },
      { id: 5, price: 43250.00, amount: 0.035, side: 'buy', time: '14:32:02' }
    ];
    
    const mockOpenOrders = [
      { id: 1, pair: 'BTC/USDT', side: 'buy', type: 'limit', amount: 0.025, price: 42800.00, status: 'open' },
      { id: 2, pair: 'ETH/USDT', side: 'sell', type: 'limit', amount: 1.5, price: 2720.00, status: 'open' }
    ];
    
    setMarketData(mockData);
    setOrderBook(mockOrderBook);
    setRecentTrades(mockRecentTrades);
    setOpenOrders(mockOpenOrders);
  };

  const generateMockPriceData = () => {
    const data = [];
    const now = new Date();
    let basePrice = 43250;
    
    for (let i = 59; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 1000);
      basePrice += (Math.random() - 0.5) * 100;
      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        price: basePrice
      });
    }
    return data;
  };

  const handlePlaceOrder = () => {
    // Validate order
    if (!amount || (orderType === 'limit' && !price)) {
      alert('Please fill in all required fields');
      return;
    }
    
    // Mock order placement
    const newOrder = {
      id: Date.now(),
      pair: selectedPair,
      side: orderSide,
      type: orderType,
      amount: parseFloat(amount),
      price: orderType === 'market' ? marketData.price : parseFloat(price),
      status: 'pending'
    };
    
    console.log('Placing order:', newOrder);
    alert(`Order placed: ${orderSide.toUpperCase()} ${amount} ${selectedPair}`);
    
    // Reset form
    setAmount('');
    setPrice('');
    setStopLoss('');
    setTakeProfit('');
  };

  const handleCancelOrder = (orderId) => {
    setOpenOrders(prev => prev.filter(order => order.id !== orderId));
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

  const getPriceColor = (value) => {
    if (value > 0) return 'success.main';
    if (value < 0) return 'error.main';
    return 'text.primary';
  };

  const calculateOrderValue = () => {
    const orderAmount = parseFloat(amount) || 0;
    const orderPrice = orderType === 'market' ? marketData.price : parseFloat(price) || 0;
    return orderAmount * orderPrice;
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" component="h1" sx={{ fontWeight: 300, mb: 3 }}>
        Trading Terminal
      </Typography>

      <Grid container spacing={3}>
        {/* Market Data & Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              {/* Pair Selector & Price Info */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <FormControl sx={{ minWidth: 150 }}>
                  <InputLabel>Trading Pair</InputLabel>
                  <Select
                    value={selectedPair}
                    onChange={(e) => setSelectedPair(e.target.value)}
                    label="Trading Pair"
                  >
                    {tradingPairs.map((pair) => (
                      <MenuItem key={pair} value={pair}>{pair}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h4" className="number-large">
                    {formatCurrency(marketData.price)}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    {marketData.change24h >= 0 ? (
                      <TrendingUp sx={{ color: 'success.main', mr: 0.5 }} />
                    ) : (
                      <TrendingDown sx={{ color: 'error.main', mr: 0.5 }} />
                    )}
                    <Typography 
                      variant="body1" 
                      sx={{ color: getPriceColor(marketData.change24h) }}
                    >
                      {formatCurrency(marketData.change24h)} ({formatPercent(marketData.changePercent24h)})
                    </Typography>
                  </Box>
                </Box>
              </Box>
              
              {/* 24h Stats */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={3}>
                  <Typography variant="body2" color="text.secondary">24h High</Typography>
                  <Typography variant="body1">{formatCurrency(marketData.high24h)}</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="body2" color="text.secondary">24h Low</Typography>
                  <Typography variant="body1">{formatCurrency(marketData.low24h)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">24h Volume</Typography>
                  <Typography variant="body1">{formatCurrency(marketData.volume24h)}</Typography>
                </Grid>
              </Grid>
              
              {/* Price Chart */}
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={marketData.priceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#b0bec5"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#b0bec5"
                      fontSize={12}
                      domain={['dataMin - 100', 'dataMax + 100']}
                      tickFormatter={(value) => `$${value.toLocaleString()}`}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#00d4ff"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Order Form */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Place Order</Typography>
              
              {/* Order Type Tabs */}
              <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
                <Tab label="Spot" />
                <Tab label="Margin" disabled />
              </Tabs>
              
              {/* Buy/Sell Toggle */}
              <Box sx={{ display: 'flex', mb: 2 }}>
                <Button
                  variant={orderSide === 'buy' ? 'contained' : 'outlined'}
                  className={orderSide === 'buy' ? 'btn-buy' : ''}
                  onClick={() => setOrderSide('buy')}
                  sx={{ flex: 1, mr: 1 }}
                >
                  Buy
                </Button>
                <Button
                  variant={orderSide === 'sell' ? 'contained' : 'outlined'}
                  className={orderSide === 'sell' ? 'btn-sell' : ''}
                  onClick={() => setOrderSide('sell')}
                  sx={{ flex: 1, ml: 1 }}
                >
                  Sell
                </Button>
              </Box>
              
              {/* Order Type */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Order Type</InputLabel>
                <Select
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value)}
                  label="Order Type"
                >
                  <MenuItem value="market">Market</MenuItem>
                  <MenuItem value="limit">Limit</MenuItem>
                  <MenuItem value="stop">Stop Loss</MenuItem>
                </Select>
              </FormControl>
              
              {/* Price (for limit orders) */}
              {orderType === 'limit' && (
                <TextField
                  fullWidth
                  label="Price (USDT)"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  type="number"
                  sx={{ mb: 2 }}
                />
              )}
              
              {/* Amount */}
              <TextField
                fullWidth
                label={`Amount (${selectedPair.split('/')[0]})`}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                type="number"
                sx={{ mb: 2 }}
              />
              
              {/* Percentage Selector */}
              <FormControlLabel
                control={
                  <Switch
                    checked={usePercentage}
                    onChange={(e) => setUsePercentage(e.target.checked)}
                  />
                }
                label="Use % of balance"
                sx={{ mb: 1 }}
              />
              
              {usePercentage && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {balancePercentage}% of available balance
                  </Typography>
                  <Slider
                    value={balancePercentage}
                    onChange={(e, newValue) => setBalancePercentage(newValue)}
                    step={25}
                    marks
                    min={0}
                    max={100}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                  />
                </Box>
              )}
              
              {/* Advanced Options */}
              <TextField
                fullWidth
                label="Stop Loss (Optional)"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                type="number"
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Take Profit (Optional)"
                value={takeProfit}
                onChange={(e) => setTakeProfit(e.target.value)}
                type="number"
                sx={{ mb: 2 }}
              />
              
              {/* Order Summary */}
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Order Value: {formatCurrency(calculateOrderValue())}
                </Typography>
                <Typography variant="body2">
                  Available: {formatCurrency(balance.USDT)} USDT
                </Typography>
              </Alert>
              
              {/* Place Order Button */}
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handlePlaceOrder}
                className={orderSide === 'buy' ? 'btn-buy' : 'btn-sell'}
              >
                {orderSide === 'buy' ? 'Buy' : 'Sell'} {selectedPair.split('/')[0]}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Order Book */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Order Book</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="error.main" sx={{ mb: 1 }}>Asks (Sell Orders)</Typography>
                  {orderBook.asks.slice().reverse().map((ask, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                      <Typography variant="body2" color="error.main">
                        {formatCurrency(ask.price)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {ask.amount}
                      </Typography>
                    </Box>
                  ))}
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="success.main" sx={{ mb: 1 }}>Bids (Buy Orders)</Typography>
                  {orderBook.bids.map((bid, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                      <Typography variant="body2" color="success.main">
                        {formatCurrency(bid.price)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {bid.amount}
                      </Typography>
                    </Box>
                  ))}
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Trades & Open Orders */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Recent Trades</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Price</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Side</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentTrades.map((trade) => (
                      <TableRow key={trade.id}>
                        <TableCell>{trade.time}</TableCell>
                        <TableCell>{formatCurrency(trade.price)}</TableCell>
                        <TableCell>{trade.amount}</TableCell>
                        <TableCell>
                          <Chip 
                            label={trade.side.toUpperCase()} 
                            size="small"
                            color={trade.side === 'buy' ? 'success' : 'error'}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Open Orders */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Open Orders</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Pair</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {openOrders.map((order) => (
                      <TableRow key={order.id}>
                        <TableCell>{order.pair}</TableCell>
                        <TableCell>
                          <Chip 
                            label={order.side.toUpperCase()} 
                            size="small"
                            color={order.side === 'buy' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell>{order.type.toUpperCase()}</TableCell>
                        <TableCell align="right">{order.amount}</TableCell>
                        <TableCell align="right">{formatCurrency(order.price)}</TableCell>
                        <TableCell>
                          <Chip label={order.status.toUpperCase()} size="small" />
                        </TableCell>
                        <TableCell>
                          <Button 
                            size="small" 
                            color="error"
                            onClick={() => handleCancelOrder(order.id)}
                          >
                            Cancel
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Trading;