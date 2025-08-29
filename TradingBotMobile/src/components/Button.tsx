import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ViewStyle,
  TextStyle,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  iconPosition?: 'left' | 'right';
  style?: ViewStyle;
  textStyle?: TextStyle;
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  style,
  textStyle,
  fullWidth = false,
}) => {
  const {theme} = useTheme();

  const getButtonStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      borderRadius: theme.borderRadius?.lg || 12,
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'row',
    };

    // Enhanced size styles with better proportions
    switch (size) {
      case 'small':
        baseStyle.paddingHorizontal = theme.spacing?.md || 16;
        baseStyle.paddingVertical = theme.spacing?.sm || 8;
        baseStyle.minHeight = 36;
        baseStyle.borderRadius = theme.borderRadius?.md || 8;
        break;
      case 'large':
        baseStyle.paddingHorizontal = theme.spacing?.xl || 32;
        baseStyle.paddingVertical = theme.spacing?.lg || 16;
        baseStyle.minHeight = 56;
        baseStyle.borderRadius = theme.borderRadius?.xl || 16;
        break;
      default: // medium
        baseStyle.paddingHorizontal = theme.spacing?.lg || 24;
        baseStyle.paddingVertical = theme.spacing?.md || 12;
        baseStyle.minHeight = 48;
        baseStyle.borderRadius = theme.borderRadius?.lg || 12;
    }

    // Enhanced variant styles with modern design
    switch (variant) {
      case 'secondary':
        baseStyle.backgroundColor = theme.colors.surfaceVariant || theme.colors.surface;
        baseStyle.borderWidth = 1;
        baseStyle.borderColor = theme.colors.border;
        if (theme.shadows?.sm) {
          Object.assign(baseStyle, theme.shadows.sm);
        }
        break;
      case 'outline':
        baseStyle.backgroundColor = 'transparent';
        baseStyle.borderWidth = 2;
        baseStyle.borderColor = theme.colors.primary;
        break;
      case 'text':
        baseStyle.backgroundColor = 'transparent';
        baseStyle.borderWidth = 0;
        break;
      default: // primary
        baseStyle.backgroundColor = theme.colors.primary;
        baseStyle.borderWidth = 0;
        if (theme.shadows?.md) {
          Object.assign(baseStyle, theme.shadows.md);
        }
    }

    // Disabled state
    if (disabled || loading) {
      baseStyle.opacity = 0.5;
    }

    // Full width
    if (fullWidth) {
      baseStyle.width = '100%';
    }

    return baseStyle;
  };

  const getTextStyle = (): TextStyle => {
    const baseStyle: TextStyle = {
      fontWeight: '600',
    };

    // Size styles
    switch (size) {
      case 'small':
        baseStyle.fontSize = 14;
        break;
      case 'large':
        baseStyle.fontSize = 18;
        break;
      default: // medium
        baseStyle.fontSize = 16;
    }

    // Variant styles
    switch (variant) {
      case 'secondary':
        baseStyle.color = theme.colors.onSurfaceVariant;
        break;
      case 'outline':
        baseStyle.color = theme.colors.primary;
        break;
      case 'text':
        baseStyle.color = theme.colors.primary;
        break;
      default: // primary
        baseStyle.color = theme.colors.onPrimary;
    }

    return baseStyle;
  };

  const getIconSize = (): number => {
    switch (size) {
      case 'small':
        return 16;
      case 'large':
        return 24;
      default: // medium
        return 20;
    }
  };

  const getIconColor = (): string => {
    switch (variant) {
      case 'secondary':
        return theme.colors.onSurfaceVariant;
      case 'outline':
      case 'text':
        return theme.colors.primary;
      default: // primary
        return theme.colors.onPrimary;
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <ActivityIndicator
          size={size === 'small' ? 'small' : 'small'}
          color={getIconColor()}
        />
      );
    }

    const iconElement = icon ? (
      <Icon
        name={icon}
        size={getIconSize()}
        color={getIconColor()}
        style={{
          marginRight: iconPosition === 'left' ? 8 : 0,
          marginLeft: iconPosition === 'right' ? 8 : 0,
        }}
      />
    ) : null;

    const textElement = (
      <Text style={[getTextStyle(), textStyle]}>{title}</Text>
    );

    if (iconPosition === 'right') {
      return (
        <>
          {textElement}
          {iconElement}
        </>
      );
    }

    return (
      <>
        {iconElement}
        {textElement}
      </>
    );
  };

  return (
    <TouchableOpacity
      style={[getButtonStyle(), style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {renderContent()}
    </TouchableOpacity>
  );
};

export default Button;