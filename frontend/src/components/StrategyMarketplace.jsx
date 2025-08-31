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
  FormControlLabel,
  Switch,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Pagination,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Paper,
  Divider
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Code as CodeIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CloudUpload as CloudUploadIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  ShowChart as ShowChartIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const StrategyMarketplace = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [strategies, setStrategies] = useState([]);
  const [myStrategies, setMyStrategies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Upload dialog state
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadData, setUploadData] = useState({
    strategy_name: '',
    strategy_description: '',
    is_public: false,
    file: null
  });
  const [uploadLoading, setUploadLoading] = useState(false);
  
  // Browse filters
  const [filters, setFilters] = useState({
    search: '',
    category: 'all',
    sort_by: 'created_at',
    page: 1,
    per_page: 12
  });
  const [pagination, setPagination] = useState({
    page: 1,
    pages: 1,
    total: 0
  });
  
  // Strategy details dialog
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  
  // Code validation
  const [codeValidationOpen, setCodeValidationOpen] = useState(false);
  const [validationCode, setValidationCode] = useState('');
  const [validationResult, setValidationResult] = useState(null);

  useEffect(() => {
    loadCategories();
    if (activeTab === 0) {
      loadStrategies();
    } else if (activeTab === 1) {
      loadMyStrategies();
    }
  }, [activeTab, filters]);

  const loadCategories = async () => {
    try {
      const response = await api.get('/marketplace/categories');
      if (response.data.success) {
        setCategories(response.data.categories);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadStrategies = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams(filters);
      const response = await api.get(`/marketplace/browse?${params}`);
      if (response.data.success) {
        setStrategies(response.data.strategies);
        setPagination(response.data.pagination);
      }
    } catch (error) {
      setError('Failed to load strategies');
      console.error('Error loading strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMyStrategies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/marketplace/my-strategies');
      if (response.data.success) {
        setMyStrategies(response.data.strategies);
      }
    } catch (error) {
      setError('Failed to load your strategies');
      console.error('Error loading my strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadData.strategy_name || !uploadData.file) {
      setError('Please provide strategy name and file');
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('strategy_file', uploadData.file);
      formData.append('strategy_name', uploadData.strategy_name);
      formData.append('strategy_description', uploadData.strategy_description);
      formData.append('is_public', uploadData.is_public.toString());

      const response = await api.post('/marketplace/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        setSuccess('Strategy uploaded successfully!');
        setUploadDialogOpen(false);
        setUploadData({
          strategy_name: '',
          strategy_description: '',
          is_public: false,
          file: null
        });
        if (activeTab === 1) {
          loadMyStrategies();
        }
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload strategy');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDeleteStrategy = async (strategyId) => {
    if (!window.confirm('Are you sure you want to delete this strategy?')) {
      return;
    }

    try {
      const response = await api.delete(`/marketplace/strategy/${strategyId}`);
      if (response.data.success) {
        setSuccess('Strategy deleted successfully!');
        loadMyStrategies();
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to delete strategy');
    }
  };

  const handleViewDetails = async (strategyId) => {
    try {
      const response = await api.get(`/marketplace/strategy/${strategyId}`);
      if (response.data.success) {
        setSelectedStrategy(response.data.strategy);
        setDetailsDialogOpen(true);
      }
    } catch (error) {
      setError('Failed to load strategy details');
    }
  };

  const validateCode = async () => {
    if (!validationCode.trim()) {
      setError('Please enter code to validate');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/marketplace/validate', {
        code: validationCode
      });
      
      if (response.data.success) {
        setValidationResult(response.data.validation);
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to validate code');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: key !== 'page' ? 1 : value
    }));
  };

  const getStrategyIcon = (category) => {
    switch (category) {
      case 'arbitrage': return <TrendingUpIcon />;
      case 'scalping': return <SpeedIcon />;
      case 'technical_analysis': return <ShowChartIcon />;
      default: return <CodeIcon />;
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Strategy Marketplace
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Browse Strategies" />
          <Tab label="My Strategies" />
          <Tab label="Code Validator" />
        </Tabs>
      </Paper>

      {/* Browse Strategies Tab */}
      {activeTab === 0 && (
        <Box>
          {/* Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  placeholder="Search strategies..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={filters.category}
                    onChange={(e) => handleFilterChange('category', e.target.value)}
                    label="Category"
                  >
                    {categories.map((category) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Sort By</InputLabel>
                  <Select
                    value={filters.sort_by}
                    onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                    label="Sort By"
                  >
                    <MenuItem value="created_at">Newest First</MenuItem>
                    <MenuItem value="name">Name A-Z</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* Strategies Grid */}
          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <Grid container spacing={3}>
                {strategies.map((strategy) => (
                  <Grid item xs={12} md={6} lg={4} key={strategy.id}>
                    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Box display="flex" alignItems="center" mb={2}>
                          {getStrategyIcon(strategy.metadata?.tags?.[0])}
                          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
                            {strategy.name}
                          </Typography>
                          {strategy.metadata?.risk_level && (
                            <Chip
                              label={strategy.metadata.risk_level}
                              color={getRiskColor(strategy.metadata.risk_level)}
                              size="small"
                            />
                          )}
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {strategy.description}
                        </Typography>
                        
                        {strategy.metadata?.tags && (
                          <Box sx={{ mb: 2 }}>
                            {strategy.metadata.tags.slice(0, 3).map((tag) => (
                              <Chip
                                key={tag}
                                label={tag}
                                size="small"
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5 }}
                              />
                            ))}
                          </Box>
                        )}
                        
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="caption" color="text.secondary">
                            {new Date(strategy.created_at).toLocaleDateString()}
                          </Typography>
                          <Button
                            size="small"
                            startIcon={<ViewIcon />}
                            onClick={() => handleViewDetails(strategy.id)}
                          >
                            View Details
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              
              {pagination.pages > 1 && (
                <Box display="flex" justifyContent="center" mt={4}>
                  <Pagination
                    count={pagination.pages}
                    page={pagination.page}
                    onChange={(e, page) => handleFilterChange('page', page)}
                  />
                </Box>
              )}
            </>
          )}
        </Box>
      )}

      {/* My Strategies Tab */}
      {activeTab === 1 && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6">
              My Strategies ({myStrategies.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<UploadIcon />}
              onClick={() => setUploadDialogOpen(true)}
            >
              Upload Strategy
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : myStrategies.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <CloudUploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No strategies uploaded yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Upload your first custom trading strategy to get started
              </Typography>
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={() => setUploadDialogOpen(true)}
              >
                Upload Strategy
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {myStrategies.map((strategy) => (
                <Grid item xs={12} md={6} lg={4} key={strategy.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={2}>
                        <CodeIcon sx={{ mr: 1 }} />
                        <Typography variant="h6" sx={{ flexGrow: 1 }}>
                          {strategy.name}
                        </Typography>
                        <Chip
                          label={strategy.is_public ? 'Public' : 'Private'}
                          color={strategy.is_public ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {strategy.description}
                      </Typography>
                      
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                        Created: {new Date(strategy.created_at).toLocaleDateString()}
                      </Typography>
                      
                      <Box display="flex" gap={1}>
                        <Button
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => handleViewDetails(strategy.id)}
                        >
                          View
                        </Button>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteStrategy(strategy.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {/* Code Validator Tab */}
      {activeTab === 2 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Strategy Code Validator
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Validate your strategy code before uploading to ensure it meets security and compliance requirements.
          </Typography>
          
          <Paper sx={{ p: 3 }}>
            <TextField
              fullWidth
              multiline
              rows={12}
              placeholder="Paste your strategy code here..."
              value={validationCode}
              onChange={(e) => setValidationCode(e.target.value)}
              sx={{ mb: 2 }}
            />
            
            <Button
              variant="contained"
              startIcon={<SecurityIcon />}
              onClick={validateCode}
              disabled={loading || !validationCode.trim()}
            >
              {loading ? 'Validating...' : 'Validate Code'}
            </Button>
            
            {validationResult && (
              <Box sx={{ mt: 3 }}>
                <Alert severity={validationResult.valid ? 'success' : 'error'}>
                  {validationResult.valid ? (
                    <Box>
                      <Typography variant="subtitle2">Code is valid!</Typography>
                      {validationResult.metadata && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2">
                            Strategy: {validationResult.metadata.name}
                          </Typography>
                          <Typography variant="body2">
                            Class: {validationResult.strategy_class}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Typography variant="subtitle2">
                      Validation failed: {validationResult.error}
                    </Typography>
                  )}
                </Alert>
              </Box>
            )}
          </Paper>
        </Box>
      )}

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Upload Custom Strategy</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Strategy Name"
              value={uploadData.strategy_name}
              onChange={(e) => setUploadData(prev => ({ ...prev, strategy_name: e.target.value }))}
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description"
              value={uploadData.strategy_description}
              onChange={(e) => setUploadData(prev => ({ ...prev, strategy_description: e.target.value }))}
              sx={{ mb: 2 }}
            />
            
            <input
              type="file"
              accept=".py"
              onChange={(e) => setUploadData(prev => ({ ...prev, file: e.target.files[0] }))}
              style={{ marginBottom: 16 }}
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={uploadData.is_public}
                  onChange={(e) => setUploadData(prev => ({ ...prev, is_public: e.target.checked }))}
                />
              }
              label="Make strategy public (visible to other users)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={uploadLoading || !uploadData.strategy_name || !uploadData.file}
          >
            {uploadLoading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Strategy Details Dialog */}
      <Dialog open={detailsDialogOpen} onClose={() => setDetailsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedStrategy?.name}
        </DialogTitle>
        <DialogContent>
          {selectedStrategy && (
            <Box>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedStrategy.description}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              {selectedStrategy.metadata && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Strategy Details
                  </Typography>
                  
                  {selectedStrategy.metadata.risk_level && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" component="span" sx={{ fontWeight: 'bold' }}>
                        Risk Level: 
                      </Typography>
                      <Chip
                        label={selectedStrategy.metadata.risk_level}
                        color={getRiskColor(selectedStrategy.metadata.risk_level)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  )}
                  
                  {selectedStrategy.metadata.minimum_capital && (
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Minimum Capital:</strong> ${selectedStrategy.metadata.minimum_capital}
                    </Typography>
                  )}
                  
                  {selectedStrategy.metadata.supported_timeframes && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Supported Timeframes:
                      </Typography>
                      <Box>
                        {selectedStrategy.metadata.supported_timeframes.map((timeframe) => (
                          <Chip
                            key={timeframe}
                            label={timeframe}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {selectedStrategy.metadata.tags && (
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Tags:
                      </Typography>
                      <Box>
                        {selectedStrategy.metadata.tags.map((tag) => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="caption" color="text.secondary">
                Created: {new Date(selectedStrategy.created_at).toLocaleDateString()}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategyMarketplace;