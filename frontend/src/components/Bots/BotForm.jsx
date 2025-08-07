import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Grid,
  Paper,
  Divider,
  Slider,
  InputAdornment,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import useTradingStore from '../../stores/useTradingStore';

const BotForm = ({ initialData = null }) => {
  const navigate = useNavigate();
  const { 
    symbols, 
    strategies, 
    isLoading, 
    error, 
    fetchSymbols, 
    fetchStrategies, 
    createBot, 
    updateBot,
    clearError
  } = useTradingStore();

  const [formData, setFormData] = useState({
    name: '',
    symbol: '',
    strategy_id: '',
    interval: '1h',
    amount: 100,
    take_profit: 3,
    stop_loss: 2,
    strategy_params: {}
  });

  const [formErrors, setFormErrors] = useState({});
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Load symbols and strategies on component mount
  useEffect(() => {
    fetchSymbols();
    fetchStrategies();
  }, [fetchSymbols, fetchStrategies]);

  // Set initial form data if editing an existing bot
  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        symbol: initialData.symbol || '',
        strategy_id: initialData.strategy?.id || '',
        interval: initialData.interval || '1h',
        amount: initialData.amount || 100,
        take_profit: initialData.take_profit || 3,
        stop_loss: initialData.stop_loss || 2,
        strategy_params: initialData.strategy_params || {}
      });

      // Find the selected strategy
      if (strategies.length > 0 && initialData.strategy?.id) {
        const strategy = strategies.find(s => s.id === initialData.strategy.id);
        setSelectedStrategy(strategy);
      }
    }
  }, [initialData, strategies]);

  // Update selected strategy when strategy_id changes
  useEffect(() => {
    if (strategies.length > 0 && formData.strategy_id) {
      const strategy = strategies.find(s => s.id === formData.strategy_id);
      setSelectedStrategy(strategy);

      // Initialize strategy parameters with default values if not set
      if (strategy && strategy.parameters) {
        const initialParams = {};
        
        strategy.parameters.forEach(param => {
          // Only set default if the parameter doesn't already have a value
          if (!formData.strategy_params[param.name]) {
            initialParams[param.name] = param.default;
          }
        });

        if (Object.keys(initialParams).length > 0) {
          setFormData(prev => ({
            ...prev,
            strategy_params: {
              ...prev.strategy_params,
              ...initialParams
            }
          }));
        }
      }
    }
  }, [formData.strategy_id, strategies]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error for this field
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Clear success message when form changes
    if (successMessage) {
      setSuccessMessage('');
    }

    // Clear global error
    if (error) {
      clearError();
    }
  };

  const handleStrategyParamChange = (paramName, value) => {
    setFormData(prev => ({
      ...prev,
      strategy_params: {
        ...prev.strategy_params,
        [paramName]: value
      }
    }));
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.name.trim()) {
      errors.name = 'Bot name is required';
    }

    if (!formData.symbol) {
      errors.symbol = 'Trading pair is required';
    }

    if (!formData.strategy_id) {
      errors.strategy_id = 'Strategy is required';
    }

    if (!formData.interval) {
      errors.interval = 'Time interval is required';
    }

    if (!formData.amount || formData.amount <= 0) {
      errors.amount = 'Amount must be greater than 0';
    }

    if (formData.take_profit <= 0) {
      errors.take_profit = 'Take profit must be greater than 0';
    }

    if (formData.stop_loss <= 0) {
      errors.stop_loss = 'Stop loss must be greater than 0';
    }

    // Validate strategy parameters
    if (selectedStrategy && selectedStrategy.parameters) {
      selectedStrategy.parameters.forEach(param => {
        const value = formData.strategy_params[param.name];
        
        if (value === undefined || value === null) {
          errors[`strategy_param_${param.name}`] = `${param.label} is required`;
        } else if (param.min !== undefined && value < param.min) {
          errors[`strategy_param_${param.name}`] = `${param.label} must be at least ${param.min}`;
        } else if (param.max !== undefined && value > param.max) {
          errors[`strategy_param_${param.name}`] = `${param.label} must be at most ${param.max}`;
        }
      });
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSuccessMessage('');

    try {
      const result = initialData
        ? await updateBot(initialData.id, formData)
        : await createBot(formData);

      if (result.success) {
        setSuccessMessage(
          initialData 
            ? `Bot "${formData.name}" updated successfully!` 
            : `Bot "${formData.name}" created successfully!`
        );
        
        // Redirect after a short delay
        setTimeout(() => {
          navigate('/bots');
        }, 1500);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStrategyParameters = () => {
    if (!selectedStrategy || !selectedStrategy.parameters) {
      return null;
    }

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Strategy Parameters
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          {selectedStrategy.description}
        </Typography>
        
        <Grid container spacing={3}>
          {selectedStrategy.parameters.map((param) => {
            const value = formData.strategy_params[param.name] !== undefined 
              ? formData.strategy_params[param.name] 
              : param.default;
            
            const errorKey = `strategy_param_${param.name}`;
            const hasError = !!formErrors[errorKey];
            
            return (
              <Grid item xs={12} sm={6} key={param.name}>
                <Box sx={{ mb: 2 }}>
                  <Typography id={`${param.name}-slider-label`} gutterBottom>
                    {param.label}
                  </Typography>
                  
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs>
                      <Slider
                        value={value}
                        onChange={(e, newValue) => handleStrategyParamChange(param.name, newValue)}
                        aria-labelledby={`${param.name}-slider-label`}
                        valueLabelDisplay="auto"
                        step={param.step || 1}
                        min={param.min}
                        max={param.max}
                        marks={[
                          { value: param.min, label: param.min.toString() },
                          { value: param.max, label: param.max.toString() }
                        ]}
                      />
                    </Grid>
                    <Grid item>
                      <TextField
                        value={value}
                        onChange={(e) => {
                          const newValue = parseFloat(e.target.value);
                          if (!isNaN(newValue)) {
                            handleStrategyParamChange(param.name, newValue);
                          }
                        }}
                        inputProps={{
                          step: param.step || 1,
                          min: param.min,
                          max: param.max,
                          type: 'number',
                          'aria-labelledby': `${param.name}-slider-label`,
                        }}
                        size="small"
                        error={hasError}
                        sx={{ width: 80 }}
                      />
                    </Grid>
                  </Grid>
                  
                  {hasError && (
                    <FormHelperText error>{formErrors[errorKey]}</FormHelperText>
                  )}
                  
                  {param.description && (
                    <FormHelperText>{param.description}</FormHelperText>
                  )}
                </Box>
              </Grid>
            );
          })}
        </Grid>
      </Box>
    );
  };

  const renderBacktestingSection = () => {
    if (!selectedStrategy) {
      return null;
    }

    return (
      <Accordion sx={{ mt: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Backtest Strategy</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" paragraph>
            Run a backtest to see how this strategy would have performed historically.
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Start Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                // Add your backtest state handling here
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="End Date"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                // Add your backtest state handling here
              />
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              variant="outlined" 
              color="primary"
              // Add your backtest function here
            >
              Run Backtest
            </Button>
          </Box>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          {initialData ? 'Edit Trading Bot' : 'Create New Trading Bot'}
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {successMessage && (
          <Alert severity="success" sx={{ mb: 3 }}>
            {successMessage}
          </Alert>
        )}
        
        <Grid container spacing={3}>
          {/* Bot Name */}
          <Grid item xs={12}>
            <TextField
              name="name"
              label="Bot Name"
              value={formData.name}
              onChange={handleInputChange}
              fullWidth
              required
              error={!!formErrors.name}
              helperText={formErrors.name || 'Give your bot a descriptive name'}
            />
          </Grid>
          
          {/* Trading Pair */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth error={!!formErrors.symbol}>
              <InputLabel id="symbol-label">Trading Pair</InputLabel>
              <Select
                labelId="symbol-label"
                name="symbol"
                value={formData.symbol}
                onChange={handleInputChange}
                label="Trading Pair"
                disabled={isLoading || symbols.length === 0}
              >
                {symbols.map((symbol) => (
                  <MenuItem key={symbol} value={symbol}>
                    {symbol}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>{formErrors.symbol || 'Select the cryptocurrency pair to trade'}</FormHelperText>
            </FormControl>
          </Grid>
          
          {/* Strategy */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth error={!!formErrors.strategy_id}>
              <InputLabel id="strategy-label">Strategy</InputLabel>
              <Select
                labelId="strategy-label"
                name="strategy_id"
                value={formData.strategy_id}
                onChange={handleInputChange}
                label="Strategy"
                disabled={isLoading || strategies.length === 0}
              >
                {strategies.map((strategy) => (
                  <MenuItem key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>{formErrors.strategy_id || 'Select the trading strategy to use'}</FormHelperText>
            </FormControl>
          </Grid>
          
          {/* Time Interval */}
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth error={!!formErrors.interval}>
              <InputLabel id="interval-label">Time Interval</InputLabel>
              <Select
                labelId="interval-label"
                name="interval"
                value={formData.interval}
                onChange={handleInputChange}
                label="Time Interval"
              >
                <MenuItem value="1m">1 minute</MenuItem>
                <MenuItem value="5m">5 minutes</MenuItem>
                <MenuItem value="15m">15 minutes</MenuItem>
                <MenuItem value="30m">30 minutes</MenuItem>
                <MenuItem value="1h">1 hour</MenuItem>
                <MenuItem value="4h">4 hours</MenuItem>
                <MenuItem value="1d">1 day</MenuItem>
              </Select>
              <FormHelperText>{formErrors.interval || 'Select the candle interval for analysis'}</FormHelperText>
            </FormControl>
          </Grid>
          
          {/* Amount */}
          <Grid item xs={12} sm={4}>
            <TextField
              name="amount"
              label="Trading Amount"
              type="number"
              value={formData.amount}
              onChange={handleInputChange}
              fullWidth
              required
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              inputProps={{
                min: 10,
                step: 10
              }}
              error={!!formErrors.amount}
              helperText={formErrors.amount || 'Amount to invest per trade'}
            />
          </Grid>
          
          {/* Take Profit */}
          <Grid item xs={12} sm={2}>
            <TextField
              name="take_profit"
              label="Take Profit"
              type="number"
              value={formData.take_profit}
              onChange={handleInputChange}
              fullWidth
              required
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              inputProps={{
                min: 0.5,
                step: 0.5
              }}
              error={!!formErrors.take_profit}
              helperText={formErrors.take_profit}
            />
          </Grid>
          
          {/* Stop Loss */}
          <Grid item xs={12} sm={2}>
            <TextField
              name="stop_loss"
              label="Stop Loss"
              type="number"
              value={formData.stop_loss}
              onChange={handleInputChange}
              fullWidth
              required
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              inputProps={{
                min: 0.5,
                step: 0.5
              }}
              error={!!formErrors.stop_loss}
              helperText={formErrors.stop_loss}
            />
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 3 }} />
        
        {/* Strategy Parameters */}
        {renderStrategyParameters()}
        
        {/* Backtesting Section */}
        {renderBacktestingSection()}
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button 
            variant="outlined" 
            color="inherit" 
            onClick={() => navigate('/bots')} 
            sx={{ mr: 2 }}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            color="primary"
            disabled={isSubmitting}
            startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
          >
            {isSubmitting ? 'Saving...' : initialData ? 'Update Bot' : 'Create Bot'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default BotForm;