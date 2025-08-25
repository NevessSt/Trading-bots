import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const RiskDisclaimerContext = createContext();

export const useRiskDisclaimer = () => {
  const context = useContext(RiskDisclaimerContext);
  if (!context) {
    throw new Error('useRiskDisclaimer must be used within a RiskDisclaimerProvider');
  }
  return context;
};

export const RiskDisclaimerProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [hasAcceptedRisk, setHasAcceptedRisk] = useState(false);
  const [showRiskDisclaimer, setShowRiskDisclaimer] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user has accepted risk disclaimer
  useEffect(() => {
    if (isAuthenticated && user) {
      checkRiskAcceptance();
    } else {
      setIsLoading(false);
    }
  }, [isAuthenticated, user]);

  const checkRiskAcceptance = () => {
    try {
      // Check localStorage for risk acceptance
      const riskAcceptanceKey = `risk_accepted_${user.id}`;
      const acceptanceData = localStorage.getItem(riskAcceptanceKey);
      
      if (acceptanceData) {
        const { accepted, timestamp } = JSON.parse(acceptanceData);
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000); // 30 days in milliseconds
        
        // Check if acceptance is still valid (within 30 days)
        if (accepted && timestamp > thirtyDaysAgo) {
          setHasAcceptedRisk(true);
        } else {
          // Acceptance expired, need to show disclaimer again
          setHasAcceptedRisk(false);
        }
      } else {
        setHasAcceptedRisk(false);
      }
    } catch (error) {
      console.error('Error checking risk acceptance:', error);
      setHasAcceptedRisk(false);
    } finally {
      setIsLoading(false);
    }
  };

  const acceptRiskDisclaimer = () => {
    try {
      const riskAcceptanceKey = `risk_accepted_${user.id}`;
      const acceptanceData = {
        accepted: true,
        timestamp: Date.now(),
        version: '1.0' // Version of the disclaimer
      };
      
      localStorage.setItem(riskAcceptanceKey, JSON.stringify(acceptanceData));
      setHasAcceptedRisk(true);
      setShowRiskDisclaimer(false);
    } catch (error) {
      console.error('Error saving risk acceptance:', error);
    }
  };

  const declineRiskDisclaimer = () => {
    setShowRiskDisclaimer(false);
    // Optionally redirect to a safe page or show a message
  };

  const requireRiskAcceptance = () => {
    if (!hasAcceptedRisk && isAuthenticated) {
      setShowRiskDisclaimer(true);
      return false;
    }
    return true;
  };

  const resetRiskAcceptance = () => {
    try {
      const riskAcceptanceKey = `risk_accepted_${user?.id}`;
      localStorage.removeItem(riskAcceptanceKey);
      setHasAcceptedRisk(false);
    } catch (error) {
      console.error('Error resetting risk acceptance:', error);
    }
  };

  const value = {
    hasAcceptedRisk,
    showRiskDisclaimer,
    isLoading,
    acceptRiskDisclaimer,
    declineRiskDisclaimer,
    requireRiskAcceptance,
    resetRiskAcceptance,
    setShowRiskDisclaimer
  };

  return (
    <RiskDisclaimerContext.Provider value={value}>
      {children}
    </RiskDisclaimerContext.Provider>
  );
};

export default RiskDisclaimerContext;