import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

const LoadingScreen = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: '#121212',
        color: '#fff'
      }}
    >
      <Box sx={{ mb: 4 }}>
        <img 
          src="./assets/icon.png" 
          alt="TradingBot Pro" 
          style={{ width: 80, height: 80 }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      </Box>
      
      <CircularProgress 
        size={60} 
        sx={{ 
          color: '#00d4aa',
          mb: 3
        }} 
      />
      
      <Typography 
        variant="h5" 
        sx={{ 
          mb: 1,
          fontWeight: 600,
          color: '#fff'
        }}
      >
        TradingBot Pro
      </Typography>
      
      <Typography 
        variant="body1" 
        sx={{ 
          color: '#888',
          textAlign: 'center'
        }}
      >
        Loading your trading dashboard...
      </Typography>
      
      <Box sx={{ mt: 4 }}>
        <Typography 
          variant="caption" 
          sx={{ 
            color: '#666',
            fontSize: '0.75rem'
          }}
        >
          Professional Cryptocurrency Trading Bot
        </Typography>
      </Box>
    </Box>
  );
};

export default LoadingScreen;