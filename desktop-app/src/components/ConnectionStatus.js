import React from 'react';
import { Box, Typography, Tooltip } from '@mui/material';
import { Circle } from '@mui/icons-material';

const ConnectionStatus = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: '#4caf50',
          text: 'Connected',
          description: 'Connected to trading backend'
        };
      case 'connecting':
        return {
          color: '#ff9800',
          text: 'Connecting',
          description: 'Connecting to trading backend...'
        };
      case 'disconnected':
      default:
        return {
          color: '#f44336',
          text: 'Disconnected',
          description: 'Disconnected from trading backend'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Tooltip title={config.description}>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        mr: 2,
        cursor: 'pointer'
      }}>
        <Circle 
          sx={{ 
            color: config.color, 
            fontSize: 12, 
            mr: 1,
            animation: status === 'connecting' ? 'pulse 1.5s infinite' : 'none'
          }} 
        />
        <Typography variant="body2" sx={{ color: config.color }}>
          {config.text}
        </Typography>
      </Box>
    </Tooltip>
  );
};

export default ConnectionStatus;