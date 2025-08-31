import React, { useState, useEffect } from 'react';
import { Switch, FormControlLabel, Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box, Chip } from '@mui/material';
import { Warning, Info } from '@mui/icons-material';
import demoDataService from '../services/demoDataService';

const DemoModeToggle = ({ onModeChange }) => {
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingMode, setPendingMode] = useState(false);

  useEffect(() => {
    // Initialize demo mode state
    const demoMode = demoDataService.isDemoMode();
    setIsDemoMode(demoMode);
  }, []);

  const handleToggleChange = (event) => {
    const newMode = event.target.checked;
    setPendingMode(newMode);
    setShowConfirmDialog(true);
  };

  const handleConfirmModeChange = () => {
    setIsDemoMode(pendingMode);
    demoDataService.setDemoMode(pendingMode);
    
    if (onModeChange) {
      onModeChange(pendingMode);
    }
    
    setShowConfirmDialog(false);
    
    // Reload the page to refresh all data
    window.location.reload();
  };

  const handleCancelModeChange = () => {
    setShowConfirmDialog(false);
    setPendingMode(isDemoMode);
  };

  const resetDemoData = () => {
    if (isDemoMode) {
      demoDataService.resetDemoData();
      window.location.reload();
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {/* Demo Mode Indicator */}
      {isDemoMode && (
        <Chip
          label="DEMO MODE"
          color="warning"
          variant="filled"
          size="small"
          sx={{
            fontWeight: 'bold',
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.7 },
              '100%': { opacity: 1 }
            }
          }}
        />
      )}
      
      {/* Mode Toggle Switch */}
      <FormControlLabel
        control={
          <Switch
            checked={isDemoMode}
            onChange={handleToggleChange}
            color="warning"
            size="medium"
          />
        }
        label={
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {isDemoMode ? 'Demo Mode' : 'Live Mode'}
          </Typography>
        }
      />
      
      {/* Reset Demo Data Button */}
      {isDemoMode && (
        <Button
          variant="outlined"
          size="small"
          onClick={resetDemoData}
          sx={{ ml: 1 }}
        >
          Reset Demo Data
        </Button>
      )}

      {/* Confirmation Dialog */}
      <Dialog
        open={showConfirmDialog}
        onClose={handleCancelModeChange}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {pendingMode ? (
            <>
              <Warning color="warning" />
              Switch to Demo Mode?
            </>
          ) : (
            <>
              <Info color="info" />
              Switch to Live Mode?
            </>
          )}
        </DialogTitle>
        
        <DialogContent>
          {pendingMode ? (
            <Box>
              <Typography variant="body1" gutterBottom>
                You are about to switch to <strong>Demo Mode</strong>. In demo mode:
              </Typography>
              <Box component="ul" sx={{ mt: 2, pl: 2 }}>
                <Typography component="li" variant="body2" gutterBottom>
                  All trading data will be simulated with fake data
                </Typography>
                <Typography component="li" variant="body2" gutterBottom>
                  You'll start with a virtual $100,000 portfolio
                </Typography>
                <Typography component="li" variant="body2" gutterBottom>
                  No real trades will be executed
                </Typography>
                <Typography component="li" variant="body2" gutterBottom>
                  Perfect for testing strategies without financial risk
                </Typography>
              </Box>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                <Typography variant="body2" color="warning.dark">
                  <strong>Note:</strong> This is ideal for buyers who want to test the platform before connecting their real trading accounts.
                </Typography>
              </Box>
            </Box>
          ) : (
            <Box>
              <Typography variant="body1" gutterBottom>
                You are about to switch to <strong>Live Mode</strong>. In live mode:
              </Typography>
              <Box component="ul" sx={{ mt: 2, pl: 2 }}>
                <Typography component="li" variant="body2" gutterBottom>
                  Real trading data from your connected exchange accounts
                </Typography>
                <Typography component="li" variant="body2" gutterBottom>
                  Actual trades can be executed with real money
                </Typography>
                <Typography component="li" variant="body2" gutterBottom>
                  Requires valid API keys and exchange connections
                </Typography>
                <Typography component="li" variant="body2" gutterBottom>
                  All profits and losses will be real
                </Typography>
              </Box>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                <Typography variant="body2" color="error.dark">
                  <strong>Warning:</strong> Make sure you have properly configured your API keys and risk management settings before switching to live mode.
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleCancelModeChange} color="inherit">
            Cancel
          </Button>
          <Button 
            onClick={handleConfirmModeChange} 
            variant="contained"
            color={pendingMode ? 'warning' : 'primary'}
          >
            {pendingMode ? 'Switch to Demo' : 'Switch to Live'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DemoModeToggle