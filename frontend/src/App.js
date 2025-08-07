import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import useAuthStore from './stores/useAuthStore';

// Layout
import Layout from './components/Layout';

// Components
import Dashboard from './components/Dashboard';
import BotList from './components/Bots/BotList';
import BotDetail from './components/Bots/BotDetail';
import BotForm from './components/Bots/BotForm';
import TradesList from './components/Trades';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import NotFound from './pages/NotFound';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, checkAuth } = useAuthStore();
  
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  
  if (isAuthenticated === null) {
    // Still checking authentication
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Dashboard routes */}
        <Route element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route path="/" element={<Dashboard />} />
          <Route path="/bots" element={<BotList />} />
          <Route path="/bots/new" element={<BotForm />} />
          <Route path="/bots/:botId" element={<BotDetail />} />
          <Route path="/bots/:botId/edit" element={<BotForm />} />
          <Route path="/trades" element={<TradesList />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
        
        {/* 404 route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export default App;