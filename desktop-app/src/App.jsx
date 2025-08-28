import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Dashboard from './components/Dashboard';
import SetupWizardDesktop from './components/SetupWizardDesktop';
import LoadingScreen from './components/LoadingScreen';
import UpdateManager from './UpdateManager';
import UpdateNotification from './UpdateNotification';
import './App.css';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4aa',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [setupStatus, setSetupStatus] = useState({ completed: false, skipped: false });
  const [appReady, setAppReady] = useState(false);
  const [showUpdateManager, setShowUpdateManager] = useState(false);
  const [showUpdateNotification, setShowUpdateNotification] = useState(true);

  useEffect(() => {
    // Initialize app and check setup status
    const initializeApp = async () => {
      try {
        // Check if setup wizard should be shown
        if (window.electronAPI && window.electronAPI.getSetupStatus) {
          const status = await window.electronAPI.getSetupStatus();
          setSetupStatus(status);
          
          // Show setup wizard if not completed and not skipped
          if (!status.completed && !status.skipped) {
            setShowSetupWizard(true);
          }
        }
        
        setAppReady(true);
      } catch (error) {
        console.error('Failed to initialize app:', error);
        setAppReady(true); // Continue anyway
      } finally {
        setIsLoading(false);
      }
    };

    // Simulate loading time
    setTimeout(initializeApp, 2000);
  }, []);

  const handleSetupComplete = () => {
    setShowSetupWizard(false);
    setSetupStatus({ completed: true, skipped: false });
  };

  const handleSetupSkip = () => {
    setShowSetupWizard(false);
    setSetupStatus({ completed: false, skipped: true });
  };

  const handleShowSetupWizard = () => {
    setShowSetupWizard(true);
  };

  const handleResetSetup = async () => {
    try {
      if (window.electronAPI && window.electronAPI.resetSetup) {
        await window.electronAPI.resetSetup();
        setSetupStatus({ completed: false, skipped: false });
        setShowSetupWizard(true);
      }
    } catch (error) {
      console.error('Failed to reset setup:', error);
    }
  };

  const handleOpenUpdateManager = () => {
    setShowUpdateManager(true);
  };

  const handleCloseUpdateManager = () => {
    setShowUpdateManager(false);
  };

  const handleDismissUpdateNotification = () => {
    setShowUpdateNotification(false);
  };

  if (isLoading) {
    return (
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <LoadingScreen />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <div className="app">
        {showSetupWizard && (
          <SetupWizardDesktop
            onComplete={handleSetupComplete}
            onSkip={handleSetupSkip}
          />
        )}
        
        {appReady && (
          <Dashboard
            setupStatus={setupStatus}
            onShowSetupWizard={handleShowSetupWizard}
            onResetSetup={handleResetSetup}
            onOpenUpdateManager={handleOpenUpdateManager}
          />
        )}
        
        {showUpdateManager && (
          <UpdateManager onClose={handleCloseUpdateManager} />
        )}
        
        {showUpdateNotification && (
          <UpdateNotification
            onOpenUpdateManager={handleOpenUpdateManager}
            onDismiss={handleDismissUpdateNotification}
          />
        )}
      </div>
    </ThemeProvider>
  );
}

export default App;