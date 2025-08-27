import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  PlayArrow as TestIcon,
  Code as CodeIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`strategy-tabpanel-${index}`}
      aria-labelledby={`strategy-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const StrategyManager = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  
  // Form states
  const [newStrategyCode, setNewStrategyCode] = useState('');
  const [newStrategyName, setNewStrategyName] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [testParameters, setTestParameters] = useState({});
  const [testResults, setTestResults] = useState(null);
  const [validationResults, setValidationResults] = useState(null);
  
  // Stats and metadata
  const [strategyStats, setStrategyStats] = useState(null);
  const [strategyMetadata, setStrategyMetadata] = useState({});

  useEffect(() => {
    loadStrategies();
    if (user?.role === 'admin') {
      loadStrategyStats();
    }
  }, [user]);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/strategies/available');
      if (response.data.success) {
        setStrategies(response.data.strategies);
      } else {
        setError('Failed to load strategies');
      }
    } catch (err) {
      setError('Error loading strategies: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const loadStrategyStats = async () => {
    try {
      const response = await api.get('/api/strategies/stats');
      if (response.data.success) {
        setStrategyStats(response.data.stats);
      }
    } catch (err) {
      console.error('Error loading strategy stats:', err);
    }
  };

  const loadStrategyMetadata = async (strategyId) => {
    try {
      const response = await api.get(`/api/strategies/metadata/${strategyId}`);
      if (response.data.success) {
        setStrategyMetadata(prev => ({
          ...prev,
          [strategyId]: response.data.metadata
        }));
      }
    } catch (err) {
      console.error('Error loading strategy metadata:', err);
    }
  };

  const handleReloadStrategies = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/strategies/reload');
      if (response.data.success) {
        setSuccess(`Successfully reloaded ${response.data.reloaded_count} strategies`);
        await loadStrategies();
        if (user?.role === 'admin') {
          await loadStrategyStats();
        }
      } else {
        setError('Failed to reload strategies');
      }
    } catch (err) {
      setError('Error reloading strategies: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleValidateCode = async () => {
    try {
      const response = await api.post('/api/strategies/validate', {
        code: newStrategyCode
      });
      
      if (response.data.success) {
        setValidationResults({
          valid: true,
          message: response.data.message,
          warnings: response.data.warnings || []
        });
      } else {
        setValidationResults({
          valid: false,
          error: response.data.error,
          details: response.data.details,
          missing: response.data.missing
        });
      }
    } catch (err) {
      setValidationResults({
        valid: false,
        error: 'Validation failed: ' + (err.response?.data?.error || err.message)
      });
    }
  };

  const handleAddStrategy = async () => {
    try {
      const response = await api.post('/api/strategies/add', {
        code: newStrategyCode,
        name: newStrategyName
      });
      
      if (response.data.success) {
        setSuccess(`Strategy "${newStrategyName}" added successfully`);
        setAddDialogOpen(false);
        setNewStrategyCode('');
        setNewStrategyName('');
        setValidationResults(null);
        await loadStrategies();
      } else {
        setError('Failed to add strategy: ' + response.data.error);
      }
    } catch (err) {
      setError('Error adding strategy: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleTestStrategy = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/strategies/test', {
        strategy_name: selectedStrategy.name,
        parameters: testParameters
      });
      
      if (response.data.success) {
        setTestResults(response.data);
      } else {
        setError('Test failed: ' + response.data.error);
      }
    } catch (err) {
      setError('Error testing strategy: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleShowInfo = async (strategy) => {
    setSelectedStrategy(strategy);
    if (!strategyMetadata[strategy.id]) {
      await loadStrategyMetadata(strategy.id);
    }
    setInfoDialogOpen(true);
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  const formatParameters = (parameters) => {
    if (!parameters || typeof parameters !== 'object') return 'None';
    return Object.entries(parameters)
      .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
      .join(', ');
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Strategy Manager
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Available Strategies" />
          {user?.role === 'admin' && <Tab label="Add Strategy" />}
          {user?.role === 'admin' && <Tab label="Statistics" />}
        </Tabs>
      </Box>

      {/* Available Strategies Tab */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">
            Available Strategies ({strategies.length})
          </Typography>
          <Box>
            <Button
              startIcon={<RefreshIcon />}
              onClick={loadStrategies}
              disabled={loading}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
            {user?.role === 'admin' && (
              <Button
                startIcon={<RefreshIcon />}
                onClick={handleReloadStrategies}
                disabled={loading}
                variant="outlined"
              >
                Reload All
              </Button>
            )}
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={2}>
            {strategies.map((strategy) => (
              <Grid item xs={12} md={6} lg={4} key={strategy.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="h6" component="div">
                        {strategy.name}
                      </Typography>
                      <Box>
                        <Tooltip title="Test Strategy">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedStrategy(strategy);
                              setTestParameters(strategy.default_parameters || {});
                              setTestResults(null);
                              setTestDialogOpen(true);
                            }}
                          >
                            <TestIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Strategy Info">
                          <IconButton
                            size="small"
                            onClick={() => handleShowInfo(strategy)}
                          >
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {strategy.description}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      {strategy.risk_level && (
                        <Chip
                          label={`Risk: ${strategy.risk_level}`}
                          color={getRiskLevelColor(strategy.risk_level)}
                          size="small"
                        />
                      )}
                      {strategy.version && (
                        <Chip label={`v${strategy.version}`} size="small" variant="outlined" />
                      )}
                      {strategy.tags && strategy.tags.map((tag) => (
                        <Chip key={tag} label={tag} size="small" variant="outlined" />
                      ))}
                    </Box>
                    
                    {strategy.min_capital && (
                      <Typography variant="caption" display="block">
                        Min Capital: ${strategy.min_capital}
                      </Typography>
                    )}
                    
                    {strategy.supported_timeframes && (
                      <Typography variant="caption" display="block">
                        Timeframes: {strategy.supported_timeframes.join(', ')}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Add Strategy Tab (Admin Only) */}
      {user?.role === 'admin' && (
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Add New Strategy
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Strategy Name"
                value={newStrategyName}
                onChange={(e) => setNewStrategyName(e.target.value)}
                placeholder="e.g., MyCustomStrategy"
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                multiline
                rows={20}
                label="Strategy Code"
                value={newStrategyCode}
                onChange={(e) => setNewStrategyCode(e.target.value)}
                placeholder="Paste your strategy code here..."
                sx={{ mb: 2, fontFamily: 'monospace' }}
              />
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  onClick={handleValidateCode}
                  disabled={!newStrategyCode}
                >
                  Validate Code
                </Button>
                <Button
                  variant="contained"
                  onClick={handleAddStrategy}
                  disabled={!newStrategyCode || !newStrategyName || (validationResults && !validationResults.valid)}
                >
                  Add Strategy
                </Button>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {validationResults && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Validation Results
                    </Typography>
                    
                    {validationResults.valid ? (
                      <Alert severity="success" sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <CheckCircleIcon sx={{ mr: 1 }} />
                          {validationResults.message}
                        </Box>
                      </Alert>
                    ) : (
                      <Alert severity="error" sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <ErrorIcon sx={{ mr: 1 }} />
                          {validationResults.error}
                        </Box>
                      </Alert>
                    )}
                    
                    {validationResults.warnings && validationResults.warnings.length > 0 && (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        <Typography variant="subtitle2">Warnings:</Typography>
                        <ul>
                          {validationResults.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      </Alert>
                    )}
                    
                    {validationResults.missing && validationResults.missing.length > 0 && (
                      <Alert severity="info">
                        <Typography variant="subtitle2">Missing Components:</Typography>
                        <ul>
                          {validationResults.missing.map((missing, index) => (
                            <li key={index}>{missing}</li>
                          ))}
                        </ul>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              )}
              
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Strategy Template
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Your strategy must inherit from BaseStrategy and implement the required methods:
                  </Typography>
                  <Box component="pre" sx={{ 
                    backgroundColor: 'grey.100', 
                    p: 2, 
                    borderRadius: 1, 
                    fontSize: '0.8rem',
                    overflow: 'auto'
                  }}>
{`from bot_engine.strategies.base_strategy import BaseStrategy
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    def __init__(self, parameters=None):
        super().__init__(parameters)
        # Initialize your strategy parameters
        
    def generate_signals(self, data):
        # Implement your trading logic
        # Return DataFrame with 'signal' column
        # 1 = buy, -1 = sell, 0 = hold
        pass
        
    def get_parameters(self):
        # Return current parameters
        return self.parameters
        
    def set_parameters(self, parameters):
        # Update parameters
        self.parameters = parameters`}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      )}

      {/* Statistics Tab (Admin Only) */}
      {user?.role === 'admin' && (
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Strategy Statistics
          </Typography>
          
          {strategyStats ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Overview
                    </Typography>
                    <Typography>Total Strategies: {strategyStats.total_strategies}</Typography>
                    <Typography>Dynamic Strategies: {strategyStats.dynamic_strategies}</Typography>
                    <Typography>Legacy Strategies: {strategyStats.legacy_strategies}</Typography>
                    <Typography>Active Strategies: {strategyStats.active_strategies}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Performance
                    </Typography>
                    <Typography>Load Time: {strategyStats.load_time_ms}ms</Typography>
                    <Typography>Memory Usage: {strategyStats.memory_usage_mb}MB</Typography>
                    <Typography>Last Reload: {new Date(strategyStats.last_reload).toLocaleString()}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Typography>Loading statistics...</Typography>
          )}
        </TabPanel>
      )}

      {/* Test Strategy Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Test Strategy: {selectedStrategy?.name}
        </DialogTitle>
        <DialogContent>
          {selectedStrategy && (
            <Box>
              <Typography variant="body2" paragraph>
                {selectedStrategy.description}
              </Typography>
              
              <Typography variant="h6" gutterBottom>
                Parameters
              </Typography>
              
              {selectedStrategy.parameters && Object.entries(selectedStrategy.parameters).map(([key, param]) => (
                <TextField
                  key={key}
                  fullWidth
                  label={param.name || key}
                  type={param.type === 'number' ? 'number' : 'text'}
                  value={testParameters[key] || param.default || ''}
                  onChange={(e) => setTestParameters(prev => ({
                    ...prev,
                    [key]: param.type === 'number' ? parseFloat(e.target.value) : e.target.value
                  }))}
                  helperText={param.description}
                  sx={{ mb: 2 }}
                />
              ))}
              
              {testResults && (
                <Card sx={{ mt: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Test Results
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography>Data Points: {testResults.test_results.data_points}</Typography>
                        <Typography>Buy Signals: {testResults.test_results.buy_signals}</Typography>
                        <Typography>Sell Signals: {testResults.test_results.sell_signals}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography>Total Signals: {testResults.test_results.total_signals}</Typography>
                        <Typography>Signal Frequency: {testResults.test_results.signal_frequency.toFixed(2)}%</Typography>
                      </Grid>
                    </Grid>
                    
                    {testResults.backtest_results && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Backtest Results
                        </Typography>
                        <Typography>Total Return: {(testResults.backtest_results.total_return * 100).toFixed(2)}%</Typography>
                        <Typography>Annual Return: {(testResults.backtest_results.annual_return * 100).toFixed(2)}%</Typography>
                        <Typography>Sharpe Ratio: {testResults.backtest_results.sharpe_ratio?.toFixed(2) || 'N/A'}</Typography>
                        <Typography>Max Drawdown: {(testResults.backtest_results.max_drawdown * 100).toFixed(2)}%</Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Close</Button>
          <Button onClick={handleTestStrategy} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={20} /> : 'Run Test'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Strategy Info Dialog */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Strategy Information: {selectedStrategy?.name}
        </DialogTitle>
        <DialogContent>
          {selectedStrategy && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedStrategy.description}
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Details</Typography>
                  <Typography>Version: {selectedStrategy.version || 'N/A'}</Typography>
                  <Typography>Author: {selectedStrategy.author || 'N/A'}</Typography>
                  <Typography>Risk Level: {selectedStrategy.risk_level || 'N/A'}</Typography>
                  <Typography>Min Capital: ${selectedStrategy.min_capital || 'N/A'}</Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Supported Timeframes</Typography>
                  {selectedStrategy.supported_timeframes ? (
                    selectedStrategy.supported_timeframes.map((tf) => (
                      <Chip key={tf} label={tf} size="small" sx={{ mr: 1, mb: 1 }} />
                    ))
                  ) : (
                    <Typography>Not specified</Typography>
                  )}
                </Grid>
              </Grid>
              
              {selectedStrategy.parameters && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="h6" gutterBottom>Parameters</Typography>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Parameter</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Default</TableCell>
                          <TableCell>Description</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(selectedStrategy.parameters).map(([key, param]) => (
                          <TableRow key={key}>
                            <TableCell>{param.name || key}</TableCell>
                            <TableCell>{param.type}</TableCell>
                            <TableCell>{JSON.stringify(param.default)}</TableCell>
                            <TableCell>{param.description}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              {selectedStrategy.tags && selectedStrategy.tags.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="h6" gutterBottom>Tags</Typography>
                  {selectedStrategy.tags.map((tag) => (
                    <Chip key={tag} label={tag} size="small" sx={{ mr: 1, mb: 1 }} />
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategyManager;