import React from 'react';
import {View, StyleSheet, ViewStyle} from 'react-native';
import {useTheme} from '../context/ThemeContext';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'elevated' | 'outlined' | 'filled';
  padding?: 'sm' | 'md' | 'lg' | 'xl' | 'none';
  onPress?: () => void;
}

const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  padding = 'md',
  style,
  onPress,
  ...props
}) => {
  const {theme} = useTheme();

  const getCardStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      borderRadius: theme.borderRadius?.xl || 16,
      backgroundColor: theme.colors.surface,
      overflow: 'hidden', // Ensure content respects border radius
    };

    // Enhanced padding styles with theme spacing
    const paddingValue = {
      sm: theme.spacing?.sm || 8,
      md: theme.spacing?.lg || 16,
      lg: theme.spacing?.xl || 24,
      xl: theme.spacing?.xxl || 32,
      none: 0,
    }[padding] || theme.spacing?.lg || 16;

    baseStyle.padding = paddingValue;

    // Enhanced variant styles with modern design
    switch (variant) {
      case 'outlined':
        baseStyle.borderWidth = 1;
        baseStyle.borderColor = theme.colors.border || theme.colors.outline;
        baseStyle.backgroundColor = theme.colors.surface;
        break;
      case 'filled':
        baseStyle.backgroundColor = theme.colors.surfaceVariant || theme.colors.surface;
        baseStyle.borderWidth = 0;
        break;
      default: // elevated
        // Enhanced shadow with theme shadows
        if (theme.shadows?.lg) {
          Object.assign(baseStyle, theme.shadows.lg);
        } else {
          // Fallback shadow
          baseStyle.shadowColor = '#000';
          baseStyle.shadowOffset = { width: 0, height: 4 };
          baseStyle.shadowOpacity = 0.1;
          baseStyle.shadowRadius = 8;
          baseStyle.elevation = 5;
        }
        baseStyle.borderWidth = 0;
    }

    // Add subtle border for better definition in light themes
    if (variant !== 'outlined' && !baseStyle.borderWidth) {
      baseStyle.borderWidth = 0.5;
      baseStyle.borderColor = theme.colors.borderLight || theme.colors.border || 'transparent';
    }

    return baseStyle;
  };

  return (
    <View
      style={[
        getCardStyle(),
        style,
      ]}
      {...props}
    >
      {children}
    </View>
  );
};



export default Card;