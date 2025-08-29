import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import {useColorScheme} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {MD3LightTheme, MD3DarkTheme} from 'react-native-paper';

type ThemeType = 'light' | 'dark' | 'system';

interface CustomTheme {
  dark: boolean;
  colors: {
    primary: string;
    onPrimary: string;
    primaryContainer: string;
    onPrimaryContainer: string;
    secondary: string;
    onSecondary: string;
    secondaryContainer: string;
    onSecondaryContainer: string;
    tertiary: string;
    onTertiary: string;
    tertiaryContainer: string;
    onTertiaryContainer: string;
    error: string;
    onError: string;
    errorContainer: string;
    onErrorContainer: string;
    background: string;
    onBackground: string;
    surface: string;
    onSurface: string;
    surfaceVariant: string;
    onSurfaceVariant: string;
    outline: string;
    outlineVariant: string;
    shadow: string;
    scrim: string;
    inverseSurface: string;
    inverseOnSurface: string;
    inversePrimary: string;
    elevation: {
      level0: string;
      level1: string;
      level2: string;
      level3: string;
      level4: string;
      level5: string;
    };
    surfaceDisabled: string;
    onSurfaceDisabled: string;
    backdrop: string;
    // Trading-specific colors
    profit: string;
    loss: string;
    warning: string;
    info: string;
  };
}

interface ThemeContextType {
  theme: CustomTheme;
  themeType: ThemeType;
  setThemeType: (type: ThemeType) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Custom light theme with enhanced design system
const lightTheme: CustomTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    // Primary brand colors - Modern blue gradient system
    primary: '#2563EB', // Blue-600
    onPrimary: '#FFFFFF',
    primaryContainer: '#E3F2FD',
    onPrimaryContainer: '#0D47A1',
    secondary: '#7C3AED', // Violet-600
    onSecondary: '#FFFFFF',
    secondaryContainer: '#F5F5F5',
    onSecondaryContainer: '#212121',
    // Enhanced background system
    background: '#FFFFFF',
    surface: '#F8FAFC', // Slate-50
    // Trading-specific colors with modern palette
    profit: '#10B981', // Emerald-500
    loss: '#EF4444', // Red-500
    warning: '#F59E0B', // Amber-500
    info: '#3B82F6', // Blue-500
  },
};

// Custom dark theme with enhanced design system
const darkTheme: CustomTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    // Primary brand colors - Adjusted for dark mode
    primary: '#3B82F6', // Blue-500 (brighter for dark)
    onPrimary: '#FFFFFF',
    primaryContainer: '#1E3A8A', // Blue-900
    onPrimaryContainer: '#DBEAFE', // Blue-100
    secondary: '#8B5CF6', // Violet-500
    onSecondary: '#FFFFFF',
    secondaryContainer: '#4C1D95', // Violet-900
    onSecondaryContainer: '#EDE9FE', // Violet-100
    // Enhanced dark background system
    background: '#0F172A', // Slate-900
    surface: '#1E293B', // Slate-800
    // Trading-specific colors - Enhanced for dark mode visibility
    profit: '#34D399', // Emerald-400 (brighter for dark backgrounds)
    loss: '#F87171', // Red-400 (softer for dark backgrounds)
    warning: '#FBBF24', // Amber-400
    info: '#60A5FA', // Blue-400
  },
};

interface ThemeProviderProps {
  children: ReactNode;
  initialTheme?: ThemeType;
}

export function ThemeProvider({children, initialTheme = 'system'}: ThemeProviderProps) {
  const systemColorScheme = useColorScheme();
  const [themeType, setThemeType] = useState<ThemeType>(initialTheme);
  const [currentTheme, setCurrentTheme] = useState<CustomTheme>(lightTheme);

  // Determine if dark mode should be active
  const isDark = themeType === 'dark' || (themeType === 'system' && systemColorScheme === 'dark');

  useEffect(() => {
    // Load saved theme preference
    const loadTheme = async () => {
      try {
        const savedTheme = await AsyncStorage.getItem('theme');
        if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
          setThemeType(savedTheme as ThemeType);
        }
      } catch (error) {
        console.error('Failed to load theme preference:', error);
      }
    };

    loadTheme();
  }, []);

  useEffect(() => {
    // Update current theme based on theme type and system preference
    setCurrentTheme(isDark ? darkTheme : lightTheme);
  }, [isDark]);

  const handleSetThemeType = async (type: ThemeType) => {
    try {
      setThemeType(type);
      await AsyncStorage.setItem('theme', type);
    } catch (error) {
      console.error('Failed to save theme preference:', error);
    }
  };

  const contextValue: ThemeContextType = {
    theme: currentTheme,
    themeType,
    setThemeType: handleSetThemeType,
    isDark,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export {lightTheme, darkTheme};
export type {CustomTheme, ThemeType};