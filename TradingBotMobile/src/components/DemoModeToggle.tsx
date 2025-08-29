import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useDemoTrading } from '../contexts/DemoTradingContext';

interface DemoModeToggleProps {
  showLabel?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const DemoModeToggle: React.FC<DemoModeToggleProps> = ({ 
  showLabel = true, 
  size = 'medium' 
}) => {
  const { theme } = useTheme();
  const { isDemoMode, toggleDemoMode, isLoading } = useDemoTrading();

  const handleToggle = () => {
    if (isLoading) return;

    if (isDemoMode) {
      // Switching to live mode - show warning
      Alert.alert(
        'Switch to Live Trading',
        'Are you sure you want to switch to live trading? This will use real money and execute actual trades.',
        [
          {
            text: 'Cancel',
            style: 'cancel',
          },
          {
            text: 'Switch to Live',
            style: 'destructive',
            onPress: toggleDemoMode,
          },
        ]
      );
    } else {
      // Switching to demo mode - no warning needed
      toggleDemoMode();
    }
  };

  const styles = StyleSheet.create({
    container: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: theme.spacing.sm,
    },
    toggleContainer: {
      flexDirection: 'row',
      backgroundColor: theme.colors.surface,
      borderRadius: theme.borderRadius.lg,
      padding: theme.spacing.xs,
      borderWidth: 1,
      borderColor: theme.colors.border,
      shadowColor: theme.colors.shadow,
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.1,
      shadowRadius: 3,
      elevation: 3,
    },
    toggleButton: {
      paddingHorizontal: size === 'small' ? theme.spacing.sm : 
                        size === 'large' ? theme.spacing.lg : theme.spacing.md,
      paddingVertical: size === 'small' ? theme.spacing.xs : 
                      size === 'large' ? theme.spacing.md : theme.spacing.sm,
      borderRadius: theme.borderRadius.md,
      minWidth: size === 'small' ? 60 : size === 'large' ? 80 : 70,
      alignItems: 'center',
      justifyContent: 'center',
    },
    activeButton: {
      backgroundColor: isDemoMode ? theme.colors.warning : theme.colors.error,
      shadowColor: isDemoMode ? theme.colors.warning : theme.colors.error,
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 4,
    },
    inactiveButton: {
      backgroundColor: 'transparent',
    },
    activeText: {
      color: theme.colors.surface,
      fontWeight: '600',
      fontSize: size === 'small' ? 12 : size === 'large' ? 16 : 14,
    },
    inactiveText: {
      color: theme.colors.textSecondary,
      fontWeight: '500',
      fontSize: size === 'small' ? 12 : size === 'large' ? 16 : 14,
    },
    label: {
      fontSize: size === 'small' ? 12 : size === 'large' ? 16 : 14,
      fontWeight: '500',
      color: theme.colors.text,
    },
    demoIndicator: {
      backgroundColor: theme.colors.warning,
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: theme.spacing.xs,
      borderRadius: theme.borderRadius.sm,
      marginLeft: theme.spacing.sm,
    },
    demoText: {
      color: theme.colors.surface,
      fontSize: 10,
      fontWeight: '600',
      textTransform: 'uppercase',
    },
    liveIndicator: {
      backgroundColor: theme.colors.error,
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: theme.spacing.xs,
      borderRadius: theme.borderRadius.sm,
      marginLeft: theme.spacing.sm,
    },
    liveText: {
      color: theme.colors.surface,
      fontSize: 10,
      fontWeight: '600',
      textTransform: 'uppercase',
    },
  });

  return (
    <View style={styles.container}>
      {showLabel && (
        <Text style={styles.label}>Trading Mode:</Text>
      )}
      
      <View style={styles.toggleContainer}>
        <TouchableOpacity
          style={[
            styles.toggleButton,
            isDemoMode ? styles.activeButton : styles.inactiveButton,
          ]}
          onPress={handleToggle}
          disabled={isLoading}
        >
          <Text style={isDemoMode ? styles.activeText : styles.inactiveText}>
            Demo
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[
            styles.toggleButton,
            !isDemoMode ? styles.activeButton : styles.inactiveButton,
          ]}
          onPress={handleToggle}
          disabled={isLoading}
        >
          <Text style={!isDemoMode ? styles.activeText : styles.inactiveText}>
            Live
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Status Indicator */}
      <View style={isDemoMode ? styles.demoIndicator : styles.liveIndicator}>
        <Text style={isDemoMode ? styles.demoText : styles.liveText}>
          {isDemoMode ? 'DEMO' : 'LIVE'}
        </Text>
      </View>
    </View>
  );
};

export default DemoModeToggle;