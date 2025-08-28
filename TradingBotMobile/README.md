# TradingBot Mobile App

A React Native mobile application for cryptocurrency trading with real-time market data, portfolio management, and automated trading features.

## Features

### 📱 Core Functionality
- **Real-time Trading**: Execute trades with live market data
- **Portfolio Management**: Track your investments and performance
- **Price Alerts**: Get notified when prices hit your targets
- **Watchlist**: Monitor your favorite cryptocurrencies
- **Order Management**: Place, modify, and cancel orders
- **Trading History**: View your complete trading history

### 🔐 Security & Authentication
- **Biometric Authentication**: Fingerprint and Face ID support
- **Secure Storage**: Encrypted local data storage
- **API Key Management**: Secure handling of exchange API keys
- **Session Management**: Automatic logout and token refresh

### 🎨 User Experience
- **Dark/Light Theme**: Automatic theme switching
- **Responsive Design**: Optimized for all screen sizes
- **Smooth Animations**: Fluid user interface transitions
- **Offline Support**: Basic functionality without internet
- **Push Notifications**: Real-time alerts and updates

### 📊 Advanced Features
- **Real-time Charts**: Interactive price charts with technical indicators
- **Risk Management**: Stop-loss and take-profit automation
- **Paper Trading**: Practice trading without real money
- **Multi-exchange Support**: Connect to multiple exchanges
- **WebSocket Integration**: Real-time data streaming

## Technology Stack

- **React Native**: Cross-platform mobile development
- **TypeScript**: Type-safe JavaScript development
- **React Navigation**: Navigation and routing
- **React Native Paper**: Material Design components
- **React Native Reanimated**: Smooth animations
- **Victory Native**: Charts and data visualization
- **AsyncStorage**: Local data persistence
- **MMKV**: High-performance key-value storage
- **React Native Keychain**: Secure credential storage
- **React Native Push Notification**: Push notifications

## Prerequisites

Before running the app, make sure you have:

- **Node.js** (v16 or higher)
- **React Native CLI** or **Expo CLI**
- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)
- **Java Development Kit (JDK)** (v11 or higher)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd TradingBotMobile
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Install iOS dependencies** (macOS only):
   ```bash
   cd ios && pod install && cd ..
   ```

4. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Update the configuration values

## Running the App

### Development Mode

**Start the Metro bundler**:
```bash
npm start
# or
yarn start
```

**Run on Android**:
```bash
npm run android
# or
yarn android
```

**Run on iOS** (macOS only):
```bash
npm run ios
# or
yarn ios
```

### Production Build

**Android APK**:
```bash
cd android
./gradlew assembleRelease
```

**iOS Archive** (macOS only):
```bash
xcodebuild -workspace ios/TradingBotMobile.xcworkspace -scheme TradingBotMobile archive
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   └── LoadingSpinner.tsx
├── context/            # React Context providers
│   ├── AuthContext.tsx
│   ├── ThemeContext.tsx
│   └── TradingContext.tsx
├── screens/            # Screen components
│   ├── DashboardScreen.tsx
│   ├── LoginScreen.tsx
│   ├── PortfolioScreen.tsx
│   ├── SettingsScreen.tsx
│   └── TradingScreen.tsx
├── services/           # API and external services
│   ├── ApiService.ts
│   ├── NotificationService.ts
│   ├── StorageService.ts
│   └── WebSocketService.ts
├── types/              # TypeScript type definitions
│   └── index.ts
└── utils/              # Utility functions
    ├── formatters.ts
    └── validation.ts
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
API_BASE_URL=https://api.tradingbot.com
WS_URL=wss://ws.tradingbot.com

# App Configuration
APP_NAME=TradingBot
APP_VERSION=1.0.0

# Feature Flags
ENABLE_BIOMETRIC_AUTH=true
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_PAPER_TRADING=true
```

### API Keys Setup

The app supports multiple cryptocurrency exchanges:

1. **Binance**: Get API keys from [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. **Coinbase Pro**: Get API keys from [Coinbase Pro API](https://pro.coinbase.com/profile/api)
3. **Kraken**: Get API keys from [Kraken API Management](https://www.kraken.com/u/security/api)

## Features Guide

### Authentication

- **Email/Password**: Standard authentication
- **Biometric**: Fingerprint or Face ID (if supported)
- **Auto-logout**: Configurable session timeout

### Trading

- **Market Orders**: Execute immediately at current price
- **Limit Orders**: Execute when price reaches specified level
- **Stop-Loss**: Automatic sell when price drops
- **Take-Profit**: Automatic sell when profit target reached

### Portfolio Management

- **Real-time Balance**: Live portfolio value updates
- **Asset Allocation**: Visual breakdown of holdings
- **Performance Tracking**: Profit/loss calculations
- **Transaction History**: Complete trading record

### Notifications

- **Price Alerts**: Custom price level notifications
- **Order Updates**: Trade execution notifications
- **Portfolio Changes**: Significant balance changes
- **Market News**: Important market updates

## Security

### Data Protection

- **Encryption**: All sensitive data encrypted at rest
- **Secure Storage**: API keys stored in device keychain
- **Network Security**: HTTPS/WSS for all communications
- **Biometric Lock**: Optional biometric app lock

### Best Practices

- Never share your API keys
- Use read-only API keys when possible
- Enable two-factor authentication on exchanges
- Regularly review API key permissions
- Use strong, unique passwords

## Troubleshooting

### Common Issues

**Metro bundler issues**:
```bash
npx react-native start --reset-cache
```

**Android build issues**:
```bash
cd android && ./gradlew clean && cd ..
```

**iOS build issues**:
```bash
cd ios && rm -rf Pods && pod install && cd ..
```

**Package conflicts**:
```bash
rm -rf node_modules && npm install
```

### Performance Optimization

- Enable Hermes JavaScript engine
- Use Flipper for debugging
- Optimize images and assets
- Implement lazy loading for screens
- Use FlatList for large data sets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style

- Use TypeScript for all new code
- Follow React Native best practices
- Use ESLint and Prettier for formatting
- Write meaningful commit messages
- Add JSDoc comments for functions

## Testing

**Run tests**:
```bash
npm test
# or
yarn test
```

**Run E2E tests**:
```bash
npm run test:e2e
# or
yarn test:e2e
```

## Deployment

### Android Play Store

1. Generate signed APK
2. Create Play Store listing
3. Upload APK and metadata
4. Submit for review

### iOS App Store

1. Archive the app in Xcode
2. Upload to App Store Connect
3. Create App Store listing
4. Submit for review

## Support

For support and questions:

- 📧 Email: support@tradingbot.com
- 💬 Discord: [TradingBot Community](https://discord.gg/tradingbot)
- 📖 Documentation: [docs.tradingbot.com](https://docs.tradingbot.com)
- 🐛 Issues: [GitHub Issues](https://github.com/tradingbot/mobile/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0 (Initial Release)
- Basic trading functionality
- Portfolio management
- Real-time market data
- Push notifications
- Biometric authentication
- Dark/light theme support

---

**Happy Trading! 📈**