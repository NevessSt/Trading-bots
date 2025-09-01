import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LicenseProvider } from './contexts/LicenseContext';
import { RiskDisclaimerProvider, useRiskDisclaimer } from './contexts/RiskDisclaimerContext';
import { NotificationProvider } from './contexts/NotificationContext';
import RiskDisclaimer from './components/RiskDisclaimer';
import Footer from './components/Footer';

import { ThemeProvider } from './contexts/ThemeContext';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Register from './components/Register';
import Profile from './components/Profile';
import Contact from './components/Contact';
import TradingBots from './pages/TradingBots';
import Performance from './pages/Performance';
import Settings from './pages/Settings';
import Billing from './pages/Billing';
import License from './pages/License';

import AdminPanel from './components/AdminPanel';
import LoadingSpinner from './components/LoadingSpinner';
import ProDashboard from './components/ProDashboard/ProDashboard';
import ProSettings from './components/Settings/ProSettings';
import APIConnectionTest from './components/APIConnectionTest';
import StrategyManager from './components/StrategyManager';
import StrategyMarketplace from './components/StrategyMarketplace';
import ExchangeManager from './components/ExchangeManager';
import NotificationDashboard from './components/NotificationDashboard';
import EnhancedDashboardIntegration from './components/EnhancedDashboardIntegration';
import TradingDashboard from './components/TradingDashboard';

const queryClient = new QueryClient();

// MetaMask blocking is now handled in index.html before React loads

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (adminOnly && !isAdmin) {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
};

// Public Route Component (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
};

function AppContent() {
  const { isAuthenticated } = useAuth();
  const { showRiskDisclaimer, acceptRiskDisclaimer, declineRiskDisclaimer } = useRiskDisclaimer();

  // MetaMask blocking is handled in index.html before React loads

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300">
      {/* Risk Disclaimer Modal */}
      <RiskDisclaimer
        isOpen={showRiskDisclaimer}
        onAccept={acceptRiskDisclaimer}
        onDecline={declineRiskDisclaimer}
      />
      <Toaster 
        position="top-right" 
        toastOptions={{
          duration: 4000,
          className: 'dark:bg-slate-800 dark:text-slate-100',
          style: {
            background: 'rgb(var(--bg-elevated))',
            color: 'rgb(var(--text-primary))',
            border: '1px solid rgb(var(--border-primary))',
            borderRadius: '12px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#22c55e',
              secondary: 'rgb(var(--bg-elevated))',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: 'rgb(var(--bg-elevated))',
            },
          },
        }}
      />
      
      {isAuthenticated && <Navbar />}
      
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } 
        />
        
        {/* Protected Routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/bots" 
          element={
            <ProtectedRoute>
              <TradingBots />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/strategies" 
          element={
            <ProtectedRoute>
              <StrategyManager />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/marketplace" 
          element={
            <ProtectedRoute>
              <StrategyMarketplace />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/exchanges" 
          element={
            <ProtectedRoute>
              <ExchangeManager />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/performance" 
          element={
            <ProtectedRoute>
              <Performance />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/settings" 
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/billing" 
          element={
            <ProtectedRoute>
              <Billing />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/license" 
          element={
            <ProtectedRoute>
              <License />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/contact" 
          element={
            <ProtectedRoute>
              <Contact />
            </ProtectedRoute>
          } 
        />
        
        {/* Pro Dashboard Routes */}
        <Route 
          path="/pro-dashboard" 
          element={
            <ProtectedRoute>
              <ProDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/pro-settings" 
          element={
            <ProtectedRoute>
              <ProSettings />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/api-test" 
          element={
            <ProtectedRoute>
              <APIConnectionTest />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/notifications" 
          element={
            <ProtectedRoute>
              <NotificationDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/enhanced-dashboard" 
          element={
            <ProtectedRoute>
              <EnhancedDashboardIntegration />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/trading-dashboard" 
          element={
            <ProtectedRoute>
              <TradingDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Admin Routes */}
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute adminOnly={true}>
              <AdminPanel />
            </ProtectedRoute>
          } 
        />
        
        {/* Default Route */}
        <Route 
          path="/" 
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
        />
        
        {/* Catch all route */}
        <Route 
          path="*" 
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
        />
      </Routes>
      
      {/* Footer - shown on all pages */}
      <Footer />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <NotificationProvider>
            <LicenseProvider>
              <RiskDisclaimerProvider>
                <AppContent />
              </RiskDisclaimerProvider>
            </LicenseProvider>
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;