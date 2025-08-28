import React, {useState, useRef, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  Animated,
  Dimensions,
  Switch,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';
import {useAuth} from '../context/AuthContext';
import {useTradingContext} from '../context/TradingContext';

const {width} = Dimensions.get('window');

interface Step {
  id: number;
  title: string;
  subtitle: string;
  icon: string;
}

const STEPS: Step[] = [
  {
    id: 1,
    title: 'Welcome',
    subtitle: 'Let\'s get you started with TradingBot',
    icon: 'waving-hand',
  },
  {
    id: 2,
    title: 'API Configuration',
    subtitle: 'Connect your trading exchange',
    icon: 'api',
  },
  {
    id: 3,
    title: 'Risk Settings',
    subtitle: 'Configure your risk management',
    icon: 'security',
  },
  {
    id: 4,
    title: 'Notifications',
    subtitle: 'Set up alerts and notifications',
    icon: 'notifications',
  },
  {
    id: 5,
    title: 'Complete',
    subtitle: 'You\'re all set to start trading!',
    icon: 'check-circle',
  },
];

const SetupWizardScreen: React.FC = () => {
  const {theme, isDark} = useTheme();
  const {completeSetup} = useAuth();
  const {updateSettings} = useTradingContext();
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  // API Configuration
  const [exchange, setExchange] = useState('binance');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [testMode, setTestMode] = useState(true);
  
  // Risk Settings
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState('2');
  const [stopLossPercentage, setStopLossPercentage] = useState('5');
  const [takeProfitPercentage, setTakeProfitPercentage] = useState('10');
  const [maxDailyLoss, setMaxDailyLoss] = useState('10');
  
  // Notification Settings
  const [pushNotifications, setPushNotifications] = useState(true);
  const [priceAlerts, setPriceAlerts] = useState(true);
  const [tradeNotifications, setTradeNotifications] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(false);
  
  const slideAnim = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animate step transition
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(progressAnim, {
        toValue: (currentStep - 1) / (STEPS.length - 1),
        duration: 300,
        useNativeDriver: false,
      }),
    ]).start();
  }, [currentStep]);

  const handleNext = async () => {
    if (currentStep < STEPS.length) {
      if (await validateCurrentStep()) {
        setCurrentStep(currentStep + 1);
        slideAnim.setValue(50);
      }
    } else {
      await handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      slideAnim.setValue(-50);
    }
  };

  const validateCurrentStep = async (): Promise<boolean> => {
    switch (currentStep) {
      case 2: // API Configuration
        if (!apiKey.trim() || !apiSecret.trim()) {
          Alert.alert('Error', 'Please enter your API credentials');
          return false;
        }
        if (apiKey.length < 10 || apiSecret.length < 10) {
          Alert.alert('Error', 'API credentials seem too short');
          return false;
        }
        break;
      case 3: // Risk Settings
        const maxRisk = parseFloat(maxRiskPerTrade);
        const stopLoss = parseFloat(stopLossPercentage);
        const takeProfit = parseFloat(takeProfitPercentage);
        const dailyLoss = parseFloat(maxDailyLoss);
        
        if (isNaN(maxRisk) || maxRisk <= 0 || maxRisk > 10) {
          Alert.alert('Error', 'Max risk per trade must be between 0.1% and 10%');
          return false;
        }
        if (isNaN(stopLoss) || stopLoss <= 0 || stopLoss > 50) {
          Alert.alert('Error', 'Stop loss must be between 0.1% and 50%');
          return false;
        }
        if (isNaN(takeProfit) || takeProfit <= 0 || takeProfit > 100) {
          Alert.alert('Error', 'Take profit must be between 0.1% and 100%');
          return false;
        }
        if (isNaN(dailyLoss) || dailyLoss <= 0 || dailyLoss > 50) {
          Alert.alert('Error', 'Max daily loss must be between 0.1% and 50%');
          return false;
        }
        break;
    }
    return true;
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      // Save settings
      await updateSettings({
        exchange,
        apiKey,
        apiSecret,
        testMode,
        maxRiskPerTrade: parseFloat(maxRiskPerTrade),
        stopLossPercentage: parseFloat(stopLossPercentage),
        takeProfitPercentage: parseFloat(takeProfitPercentage),
        maxDailyLoss: parseFloat(maxDailyLoss),
        notifications: {
          push: pushNotifications,
          priceAlerts,
          trades: tradeNotifications,
          email: emailNotifications,
        },
      });
      
      // Complete setup
      await completeSetup();
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return renderWelcomeStep();
      case 2:
        return renderAPIStep();
      case 3:
        return renderRiskStep();
      case 4:
        return renderNotificationStep();
      case 5:
        return renderCompleteStep();
      default:
        return null;
    }
  };

  const renderWelcomeStep = () => (
    <View style={styles.stepContent}>
      <Icon name="waving-hand" size={80} color={theme.colors.primary} />
      <Text style={[styles.stepTitle, {color: theme.colors.onSurface}]}>
        Welcome to TradingBot!
      </Text>
      <Text style={[styles.stepDescription, {color: theme.colors.onSurfaceVariant}]}>
        This setup wizard will help you configure your trading bot in just a few steps.
        We'll set up your exchange connection, risk management, and notifications.
      </Text>
      <View style={styles.featureList}>
        <View style={styles.featureItem}>
          <Icon name="trending-up" size={24} color={theme.colors.primary} />
          <Text style={[styles.featureText, {color: theme.colors.onSurface}]}>Automated Trading</Text>
        </View>
        <View style={styles.featureItem}>
          <Icon name="security" size={24} color={theme.colors.primary} />
          <Text style={[styles.featureText, {color: theme.colors.onSurface}]}>Risk Management</Text>
        </View>
        <View style={styles.featureItem}>
          <Icon name="notifications" size={24} color={theme.colors.primary} />
          <Text style={[styles.featureText, {color: theme.colors.onSurface}]}>Real-time Alerts</Text>
        </View>
      </View>
    </View>
  );

  const renderAPIStep = () => (
    <View style={styles.stepContent}>
      <Icon name="api" size={60} color={theme.colors.primary} />
      <Text style={[styles.stepTitle, {color: theme.colors.onSurface}]}>
        Connect Your Exchange
      </Text>
      <Text style={[styles.stepDescription, {color: theme.colors.onSurfaceVariant}]}>
        Enter your exchange API credentials to enable trading.
      </Text>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Exchange</Text>
        <View style={styles.exchangeSelector}>
          {['binance', 'coinbase', 'kraken'].map((ex) => (
            <TouchableOpacity
              key={ex}
              style={[
                styles.exchangeOption,
                {
                  backgroundColor: exchange === ex ? theme.colors.primary : theme.colors.surface,
                  borderColor: theme.colors.outline,
                },
              ]}
              onPress={() => setExchange(ex)}
            >
              <Text
                style={[
                  styles.exchangeText,
                  {
                    color: exchange === ex ? theme.colors.onPrimary : theme.colors.onSurface,
                  },
                ]}
              >
                {ex.charAt(0).toUpperCase() + ex.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>API Key</Text>
        <TextInput
          style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
          placeholder="Enter your API key"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          value={apiKey}
          onChangeText={setApiKey}
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>API Secret</Text>
        <TextInput
          style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
          placeholder="Enter your API secret"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          value={apiSecret}
          onChangeText={setApiSecret}
          secureTextEntry
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>
      
      <View style={styles.switchContainer}>
        <Text style={[styles.switchLabel, {color: theme.colors.onSurface}]}>Test Mode</Text>
        <Switch
          value={testMode}
          onValueChange={setTestMode}
          trackColor={{false: theme.colors.outline, true: theme.colors.primary}}
          thumbColor={testMode ? theme.colors.onPrimary : theme.colors.onSurface}
        />
      </View>
      
      <Text style={[styles.helpText, {color: theme.colors.onSurfaceVariant}]}>
        💡 Test mode allows you to practice without real money
      </Text>
    </View>
  );

  const renderRiskStep = () => (
    <View style={styles.stepContent}>
      <Icon name="security" size={60} color={theme.colors.primary} />
      <Text style={[styles.stepTitle, {color: theme.colors.onSurface}]}>
        Risk Management
      </Text>
      <Text style={[styles.stepDescription, {color: theme.colors.onSurfaceVariant}]}>
        Configure your risk parameters to protect your capital.
      </Text>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Max Risk Per Trade (%)</Text>
        <TextInput
          style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
          placeholder="2.0"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          value={maxRiskPerTrade}
          onChangeText={setMaxRiskPerTrade}
          keyboardType="decimal-pad"
        />
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Stop Loss (%)</Text>
        <TextInput
          style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
          placeholder="5.0"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          value={stopLossPercentage}
          onChangeText={setStopLossPercentage}
          keyboardType="decimal-pad"
        />
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Take Profit (%)</Text>
        <TextInput
          style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
          placeholder="10.0"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          value={takeProfitPercentage}
          onChangeText={setTakeProfitPercentage}
          keyboardType="decimal-pad"
        />
      </View>
      
      <View style={styles.inputGroup}>
        <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Max Daily Loss (%)</Text>
        <TextInput
          style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
          placeholder="10.0"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          value={maxDailyLoss}
          onChangeText={setMaxDailyLoss}
          keyboardType="decimal-pad"
        />
      </View>
    </View>
  );

  const renderNotificationStep = () => (
    <View style={styles.stepContent}>
      <Icon name="notifications" size={60} color={theme.colors.primary} />
      <Text style={[styles.stepTitle, {color: theme.colors.onSurface}]}>
        Notification Settings
      </Text>
      <Text style={[styles.stepDescription, {color: theme.colors.onSurfaceVariant}]}>
        Choose how you want to be notified about trading activities.
      </Text>
      
      <View style={styles.switchContainer}>
        <Text style={[styles.switchLabel, {color: theme.colors.onSurface}]}>Push Notifications</Text>
        <Switch
          value={pushNotifications}
          onValueChange={setPushNotifications}
          trackColor={{false: theme.colors.outline, true: theme.colors.primary}}
          thumbColor={pushNotifications ? theme.colors.onPrimary : theme.colors.onSurface}
        />
      </View>
      
      <View style={styles.switchContainer}>
        <Text style={[styles.switchLabel, {color: theme.colors.onSurface}]}>Price Alerts</Text>
        <Switch
          value={priceAlerts}
          onValueChange={setPriceAlerts}
          trackColor={{false: theme.colors.outline, true: theme.colors.primary}}
          thumbColor={priceAlerts ? theme.colors.onPrimary : theme.colors.onSurface}
        />
      </View>
      
      <View style={styles.switchContainer}>
        <Text style={[styles.switchLabel, {color: theme.colors.onSurface}]}>Trade Notifications</Text>
        <Switch
          value={tradeNotifications}
          onValueChange={setTradeNotifications}
          trackColor={{false: theme.colors.outline, true: theme.colors.primary}}
          thumbColor={tradeNotifications ? theme.colors.onPrimary : theme.colors.onSurface}
        />
      </View>
      
      <View style={styles.switchContainer}>
        <Text style={[styles.switchLabel, {color: theme.colors.onSurface}]}>Email Notifications</Text>
        <Switch
          value={emailNotifications}
          onValueChange={setEmailNotifications}
          trackColor={{false: theme.colors.outline, true: theme.colors.primary}}
          thumbColor={emailNotifications ? theme.colors.onPrimary : theme.colors.onSurface}
        />
      </View>
    </View>
  );

  const renderCompleteStep = () => (
    <View style={styles.stepContent}>
      <Icon name="check-circle" size={80} color={theme.colors.primary} />
      <Text style={[styles.stepTitle, {color: theme.colors.onSurface}]}>
        Setup Complete!
      </Text>
      <Text style={[styles.stepDescription, {color: theme.colors.onSurfaceVariant}]}>
        Your TradingBot is now configured and ready to use. You can always change these settings later in the app.
      </Text>
      
      <View style={styles.summaryContainer}>
        <View style={styles.summaryItem}>
          <Icon name="api" size={20} color={theme.colors.primary} />
          <Text style={[styles.summaryText, {color: theme.colors.onSurface}]}>
            Exchange: {exchange.charAt(0).toUpperCase() + exchange.slice(1)}
          </Text>
        </View>
        <View style={styles.summaryItem}>
          <Icon name="security" size={20} color={theme.colors.primary} />
          <Text style={[styles.summaryText, {color: theme.colors.onSurface}]}>
            Max Risk: {maxRiskPerTrade}% per trade
          </Text>
        </View>
        <View style={styles.summaryItem}>
          <Icon name="notifications" size={20} color={theme.colors.primary} />
          <Text style={[styles.summaryText, {color: theme.colors.onSurface}]}>
            Notifications: {pushNotifications ? 'Enabled' : 'Disabled'}
          </Text>
        </View>
      </View>
    </View>
  );

  const gradientColors = isDark
    ? ['#1a1a2e', '#16213e']
    : ['#f8f9fa', '#e9ecef'];

  return (
    <LinearGradient colors={gradientColors} style={styles.container}>
      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={[styles.progressTrack, {backgroundColor: theme.colors.outline}]}>
          <Animated.View
            style={[
              styles.progressBar,
              {
                backgroundColor: theme.colors.primary,
                width: progressAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
              },
            ]}
          />
        </View>
        <Text style={[styles.progressText, {color: theme.colors.onSurfaceVariant}]}>
          Step {currentStep} of {STEPS.length}
        </Text>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View
          style={[
            styles.contentContainer,
            {
              transform: [{translateX: slideAnim}],
            },
          ]}
        >
          {renderStepContent()}
        </Animated.View>
      </ScrollView>

      {/* Navigation */}
      <View style={styles.navigationContainer}>
        {currentStep > 1 && (
          <TouchableOpacity
            style={[styles.navButton, styles.prevButton, {borderColor: theme.colors.outline}]}
            onPress={handlePrevious}
          >
            <Icon name="arrow-back" size={20} color={theme.colors.onSurface} />
            <Text style={[styles.navButtonText, {color: theme.colors.onSurface}]}>Previous</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={[
            styles.navButton,
            styles.nextButton,
            {backgroundColor: theme.colors.primary},
            currentStep === 1 && styles.fullWidthButton,
          ]}
          onPress={handleNext}
          disabled={isLoading}
        >
          {isLoading ? (
            <Icon name="hourglass-empty" size={20} color={theme.colors.onPrimary} />
          ) : (
            <>
              <Text style={[styles.navButtonText, {color: theme.colors.onPrimary}]}>
                {currentStep === STEPS.length ? 'Get Started' : 'Next'}
              </Text>
              {currentStep < STEPS.length && (
                <Icon name="arrow-forward" size={20} color={theme.colors.onPrimary} />
              )}
            </>
          )}
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  progressContainer: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  progressTrack: {
    height: 4,
    borderRadius: 2,
    marginBottom: 8,
  },
  progressBar: {
    height: '100%',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    textAlign: 'center',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
  },
  contentContainer: {
    flex: 1,
  },
  stepContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 12,
  },
  stepDescription: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  featureList: {
    width: '100%',
    maxWidth: 300,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  featureText: {
    fontSize: 16,
    marginLeft: 12,
  },
  inputGroup: {
    width: '100%',
    maxWidth: 300,
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  exchangeSelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  exchangeOption: {
    flex: 1,
    height: 48,
    borderWidth: 1,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 4,
  },
  exchangeText: {
    fontSize: 14,
    fontWeight: '500',
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    maxWidth: 300,
    marginBottom: 16,
    paddingVertical: 8,
  },
  switchLabel: {
    fontSize: 16,
    flex: 1,
  },
  helpText: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 16,
    fontStyle: 'italic',
  },
  summaryContainer: {
    width: '100%',
    maxWidth: 300,
    marginTop: 20,
  },
  summaryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 14,
    marginLeft: 8,
  },
  navigationContainer: {
    flexDirection: 'row',
    padding: 20,
    paddingBottom: 40,
  },
  navButton: {
    flex: 1,
    height: 48,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
  },
  prevButton: {
    borderWidth: 1,
  },
  nextButton: {
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  fullWidthButton: {
    marginHorizontal: 0,
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '600',
    marginHorizontal: 8,
  },
});

export default SetupWizardScreen;