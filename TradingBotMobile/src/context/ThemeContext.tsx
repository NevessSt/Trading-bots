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

// Custom light theme with trading colors
const lightTheme: CustomTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#1976D2',
    onPrimary: '#FFFFFF',
    primaryContainer: '#E3F2FD',
    onPrimaryContainer: '#0D47A1',
    secondary: '#424242',
    onSecondary: '#FFFFFF',
    secondaryContainer: '#F5F5F5',
    onSecondaryContainer: '#212121',
    // Trading-specific colors
    profit: '#4CAF50',
    loss: '#F44336',
    warning: '#FF9800',
    info: '#2196F3',
  },
};

// Custom dark theme with trading colors
const darkTheme: CustomTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: '#90CAF9',
    onPrimary: '#0D47A1',
    primaryContainer: '#1565C0',
    onPrimaryContainer: '#E3F2FD',
    secondary: '#BDBDBD',
    onSecondary: '#424242',
    secondaryContainer: '#616161',
    onSecondaryContainer: '#F5F5F5',
    // Trading-specific colors
    profit: '#66BB6A',
    loss: '#EF5350',
    warning: '#FFB74D',
    info: '#42A5F5',
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