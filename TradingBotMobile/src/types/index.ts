/**
 * TypeScript type definitions for the Trading Bot Mobile App
 */

// User and Authentication Types
export interface User {
  id: string;
  email: string;
  displayName: string;
  avatar?: string;
  createdAt: Date;
  lastLoginAt: Date;
  isEmailVerified: boolean;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  currency: string;
  language: string;
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  pushEnabled: boolean;
  emailEnabled: boolean;
  priceAlerts: boolean;
  tradeConfirmations: boolean;
  marketUpdates: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setupCompleted: boolean;
}

// Trading Types
export interface Asset {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap?: number;
  high24h: number;
  low24h: number;
  lastUpdated: Date;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  margin: number;
  leverage: number;
  stopLoss?: number;
  takeProfit?: number;
  openedAt: Date;
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price: number;
  executedPrice?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  fee: number;
  timestamp: Date;
  orderId?: string;
}

export interface Portfolio {
  totalValue: number;
  availableBalance: number;
  unrealizedPnL: number;
  realizedPnL: number;
  totalPnL: number;
  totalPnLPercent: number;
  positions: Position[];
  assets: PortfolioAsset[];
}

export interface PortfolioAsset {
  symbol: string;
  name: string;
  balance: number;
  value: number;
  allocation: number;
  averagePrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

export interface TradingSettings {
  apiKey?: string;
  apiSecret?: string;
  exchange: string;
  maxRiskPerTrade: number;
  maxDailyLoss: number;
  stopLossPercentage: number;
  takeProfitPercentage: number;
  autoTradingEnabled: boolean;
  paperTradingMode: boolean;
  biometricEnabled: boolean;
  pushNotificationsEnabled: boolean;
  priceAlertsEnabled: boolean;
  tradeConfirmationsEnabled: boolean;
}

export interface TradingState {
  portfolio: Portfolio;
  watchlist: Asset[];
  recentTrades: Trade[];
  activePositions: Position[];
  settings: TradingSettings;
  isLoading: boolean;
  lastUpdated: Date;
}

// Order Types
export interface OrderRequest {
  symbol: string;
  type: 'buy' | 'sell';
  orderType: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price?: number;
  stopPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  timeInForce?: 'GTC' | 'IOC' | 'FOK';
}

export interface Order {
  id: string;
  clientOrderId?: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price?: number;
  stopPrice?: number;
  executedQuantity: number;
  averagePrice?: number;
  status: 'new' | 'partially_filled' | 'filled' | 'cancelled' | 'rejected' | 'expired';
  timeInForce: 'GTC' | 'IOC' | 'FOK';
  createdAt: Date;
  updatedAt: Date;
}

// Market Data Types
export interface MarketData {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  volume: number;
  high: number;
  low: number;
  change: number;
  changePercent: number;
  timestamp: Date;
}

export interface Candle {
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceAlert {
  id: string;
  symbol: string;
  condition: 'above' | 'below';
  targetPrice: number;
  currentPrice: number;
  isActive: boolean;
  createdAt: Date;
  triggeredAt?: Date;
}

// Navigation Types
export type RootStackParamList = {
  Loading: undefined;
  Login: undefined;
  SetupWizard: undefined;
  Main: undefined;
};

export type MainTabParamList = {
  Dashboard: undefined;
  Portfolio: undefined;
  Trading: undefined;
  Settings: undefined;
};

// Theme Types
export interface CustomTheme {
  dark: boolean;
  colors: {
    primary: string;
    onPrimary: string;
    primaryContainer: string;
    onPrimaryContainer: string;
    secondary: string;
    onSecondary: string;
    secondaryContainer: string;
    onSecondaryContainer: string;
    tertiary: string;
    onTertiary: string;
    tertiaryContainer: string;
    onTertiaryContainer: string;
    error: string;
    onError: string;
    errorContainer: string;
    onErrorContainer: string;
    background: string;
    onBackground: string;
    surface: string;
    onSurface: string;
    surfaceVariant: string;
    onSurfaceVariant: string;
    outline: string;
    outlineVariant: string;
    shadow: string;
    scrim: string;
    inverseSurface: string;
    inverseOnSurface: string;
    inversePrimary: string;
    // Trading specific colors
    success: string;
    onSuccess: string;
    warning: string;
    onWarning: string;
    buy: string;
    sell: string;
  };
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

// Notification Types
export interface Notification {
  id: string;
  title: string;
  body: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'trade' | 'price_alert';
  data?: any;
  read: boolean;
  createdAt: Date;
}

// Chart Types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  data: number[];
  color?: (opacity?: number) => string;
  strokeWidth?: number;
  withDots?: boolean;
  withScrollableDot?: boolean;
}

// Settings Types
export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  currency: string;
  language: string;
  biometricEnabled: boolean;
  pushNotificationsEnabled: boolean;
  priceAlertsEnabled: boolean;
  autoRefreshEnabled: boolean;
  refreshInterval: number;
}

// Exchange Types
export interface Exchange {
  id: string;
  name: string;
  displayName: string;
  logo?: string;
  supported: boolean;
  features: ExchangeFeatures;
}

export interface ExchangeFeatures {
  spot: boolean;
  futures: boolean;
  margin: boolean;
  options: boolean;
  lending: boolean;
}

// Utility Types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  key: string;
  direction: SortDirection;
}

export interface FilterConfig {
  [key: string]: any;
}

// Form Types
export interface FormField {
  value: string;
  error?: string;
  touched: boolean;
}

export interface LoginForm {
  email: FormField;
  password: FormField;
}

export interface RegisterForm {
  email: FormField;
  password: FormField;
  confirmPassword: FormField;
  displayName: FormField;
}

export interface TradeForm {
  symbol: FormField;
  side: 'buy' | 'sell';
  type: FormField;
  quantity: FormField;
  price: FormField;
  stopLoss: FormField;
  takeProfit: FormField;
}

// Event Types
export interface WebSocketEvent {
  type: string;
  data: any;
  timestamp: Date;
}

export interface PriceUpdateEvent extends WebSocketEvent {
  type: 'price_update';
  data: {
    symbol: string;
    price: number;
    change: number;
    volume: number;
  };
}

export interface OrderUpdateEvent extends WebSocketEvent {
  type: 'order_update';
  data: Order;
}

export interface PositionUpdateEvent extends WebSocketEvent {
  type: 'position_update';
  data: Position;
}

// Storage Types
export interface StorageKeys {
  USER_DATA: 'user_data';
  AUTH_TOKEN: 'auth_token';
  TRADING_SETTINGS: 'trading_settings';
  WATCHLIST: 'watchlist';
  PRICE_ALERTS: 'price_alerts';
  THEME_PREFERENCE: 'theme_preference';
  BIOMETRIC_ENABLED: 'biometric_enabled';
  SETUP_COMPLETED: 'setup_completed';
}

// Component Props Types
export interface ScreenProps {
  navigation: any;
  route: any;
}

export interface HeaderProps {
  title: string;
  showBack?: boolean;
  rightComponent?: React.ReactNode;
  onBackPress?: () => void;
}

export interface CardProps {
  children: React.ReactNode;
  style?: any;
  onPress?: () => void;
}

export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  style?: any;
}

export interface InputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  error?: string;
  secureTextEntry?: boolean;
  keyboardType?: any;
  autoCapitalize?: any;
  style?: any;
}