import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {Alert} from 'react-native';
import * as Keychain from 'react-native-keychain';

interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  preferences: {
    currency: string;
    language: string;
    notifications: boolean;
    biometricAuth: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isSetupComplete: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  logout: () => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<boolean>;
  updateUser: (updates: Partial<User>) => Promise<void>;
  checkSetupStatus: () => Promise<boolean>;
  completeSetup: () => Promise<void>;
  enableBiometricAuth: () => Promise<boolean>;
  authenticateWithBiometrics: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const STORAGE_KEYS = {
  USER: 'user_data',
  SETUP_COMPLETE: 'setup_complete',
  REMEMBER_ME: 'remember_me',
  BIOMETRIC_ENABLED: 'biometric_enabled',
};

const KEYCHAIN_SERVICE = 'TradingBotMobile';

export function AuthProvider({children}: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSetupComplete, setIsSetupComplete] = useState(false);

  const isAuthenticated = user !== null;

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      setIsLoading(true);
      
      // Check if user data exists
      const userData = await AsyncStorage.getItem(STORAGE_KEYS.USER);
      const setupComplete = await AsyncStorage.getItem(STORAGE_KEYS.SETUP_COMPLETE);
      const rememberMe = await AsyncStorage.getItem(STORAGE_KEYS.REMEMBER_ME);
      
      if (userData && rememberMe === 'true') {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        
        // Check if biometric auth is enabled and available
        const biometricEnabled = await AsyncStorage.getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
        if (biometricEnabled === 'true') {
          // In a real app, you might want to prompt for biometric auth here
          // For now, we'll just restore the session
        }
      }
      
      setIsSetupComplete(setupComplete === 'true');
    } catch (error) {
      console.error('Failed to initialize auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe = false): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      // In a real app, this would make an API call to authenticate
      // For demo purposes, we'll simulate authentication
      if (email && password.length >= 6) {
        const userData: User = {
          id: '1',
          email,
          name: email.split('@')[0],
          preferences: {
            currency: 'USD',
            language: 'en',
            notifications: true,
            biometricAuth: false,
          },
        };
        
        setUser(userData);
        await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
        await AsyncStorage.setItem(STORAGE_KEYS.REMEMBER_ME, rememberMe.toString());
        
        // Store credentials securely if remember me is enabled
        if (rememberMe) {
          await Keychain.setCredentials(KEYCHAIN_SERVICE, email, password);
        }
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      Alert.alert('Login Failed', 'Please check your credentials and try again.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      // In a real app, this would make an API call to register
      // For demo purposes, we'll simulate registration
      if (email && password.length >= 6 && name) {
        const userData: User = {
          id: Date.now().toString(),
          email,
          name,
          preferences: {
            currency: 'USD',
            language: 'en',
            notifications: true,
            biometricAuth: false,
          },
        };
        
        setUser(userData);
        await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
        await AsyncStorage.setItem(STORAGE_KEYS.REMEMBER_ME, 'true');
        
        // Store credentials securely
        await Keychain.setCredentials(KEYCHAIN_SERVICE, email, password);
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Registration failed:', error);
      Alert.alert('Registration Failed', 'Please try again.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      setUser(null);
      await AsyncStorage.removeItem(STORAGE_KEYS.USER);
      await AsyncStorage.removeItem(STORAGE_KEYS.REMEMBER_ME);
      await Keychain.resetCredentials(KEYCHAIN_SERVICE);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const updateUser = async (updates: Partial<User>): Promise<void> => {
    try {
      if (!user) return;
      
      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);
      await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updatedUser));
    } catch (error) {
      console.error('Failed to update user:', error);
      Alert.alert('Update Failed', 'Failed to save user preferences.');
    }
  };

  const checkSetupStatus = async (): Promise<boolean> => {
    try {
      const setupComplete = await AsyncStorage.getItem(STORAGE_KEYS.SETUP_COMPLETE);
      const isComplete = setupComplete === 'true';
      setIsSetupComplete(isComplete);
      return isComplete;
    } catch (error) {
      console.error('Failed to check setup status:', error);
      return false;
    }
  };

  const completeSetup = async (): Promise<void> => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.SETUP_COMPLETE, 'true');
      setIsSetupComplete(true);
    } catch (error) {
      console.error('Failed to complete setup:', error);
    }
  };

  const enableBiometricAuth = async (): Promise<boolean> => {
    try {
      const biometryType = await Keychain.getSupportedBiometryType();
      
      if (biometryType) {
        await AsyncStorage.setItem(STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');
        
        if (user) {
          await updateUser({
            preferences: {
              ...user.preferences,
              biometricAuth: true,
            },
          });
        }
        
        return true;
      }
      
      Alert.alert('Biometric Authentication', 'Biometric authentication is not available on this device.');
      return false;
    } catch (error) {
      console.error('Failed to enable biometric auth:', error);
      Alert.alert('Error', 'Failed to enable biometric authentication.');
      return false;
    }
  };

  const authenticateWithBiometrics = async (): Promise<boolean> => {
    try {
      const credentials = await Keychain.getCredentials(KEYCHAIN_SERVICE, {
        authenticationType: Keychain.AUTHENTICATION_TYPE.BIOMETRICS,
        accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_CURRENT_SET,
      });
      
      if (credentials && credentials.username && credentials.password) {
        return await login(credentials.username, credentials.password, true);
      }
      
      return false;
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  };

  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    isSetupComplete,
    login,
    logout,
    register,
    updateUser,
    checkSetupStatus,
    completeSetup,
    enableBiometricAuth,
    authenticateWithBiometrics,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export type {User, AuthContextType};