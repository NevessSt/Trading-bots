import React, {useState} from 'react';
import {
  View,
  TextInput,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInputProps,
  ViewStyle,
  TextStyle,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: string;
  rightIcon?: string;
  onRightIconPress?: () => void;
  containerStyle?: ViewStyle;
  inputStyle?: TextStyle;
  labelStyle?: TextStyle;
  variant?: 'outlined' | 'filled';
  size?: 'small' | 'medium' | 'large';
}

const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  onRightIconPress,
  containerStyle,
  inputStyle,
  labelStyle,
  variant = 'outlined',
  size = 'medium',
  secureTextEntry,
  ...textInputProps
}) => {
  const {theme} = useTheme();
  const [isFocused, setIsFocused] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const isPassword = secureTextEntry;
  const showPassword = isPassword && !isPasswordVisible;

  const getContainerStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      marginBottom: 16,
    };

    return baseStyle;
  };

  const getInputContainerStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      flexDirection: 'row',
      alignItems: 'center',
      borderRadius: 8,
    };

    // Size styles
    switch (size) {
      case 'small':
        baseStyle.minHeight = 40;
        baseStyle.paddingHorizontal = 12;
        break;
      case 'large':
        baseStyle.minHeight = 56;
        baseStyle.paddingHorizontal = 16;
        break;
      default: // medium
        baseStyle.minHeight = 48;
        baseStyle.paddingHorizontal = 14;
    }

    // Variant styles
    if (variant === 'filled') {
      baseStyle.backgroundColor = theme.colors.surfaceVariant;
    } else {
      baseStyle.borderWidth = 1;
      baseStyle.backgroundColor = theme.colors.surface;
    }

    // State styles
    if (error) {
      baseStyle.borderColor = theme.colors.error;
    } else if (isFocused) {
      baseStyle.borderColor = theme.colors.primary;
      if (variant === 'outlined') {
        baseStyle.borderWidth = 2;
      }
    } else {
      baseStyle.borderColor = theme.colors.outline;
    }

    return baseStyle;
  };

  const getInputStyle = (): TextStyle => {
    const baseStyle: TextStyle = {
      flex: 1,
      color: theme.colors.onSurface,
      paddingVertical: 0, // Remove default padding
      fontFamily: theme.typography?.body?.fontFamily,
    };

    // Enhanced size styles with better proportions
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

    return baseStyle;
  };

  const getLabelStyle = (): TextStyle => {
    const baseStyle: TextStyle = {
      fontSize: 14,
      fontWeight: '500',
      marginBottom: 6,
      color: error ? theme.colors.error : theme.colors.onSurface,
    };

    return baseStyle;
  };

  const getHelperTextStyle = (): TextStyle => {
    const baseStyle: TextStyle = {
      fontSize: 12,
      marginTop: 4,
      color: error ? theme.colors.error : theme.colors.onSurfaceVariant,
    };

    return baseStyle;
  };

  const getIconSize = (): number => {
    switch (size) {
      case 'small':
        return 18;
      case 'large':
        return 24;
      default: // medium
        return 20;
    }
  };

  const handlePasswordToggle = () => {
    setIsPasswordVisible(!isPasswordVisible);
  };

  const renderLeftIcon = () => {
    if (!leftIcon) return null;

    return (
      <Icon
        name={leftIcon}
        size={getIconSize()}
        color={theme.colors.onSurfaceVariant}
        style={styles.leftIcon}
      />
    );
  };

  const renderRightIcon = () => {
    if (isPassword) {
      return (
        <TouchableOpacity
          onPress={handlePasswordToggle}
          style={styles.rightIcon}
        >
          <Icon
            name={isPasswordVisible ? 'visibility-off' : 'visibility'}
            size={getIconSize()}
            color={theme.colors.onSurfaceVariant}
          />
        </TouchableOpacity>
      );
    }

    if (!rightIcon) return null;

    return (
      <TouchableOpacity
        onPress={onRightIconPress}
        style={styles.rightIcon}
        disabled={!onRightIconPress}
      >
        <Icon
          name={rightIcon}
          size={getIconSize()}
          color={theme.colors.onSurfaceVariant}
        />
      </TouchableOpacity>
    );
  };

  return (
    <View style={[getContainerStyle(), containerStyle]}>
      {label && (
        <Text style={[getLabelStyle(), labelStyle]}>{label}</Text>
      )}
      
      <View style={getInputContainerStyle()}>
        {renderLeftIcon()}
        
        <TextInput
          {...textInputProps}
          style={[getInputStyle(), inputStyle]}
          onFocus={(e) => {
            setIsFocused(true);
            textInputProps.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            textInputProps.onBlur?.(e);
          }}
          secureTextEntry={showPassword}
          placeholderTextColor={theme.colors.onSurfaceVariant}
        />
        
        {renderRightIcon()}
      </View>
      
      {(error || helperText) && (
        <Text style={getHelperTextStyle()}>
          {error || helperText}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  leftIcon: {
    marginRight: 8,
  },
  rightIcon: {
    marginLeft: 8,
    padding: 4,
  },
});

export default Input;