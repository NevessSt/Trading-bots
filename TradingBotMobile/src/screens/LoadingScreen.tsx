import React, {useEffect, useRef} from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  StatusBar,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import {useTheme} from '../context/ThemeContext';

const {width, height} = Dimensions.get('window');

interface LoadingScreenProps {
  message?: string;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({message = 'Loading...'}) => {
  const {theme, isDark} = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Initial fade in animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();

    // Continuous rotation animation
    const rotateAnimation = Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 2000,
        useNativeDriver: true,
      })
    );

    // Pulse animation
    const pulseAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    );

    rotateAnimation.start();
    pulseAnimation.start();

    return () => {
      rotateAnimation.stop();
      pulseAnimation.stop();
    };
  }, [fadeAnim, scaleAnim, rotateAnim, pulseAnim]);

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const gradientColors = isDark
    ? ['#1a1a2e', '#16213e', '#0f3460']
    : ['#667eea', '#764ba2', '#f093fb'];

  return (
    <LinearGradient colors={gradientColors} style={styles.container}>
      <StatusBar
        barStyle={isDark ? 'light-content' : 'dark-content'}
        backgroundColor="transparent"
        translucent
      />
      
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{scale: scaleAnim}],
          },
        ]}
      >
        {/* Logo Container */}
        <Animated.View
          style={[
            styles.logoContainer,
            {
              transform: [{scale: pulseAnim}],
            },
          ]}
        >
          {/* Outer Ring */}
          <Animated.View
            style={[
              styles.outerRing,
              {
                borderColor: theme.colors.primary,
                transform: [{rotate: spin}],
              },
            ]}
          />
          
          {/* Inner Circle */}
          <View
            style={[
              styles.innerCircle,
              {
                backgroundColor: theme.colors.primary,
              },
            ]}
          >
            {/* Trading Bot Icon */}
            <View style={styles.iconContainer}>
              <View style={[styles.chartBar, {backgroundColor: theme.colors.onPrimary}]} />
              <View style={[styles.chartBar, styles.chartBarTall, {backgroundColor: theme.colors.onPrimary}]} />
              <View style={[styles.chartBar, {backgroundColor: theme.colors.onPrimary}]} />
              <View style={[styles.chartBar, styles.chartBarShort, {backgroundColor: theme.colors.onPrimary}]} />
            </View>
          </View>
        </Animated.View>

        {/* App Title */}
        <Text style={[styles.title, {color: theme.colors.onBackground}]}>
          TradingBot
        </Text>
        <Text style={[styles.subtitle, {color: theme.colors.onSurfaceVariant}]}>
          Mobile
        </Text>

        {/* Loading Message */}
        <Text style={[styles.message, {color: theme.colors.onSurfaceVariant}]}>
          {message}
        </Text>

        {/* Loading Dots */}
        <View style={styles.dotsContainer}>
          {[0, 1, 2].map((index) => (
            <Animated.View
              key={index}
              style={[
                styles.dot,
                {
                  backgroundColor: theme.colors.primary,
                  opacity: fadeAnim,
                },
              ]}
            />
          ))}
        </View>
      </Animated.View>

      {/* Background Pattern */}
      <View style={styles.backgroundPattern}>
        {Array.from({length: 20}).map((_, index) => (
          <View
            key={index}
            style={[
              styles.patternDot,
              {
                backgroundColor: theme.colors.primary,
                opacity: 0.1,
                left: Math.random() * width,
                top: Math.random() * height,
              },
            ]}
          />
        ))}
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    zIndex: 1,
  },
  logoContainer: {
    width: 120,
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  outerRing: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 3,
    borderStyle: 'dashed',
  },
  innerCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  iconContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'center',
    width: 32,
    height: 20,
  },
  chartBar: {
    width: 4,
    height: 12,
    marginHorizontal: 1,
    borderRadius: 2,
  },
  chartBarTall: {
    height: 20,
  },
  chartBarShort: {
    height: 8,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    fontWeight: '300',
    marginBottom: 40,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 30,
    paddingHorizontal: 40,
  },
  dotsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
  },
  backgroundPattern: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  patternDot: {
    position: 'absolute',
    width: 4,
    height: 4,
    borderRadius: 2,
  },
});

export default LoadingScreen;