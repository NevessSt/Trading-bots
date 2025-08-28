/**
 * Context Index - Export all context providers for easy importing
 */

export { ThemeProvider, useTheme } from './ThemeContext';
export { AuthProvider, useAuth } from './AuthContext';
export { TradingProvider, useTrading } from './TradingContext';

// Re-export context types
export type {
  CustomTheme,
  ThemeContextType,
  AuthContextType,
  TradingContextType,
} from '../types';