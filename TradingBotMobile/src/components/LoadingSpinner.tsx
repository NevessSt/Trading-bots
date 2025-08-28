import React, {useEffect, useRef} from 'react';
import {
  View,
  Animated,
  StyleSheet,
  ViewStyle,
} from 'react-native';
import {useTheme} from '../context/ThemeContext';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  style?: ViewStyle;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color,
  style,
}) => {
  const {theme} = useTheme();
  const spinValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const spin = () => {
      spinValue.setValue(0);
      Animated.timing(spinValue, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }).start(() => spin());
    };

    spin();
  }, [spinValue]);

  const getSize = (): number => {
    switch (size) {
      case 'small':
        return 20;
      case 'large':
        return 40;
      default: // medium
        return 30;
    }
  };

  const getBorderWidth = (): number => {
    switch (size) {
      case 'small':
        return 2;
      case 'large':
        return 4;
      default: // medium
        return 3;
    }
  };

  const spinnerColor = color || theme.colors.primary;
  const spinnerSize = getSize();
  const borderWidth = getBorderWidth();

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={[styles.container, style]}>
      <Animated.View
        style={[
          styles.spinner,
          {
            width: spinnerSize,
            height: spinnerSize,
            borderWidth,
            borderColor: `${spinnerColor}30`,
            borderTopColor: spinnerColor,
            transform: [{rotate: spin}],
          },
        ]}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  spinner: {
    borderRadius: 50,
  },
});

export default LoadingSpinner;