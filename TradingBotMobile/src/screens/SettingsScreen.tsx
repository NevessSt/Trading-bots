import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  Modal,
  TextInput,
  Linking,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useTheme} from '../context/ThemeContext';
import {useAuth} from '../context/AuthContext';
import {useTradingContext} from '../context/TradingContext';

interface SettingItem {
  id: string;
  title: string;
  subtitle?: string;
  type: 'toggle' | 'navigation' | 'action' | 'info';
  value?: boolean;
  onPress?: () => void;
  onToggle?: (value: boolean) => void;
  icon: string;
  iconColor?: string;
}

interface SettingSection {
  title: string;
  items: SettingItem[];
}

const SettingsScreen: React.FC = () => {
  const {theme, isDark, toggleTheme} = useTheme();
  const {user, logout, updateUser} = useAuth();
  const {settings, updateSettings} = useTradingContext();
  
  const [showApiModal, setShowApiModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showRiskModal, setShowRiskModal] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [displayName, setDisplayName] = useState(user?.displayName || '');
  const [email, setEmail] = useState(user?.email || '');
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState(settings?.maxRiskPerTrade?.toString() || '2');
  const [maxDailyLoss, setMaxDailyLoss] = useState(settings?.maxDailyLoss?.toString() || '10');
  const [stopLossPercentage, setStopLossPercentage] = useState(settings?.stopLossPercentage?.toString() || '5');

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: logout,
        },
      ]
    );
  };

  const handleSaveApiKeys = async () => {
    if (!apiKey.trim() || !apiSecret.trim()) {
      Alert.alert('Error', 'Please enter both API key and secret');
      return;
    }

    try {
      await updateSettings({
        ...settings,
        apiKey: apiKey.trim(),
        apiSecret: apiSecret.trim(),
      });
      setShowApiModal(false);
      setApiKey('');
      setApiSecret('');
      Alert.alert('Success', 'API keys updated successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to update API keys');
    }
  };

  const handleSaveProfile = async () => {
    if (!displayName.trim() || !email.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    try {
      await updateUser({
        displayName: displayName.trim(),
        email: email.trim(),
      });
      setShowProfileModal(false);
      Alert.alert('Success', 'Profile updated successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to update profile');
    }
  };

  const handleSaveRiskSettings = async () => {
    const maxRisk = parseFloat(maxRiskPerTrade);
    const maxDaily = parseFloat(maxDailyLoss);
    const stopLoss = parseFloat(stopLossPercentage);

    if (isNaN(maxRisk) || isNaN(maxDaily) || isNaN(stopLoss)) {
      Alert.alert('Error', 'Please enter valid numbers');
      return;
    }

    if (maxRisk <= 0 || maxRisk > 100 || maxDaily <= 0 || maxDaily > 100 || stopLoss <= 0 || stopLoss > 100) {
      Alert.alert('Error', 'Percentages must be between 0 and 100');
      return;
    }

    try {
      await updateSettings({
        ...settings,
        maxRiskPerTrade: maxRisk,
        maxDailyLoss: maxDaily,
        stopLossPercentage: stopLoss,
      });
      setShowRiskModal(false);
      Alert.alert('Success', 'Risk settings updated successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to update risk settings');
    }
  };

  const openUrl = (url: string) => {
    Linking.openURL(url).catch(() => {
      Alert.alert('Error', 'Unable to open link');
    });
  };

  const settingSections: SettingSection[] = [
    {
      title: 'Account',
      items: [
        {
          id: 'profile',
          title: 'Profile',
          subtitle: user?.displayName || 'Update your profile information',
          type: 'navigation',
          icon: 'person',
          onPress: () => setShowProfileModal(true),
        },
        {
          id: 'api_keys',
          title: 'API Keys',
          subtitle: 'Configure exchange API credentials',
          type: 'navigation',
          icon: 'vpn-key',
          onPress: () => setShowApiModal(true),
        },
        {
          id: 'biometric',
          title: 'Biometric Authentication',
          subtitle: 'Use fingerprint or face ID',
          type: 'toggle',
          value: settings?.biometricEnabled || false,
          icon: 'fingerprint',
          onToggle: (value) => updateSettings({...settings, biometricEnabled: value}),
        },
      ],
    },
    {
      title: 'Trading',
      items: [
        {
          id: 'risk_management',
          title: 'Risk Management',
          subtitle: 'Configure trading risk parameters',
          type: 'navigation',
          icon: 'security',
          onPress: () => setShowRiskModal(true),
        },
        {
          id: 'auto_trading',
          title: 'Auto Trading',
          subtitle: 'Enable automated trading',
          type: 'toggle',
          value: settings?.autoTradingEnabled || false,
          icon: 'smart-toy',
          onToggle: (value) => updateSettings({...settings, autoTradingEnabled: value}),
        },
        {
          id: 'paper_trading',
          title: 'Paper Trading Mode',
          subtitle: 'Practice with virtual money',
          type: 'toggle',
          value: settings?.paperTradingMode || false,
          icon: 'assignment',
          onToggle: (value) => updateSettings({...settings, paperTradingMode: value}),
        },
      ],
    },
    {
      title: 'Notifications',
      items: [
        {
          id: 'push_notifications',
          title: 'Push Notifications',
          subtitle: 'Receive trading alerts',
          type: 'toggle',
          value: settings?.pushNotificationsEnabled || false,
          icon: 'notifications',
          onToggle: (value) => updateSettings({...settings, pushNotificationsEnabled: value}),
        },
        {
          id: 'price_alerts',
          title: 'Price Alerts',
          subtitle: 'Get notified of price changes',
          type: 'toggle',
          value: settings?.priceAlertsEnabled || false,
          icon: 'trending-up',
          onToggle: (value) => updateSettings({...settings, priceAlertsEnabled: value}),
        },
        {
          id: 'trade_confirmations',
          title: 'Trade Confirmations',
          subtitle: 'Confirm before executing trades',
          type: 'toggle',
          value: settings?.tradeConfirmationsEnabled || true,
          icon: 'check-circle',
          onToggle: (value) => updateSettings({...settings, tradeConfirmationsEnabled: value}),
        },
      ],
    },
    {
      title: 'Appearance',
      items: [
        {
          id: 'dark_mode',
          title: 'Dark Mode',
          subtitle: 'Use dark theme',
          type: 'toggle',
          value: isDark,
          icon: 'dark-mode',
          onToggle: toggleTheme,
        },
      ],
    },
    {
      title: 'Support',
      items: [
        {
          id: 'help',
          title: 'Help & FAQ',
          subtitle: 'Get help and find answers',
          type: 'navigation',
          icon: 'help',
          onPress: () => openUrl('https://tradingbot.help'),
        },
        {
          id: 'contact',
          title: 'Contact Support',
          subtitle: 'Get in touch with our team',
          type: 'navigation',
          icon: 'support-agent',
          onPress: () => openUrl('mailto:support@tradingbot.com'),
        },
        {
          id: 'privacy',
          title: 'Privacy Policy',
          type: 'navigation',
          icon: 'privacy-tip',
          onPress: () => openUrl('https://tradingbot.com/privacy'),
        },
        {
          id: 'terms',
          title: 'Terms of Service',
          type: 'navigation',
          icon: 'description',
          onPress: () => openUrl('https://tradingbot.com/terms'),
        },
      ],
    },
    {
      title: 'Account Actions',
      items: [
        {
          id: 'logout',
          title: 'Logout',
          type: 'action',
          icon: 'logout',
          iconColor: '#f44336',
          onPress: handleLogout,
        },
      ],
    },
  ];

  const renderSettingItem = (item: SettingItem) => {
    return (
      <TouchableOpacity
        key={item.id}
        style={[
          styles.settingItem,
          {
            backgroundColor: theme.colors.surface,
            borderBottomColor: theme.colors.outline,
          },
        ]}
        onPress={item.onPress}
        disabled={item.type === 'toggle'}
      >
        <View style={styles.settingItemLeft}>
          <View
            style={[
              styles.settingIcon,
              {
                backgroundColor: item.iconColor
                  ? `${item.iconColor}20`
                  : `${theme.colors.primary}20`,
              },
            ]}
          >
            <Icon
              name={item.icon}
              size={20}
              color={item.iconColor || theme.colors.primary}
            />
          </View>
          <View style={styles.settingTextContainer}>
            <Text style={[styles.settingTitle, {color: theme.colors.onSurface}]}>
              {item.title}
            </Text>
            {item.subtitle && (
              <Text style={[styles.settingSubtitle, {color: theme.colors.onSurfaceVariant}]}>
                {item.subtitle}
              </Text>
            )}
          </View>
        </View>
        
        <View style={styles.settingItemRight}>
          {item.type === 'toggle' && (
            <Switch
              value={item.value}
              onValueChange={item.onToggle}
              trackColor={{
                false: theme.colors.outline,
                true: theme.colors.primary,
              }}
              thumbColor={theme.colors.surface}
            />
          )}
          {(item.type === 'navigation' || item.type === 'action') && (
            <Icon
              name="chevron-right"
              size={20}
              color={theme.colors.onSurfaceVariant}
            />
          )}
        </View>
      </TouchableOpacity>
    );
  };

  const renderSection = (section: SettingSection) => {
    return (
      <View key={section.title} style={styles.section}>
        <Text style={[styles.sectionTitle, {color: theme.colors.onSurfaceVariant}]}>
          {section.title}
        </Text>
        <View style={[styles.sectionContent, {backgroundColor: theme.colors.surface}]}>
          {section.items.map(renderSettingItem)}
        </View>
      </View>
    );
  };

  const renderApiModal = () => (
    <Modal
      visible={showApiModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowApiModal(false)}
    >
      <View style={[styles.modalContainer, {backgroundColor: theme.colors.background}]}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowApiModal(false)}>
            <Icon name="close" size={24} color={theme.colors.onSurface} />
          </TouchableOpacity>
          <Text style={[styles.modalTitle, {color: theme.colors.onSurface}]}>
            API Keys
          </Text>
          <TouchableOpacity onPress={handleSaveApiKeys}>
            <Text style={[styles.saveButton, {color: theme.colors.primary}]}>Save</Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>API Key</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="Enter your API key"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={apiKey}
              onChangeText={setApiKey}
              secureTextEntry
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
            />
          </View>
          
          <View style={[styles.warningBox, {backgroundColor: `${theme.colors.error}20`}]}>
            <Icon name="warning" size={20} color={theme.colors.error} />
            <Text style={[styles.warningText, {color: theme.colors.error}]}>
              Keep your API keys secure. Never share them with anyone.
            </Text>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderProfileModal = () => (
    <Modal
      visible={showProfileModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowProfileModal(false)}
    >
      <View style={[styles.modalContainer, {backgroundColor: theme.colors.background}]}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowProfileModal(false)}>
            <Icon name="close" size={24} color={theme.colors.onSurface} />
          </TouchableOpacity>
          <Text style={[styles.modalTitle, {color: theme.colors.onSurface}]}>
            Profile
          </Text>
          <TouchableOpacity onPress={handleSaveProfile}>
            <Text style={[styles.saveButton, {color: theme.colors.primary}]}>Save</Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Display Name</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="Enter your display name"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={displayName}
              onChangeText={setDisplayName}
            />
          </View>
          
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Email</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="Enter your email"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderRiskModal = () => (
    <Modal
      visible={showRiskModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowRiskModal(false)}
    >
      <View style={[styles.modalContainer, {backgroundColor: theme.colors.background}]}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowRiskModal(false)}>
            <Icon name="close" size={24} color={theme.colors.onSurface} />
          </TouchableOpacity>
          <Text style={[styles.modalTitle, {color: theme.colors.onSurface}]}>
            Risk Management
          </Text>
          <TouchableOpacity onPress={handleSaveRiskSettings}>
            <Text style={[styles.saveButton, {color: theme.colors.primary}]}>Save</Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
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
          
          <View style={styles.inputGroup}>
            <Text style={[styles.inputLabel, {color: theme.colors.onSurface}]}>Default Stop Loss (%)</Text>
            <TextInput
              style={[styles.input, {color: theme.colors.onSurface, borderColor: theme.colors.outline}]}
              placeholder="5.0"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              value={stopLossPercentage}
              onChangeText={setStopLossPercentage}
              keyboardType="decimal-pad"
            />
          </View>
          
          <View style={[styles.infoBox, {backgroundColor: `${theme.colors.primary}20`}]}>
            <Icon name="info" size={20} color={theme.colors.primary} />
            <Text style={[styles.infoText, {color: theme.colors.primary}]}>
              These settings help protect your capital by limiting potential losses.
            </Text>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  return (
    <View style={[styles.container, {backgroundColor: theme.colors.background}]}>
      <View style={styles.header}>
        <Text style={[styles.headerTitle, {color: theme.colors.onSurface}]}>
          Settings
        </Text>
      </View>
      
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {settingSections.map(renderSection)}
      </ScrollView>
      
      {renderApiModal()}
      {renderProfileModal()}
      {renderRiskModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
    marginHorizontal: 20,
  },
  sectionContent: {
    marginHorizontal: 20,
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 0.5,
  },
  settingItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  settingTextContainer: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 14,
  },
  settingItemRight: {
    marginLeft: 12,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  saveButton: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: 20,
  },
  inputGroup: {
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
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  warningText: {
    fontSize: 14,
    marginLeft: 8,
    flex: 1,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  infoText: {
    fontSize: 14,
    marginLeft: 8,
    flex: 1,
  },
});

export default SettingsScreen;