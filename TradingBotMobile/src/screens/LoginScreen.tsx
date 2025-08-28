import React, {useState, useRef, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Animated,
  Dimensions,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';
import {useAuth} from '../context/AuthContext';

const {width, height} = Dimensions.get('window');

const LoginScreen: React.FC = () => {
  const {theme, isDark} = useTheme();
  const {login, register, authenticateWithBiometrics} = useAuth();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    // Animate screen entrance
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();

    // Check if biometric authentication is available
    checkBiometricAvailability();
  }, []);

  const checkBiometricAvailability = async () => {
    // In a real app, you would check if biometric auth is available
    // For demo purposes, we'll assume it's available
    setBiometricAvailable(true);
  };

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (!isValidEmail(email)) {
      Alert.alert('Error', 'Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    try {
      const success = await login(email, password, rememberMe);
      if (!success) {
        Alert.alert('Login Failed', 'Invalid email or password');
      }
    } catch (error) {
      Alert.alert('Error', 'An error occurred during login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!email || !password || !confirmPassword || !name) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (!isValidEmail(email)) {
      Alert.alert('Error', 'Please enter a valid email address');
      return;
    }

    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters long');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    setIsLoading(true);
    try {
      const success = await register(email, password, name);
      if (!success) {
        Alert.alert('Registration Failed', 'Please try again');
      }
    } catch (error) {
      Alert.alert('Error', 'An error occurred during registration');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    setIsLoading(true);
    try {
      const success = await authenticateWithBiometrics();
      if (!success) {
        Alert.alert('Authentication Failed', 'Biometric authentication failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Biometric authentication is not available');
    } finally {
      setIsLoading(false);
    }
  };

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setName('');
  };

  const gradientColors = isDark
    ? ['#1a1a2e', '#16213e', '#0f3460']
    : ['#667eea', '#764ba2', '#f093fb'];

  return (
    <LinearGradient colors={gradientColors} style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View
            style={[
              styles.content,
              {
                opacity: fadeAnim,
                transform: [{translateY: slideAnim}],
              },
            ]}
          >
            {/* Logo */}
            <View style={styles.logoContainer}>
              <View style={[styles.logo, {backgroundColor: theme.colors.primary}]}>
                <Icon name="trending-up" size={40} color={theme.colors.onPrimary} />
              </View>
              <Text style={[styles.logoText, {color: theme.colors.onBackground}]}>
                TradingBot Mobile
              </Text>
            </View>

            {/* Form Container */}
            <View style={[styles.formContainer, {backgroundColor: theme.colors.surface}]}>
              <Text style={[styles.formTitle, {color: theme.colors.onSurface}]}>
                {isLogin ? 'Welcome Back' : 'Create Account'}
              </Text>
              <Text style={[styles.formSubtitle, {color: theme.colors.onSurfaceVariant}]}>
                {isLogin ? 'Sign in to continue' : 'Join us to start trading'}
              </Text>

              {/* Name Input (Register only) */}
              {!isLogin && (
                <View style={styles.inputContainer}>
                  <Icon name="person" size={20} color={theme.colors.onSurfaceVariant} style={styles.inputIcon} />
                  <TextInput
                    style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
                    placeholder="Full Name"
                    placeholderTextColor={theme.colors.onSurfaceVariant}
                    value={name}
                    onChangeText={setName}
                    autoCapitalize="words"
                  />
                </View>
              )}

              {/* Email Input */}
              <View style={styles.inputContainer}>
                <Icon name="email" size={20} color={theme.colors.onSurfaceVariant} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
                  placeholder="Email Address"
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              {/* Password Input */}
              <View style={styles.inputContainer}>
                <Icon name="lock" size={20} color={theme.colors.onSurfaceVariant} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
                  placeholder="Password"
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                />
                <TouchableOpacity
                  onPress={() => setShowPassword(!showPassword)}
                  style={styles.eyeIcon}
                >
                  <Icon
                    name={showPassword ? 'visibility' : 'visibility-off'}
                    size={20}
                    color={theme.colors.onSurfaceVariant}
                  />
                </TouchableOpacity>
              </View>

              {/* Confirm Password Input (Register only) */}
              {!isLogin && (
                <View style={styles.inputContainer}>
                  <Icon name="lock" size={20} color={theme.colors.onSurfaceVariant} style={styles.inputIcon} />
                  <TextInput
                    style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
                    placeholder="Confirm Password"
                    placeholderTextColor={theme.colors.onSurfaceVariant}
                    value={confirmPassword}
                    onChangeText={setConfirmPassword}
                    secureTextEntry={!showPassword}
                    autoCapitalize="none"
                  />
                </View>
              )}

              {/* Remember Me (Login only) */}
              {isLogin && (
                <TouchableOpacity
                  style={styles.rememberContainer}
                  onPress={() => setRememberMe(!rememberMe)}
                >
                  <Icon
                    name={rememberMe ? 'check-box' : 'check-box-outline-blank'}
                    size={20}
                    color={theme.colors.primary}
                  />
                  <Text style={[styles.rememberText, {color: theme.colors.onSurfaceVariant}]}>
                    Remember me
                  </Text>
                </TouchableOpacity>
              )}

              {/* Submit Button */}
              <TouchableOpacity
                style={[styles.submitButton, {backgroundColor: theme.colors.primary}]}
                onPress={isLogin ? handleLogin : handleRegister}
                disabled={isLoading}
              >
                {isLoading ? (
                  <Icon name="hourglass-empty" size={20} color={theme.colors.onPrimary} />
                ) : (
                  <Text style={[styles.submitButtonText, {color: theme.colors.onPrimary}]}>
                    {isLogin ? 'Sign In' : 'Create Account'}
                  </Text>
                )}
              </TouchableOpacity>

              {/* Biometric Login (Login only) */}
              {isLogin && biometricAvailable && (
                <TouchableOpacity
                  style={[styles.biometricButton, {borderColor: theme.colors.outline}]}
                  onPress={handleBiometricLogin}
                  disabled={isLoading}
                >
                  <Icon name="fingerprint" size={24} color={theme.colors.primary} />
                  <Text style={[styles.biometricText, {color: theme.colors.primary}]}>
                    Use Biometric Authentication
                  </Text>
                </TouchableOpacity>
              )}

              {/* Toggle Mode */}
              <View style={styles.toggleContainer}>
                <Text style={[styles.toggleText, {color: theme.colors.onSurfaceVariant}]}>
                  {isLogin ? "Don't have an account?" : 'Already have an account?'}
                </Text>
                <TouchableOpacity onPress={toggleMode}>
                  <Text style={[styles.toggleLink, {color: theme.colors.primary}]}>
                    {isLogin ? ' Sign Up' : ' Sign In'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  content: {
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  logoText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  formContainer: {
    width: '100%',
    maxWidth: 400,
    padding: 24,
    borderRadius: 16,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  formTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  formSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    position: 'relative',
  },
  inputIcon: {
    position: 'absolute',
    left: 12,
    zIndex: 1,
  },
  input: {
    flex: 1,
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    paddingLeft: 44,
    paddingRight: 44,
    fontSize: 16,
  },
  eyeIcon: {
    position: 'absolute',
    right: 12,
    padding: 4,
  },
  rememberContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  rememberText: {
    marginLeft: 8,
    fontSize: 14,
  },
  submitButton: {
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  biometricButton: {
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  biometricText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  toggleContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  toggleText: {
    fontSize: 14,
  },
  toggleLink: {
    fontSize: 14,
    fontWeight: '600',
  },
});

export default LoginScreen;