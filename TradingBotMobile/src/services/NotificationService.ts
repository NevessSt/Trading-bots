import PushNotification, {Importance} from 'react-native-push-notification';
import {Platform, Alert, PermissionsAndroid} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';

interface NotificationData {
  id?: string;
  title: string;
  message: string;
  data?: any;
  soundName?: string;
  vibrate?: boolean;
  priority?: 'default' | 'high' | 'low';
  category?: 'trade' | 'price_alert' | 'portfolio' | 'system';
}

interface PriceAlert {
  id: string;
  symbol: string;
  condition: 'above' | 'below';
  targetPrice: number;
  currentPrice: number;
  isActive: boolean;
  createdAt: string;
}

class NotificationService {
  private static instance: NotificationService;
  private isInitialized = false;
  private deviceToken: string | null = null;
  private priceAlerts: PriceAlert[] = [];

  private constructor() {}

  public static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Request permissions
      await this.requestPermissions();

      // Configure push notifications
      this.configurePushNotifications();

      // Load saved price alerts
      await this.loadPriceAlerts();

      // Get device token
      this.deviceToken = await DeviceInfo.getUniqueId();

      this.isInitialized = true;
      console.log('NotificationService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize NotificationService:', error);
      throw error;
    }
  }

  private async requestPermissions(): Promise<boolean> {
    try {
      if (Platform.OS === 'android') {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
          {
            title: 'Notification Permission',
            message: 'TradingBot needs notification permission to send you trading alerts and updates.',
            buttonNeutral: 'Ask Me Later',
            buttonNegative: 'Cancel',
            buttonPositive: 'OK',
          },
        );
        return granted === PermissionsAndroid.RESULTS.GRANTED;
      }

      // For iOS, permissions are handled by the push notification library
      return true;
    } catch (error) {
      console.error('Failed to request notification permissions:', error);
      return false;
    }
  }

  private configurePushNotifications(): void {
    // Configure the library
    PushNotification.configure({
      // Called when Token is generated (iOS and Android)
      onRegister: (token) => {
        console.log('Push notification token:', token);
        this.deviceToken = token.token;
      },

      // Called when a remote is received or opened, or local notification is opened
      onNotification: (notification) => {
        console.log('Notification received:', notification);
        
        // Handle notification tap
        if (notification.userInteraction) {
          this.handleNotificationTap(notification);
        }

        // Required on iOS only
        notification.finish && notification.finish();
      },

      // Called when Registered Action is pressed and invokeApp is false, if true onNotification will be called
      onAction: (notification) => {
        console.log('Notification action:', notification.action);
      },

      // Called when the user fails to register for remote notifications
      onRegistrationError: (err) => {
        console.error('Push notification registration error:', err.message);
      },

      // IOS ONLY: Called when a remote notification is received while app is in foreground
      onRemoteNotification: (notification) => {
        console.log('Remote notification received:', notification);
      },

      // Android only: GCM or FCM Sender ID
      senderID: 'YOUR_SENDER_ID', // Replace with your actual sender ID

      // Android only: Request permissions on init
      requestPermissions: Platform.OS === 'ios',
    });

    // Create notification channels for Android
    if (Platform.OS === 'android') {
      this.createNotificationChannels();
    }
  }

  private createNotificationChannels(): void {
    const channels = [
      {
        channelId: 'trade_notifications',
        channelName: 'Trade Notifications',
        channelDescription: 'Notifications for trade executions and updates',
        importance: Importance.HIGH,
        vibrate: true,
      },
      {
        channelId: 'price_alerts',
        channelName: 'Price Alerts',
        channelDescription: 'Price alerts for your watchlist',
        importance: Importance.HIGH,
        vibrate: true,
      },
      {
        channelId: 'portfolio_updates',
        channelName: 'Portfolio Updates',
        channelDescription: 'Updates about your portfolio performance',
        importance: Importance.DEFAULT,
        vibrate: false,
      },
      {
        channelId: 'system_notifications',
        channelName: 'System Notifications',
        channelDescription: 'System updates and maintenance notifications',
        importance: Importance.LOW,
        vibrate: false,
      },
    ];

    channels.forEach(channel => {
      PushNotification.createChannel(
        {
          channelId: channel.channelId,
          channelName: channel.channelName,
          channelDescription: channel.channelDescription,
          importance: channel.importance,
          vibrate: channel.vibrate,
        },
        (created) => console.log(`Channel ${channel.channelId} created: ${created}`)
      );
    });
  }

  private handleNotificationTap(notification: any): void {
    // Handle different notification types
    const { category, data } = notification;
    
    switch (category) {
      case 'trade':
        // Navigate to trading screen
        console.log('Navigate to trading screen');
        break;
      case 'price_alert':
        // Navigate to asset detail
        console.log('Navigate to asset detail:', data?.symbol);
        break;
      case 'portfolio':
        // Navigate to portfolio screen
        console.log('Navigate to portfolio screen');
        break;
      default:
        console.log('Handle default notification tap');
    }
  }

  public async showLocalNotification(notificationData: NotificationData): Promise<void> {
    try {
      const channelId = this.getChannelId(notificationData.category);
      
      PushNotification.localNotification({
        id: notificationData.id || Date.now().toString(),
        title: notificationData.title,
        message: notificationData.message,
        channelId,
        priority: notificationData.priority || 'default',
        vibrate: notificationData.vibrate !== false,
        playSound: true,
        soundName: notificationData.soundName || 'default',
        userInfo: {
          category: notificationData.category,
          data: notificationData.data,
        },
      });
    } catch (error) {
      console.error('Failed to show local notification:', error);
    }
  }

  private getChannelId(category?: string): string {
    switch (category) {
      case 'trade':
        return 'trade_notifications';
      case 'price_alert':
        return 'price_alerts';
      case 'portfolio':
        return 'portfolio_updates';
      case 'system':
        return 'system_notifications';
      default:
        return 'trade_notifications';
    }
  }

  public async scheduleNotification(notificationData: NotificationData, date: Date): Promise<void> {
    try {
      const channelId = this.getChannelId(notificationData.category);
      
      PushNotification.localNotificationSchedule({
        id: notificationData.id || Date.now().toString(),
        title: notificationData.title,
        message: notificationData.message,
        date,
        channelId,
        priority: notificationData.priority || 'default',
        vibrate: notificationData.vibrate !== false,
        playSound: true,
        soundName: notificationData.soundName || 'default',
        userInfo: {
          category: notificationData.category,
          data: notificationData.data,
        },
      });
    } catch (error) {
      console.error('Failed to schedule notification:', error);
    }
  }

  public cancelNotification(id: string): void {
    PushNotification.cancelLocalNotification(id);
  }

  public cancelAllNotifications(): void {
    PushNotification.cancelAllLocalNotifications();
  }

  // Price Alert Methods
  public async addPriceAlert(symbol: string, condition: 'above' | 'below', targetPrice: number, currentPrice: number): Promise<string> {
    try {
      const alert: PriceAlert = {
        id: Date.now().toString(),
        symbol,
        condition,
        targetPrice,
        currentPrice,
        isActive: true,
        createdAt: new Date().toISOString(),
      };

      this.priceAlerts.push(alert);
      await this.savePriceAlerts();

      // Show confirmation
      await this.showLocalNotification({
        title: 'Price Alert Created',
        message: `Alert set for ${symbol} ${condition} $${targetPrice.toFixed(2)}`,
        category: 'system',
      });

      return alert.id;
    } catch (error) {
      console.error('Failed to add price alert:', error);
      throw error;
    }
  }

  public async removePriceAlert(alertId: string): Promise<void> {
    try {
      this.priceAlerts = this.priceAlerts.filter(alert => alert.id !== alertId);
      await this.savePriceAlerts();
    } catch (error) {
      console.error('Failed to remove price alert:', error);
    }
  }

  public async checkPriceAlerts(currentPrices: { [symbol: string]: number }): Promise<void> {
    try {
      const triggeredAlerts: PriceAlert[] = [];

      for (const alert of this.priceAlerts) {
        if (!alert.isActive) continue;

        const currentPrice = currentPrices[alert.symbol];
        if (!currentPrice) continue;

        const isTriggered = 
          (alert.condition === 'above' && currentPrice >= alert.targetPrice) ||
          (alert.condition === 'below' && currentPrice <= alert.targetPrice);

        if (isTriggered) {
          triggeredAlerts.push(alert);
          
          // Send notification
          await this.showLocalNotification({
            title: `Price Alert: ${alert.symbol}`,
            message: `${alert.symbol} is now ${alert.condition} $${alert.targetPrice.toFixed(2)} (Current: $${currentPrice.toFixed(2)})`,
            category: 'price_alert',
            priority: 'high',
            data: { symbol: alert.symbol, price: currentPrice },
          });

          // Deactivate the alert
          alert.isActive = false;
        }
      }

      if (triggeredAlerts.length > 0) {
        await this.savePriceAlerts();
      }
    } catch (error) {
      console.error('Failed to check price alerts:', error);
    }
  }

  public getPriceAlerts(): PriceAlert[] {
    return this.priceAlerts.filter(alert => alert.isActive);
  }

  private async loadPriceAlerts(): Promise<void> {
    try {
      const alertsData = await AsyncStorage.getItem('price_alerts');
      if (alertsData) {
        this.priceAlerts = JSON.parse(alertsData);
      }
    } catch (error) {
      console.error('Failed to load price alerts:', error);
    }
  }

  private async savePriceAlerts(): Promise<void> {
    try {
      await AsyncStorage.setItem('price_alerts', JSON.stringify(this.priceAlerts));
    } catch (error) {
      console.error('Failed to save price alerts:', error);
    }
  }

  // Trading Notifications
  public async notifyTradeExecuted(symbol: string, side: 'buy' | 'sell', quantity: number, price: number): Promise<void> {
    await this.showLocalNotification({
      title: 'Trade Executed',
      message: `${side.toUpperCase()} ${quantity} ${symbol} at $${price.toFixed(2)}`,
      category: 'trade',
      priority: 'high',
      data: { symbol, side, quantity, price },
    });
  }

  public async notifyPortfolioUpdate(totalValue: number, change: number, changePercent: number): Promise<void> {
    const isPositive = change >= 0;
    const changeText = isPositive ? '+' : '';
    
    await this.showLocalNotification({
      title: 'Portfolio Update',
      message: `Total: $${totalValue.toFixed(2)} (${changeText}${changePercent.toFixed(2)}%)`,
      category: 'portfolio',
      priority: 'default',
      data: { totalValue, change, changePercent },
    });
  }

  public async notifySystemMessage(title: string, message: string): Promise<void> {
    await this.showLocalNotification({
      title,
      message,
      category: 'system',
      priority: 'default',
    });
  }

  public getDeviceToken(): string | null {
    return this.deviceToken;
  }

  public isReady(): boolean {
    return this.isInitialized;
  }
}

// Export singleton instance
const notificationService = NotificationService.getInstance();
export default notificationService;
export type { NotificationData, PriceAlert };