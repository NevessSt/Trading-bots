# Trading Bot Mobile App - Complete User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Installation & Setup](#installation--setup)
3. [App Features](#app-features)
4. [Demo Trading Mode](#demo-trading-mode)
5. [Live Trading Mode](#live-trading-mode)
6. [Screen Navigation](#screen-navigation)
7. [Settings & Configuration](#settings--configuration)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Getting Started

### Prerequisites
- iOS 12.0+ or Android 8.0+
- Active internet connection
- Trading account (for live trading)

### Quick Start
1. Install the app on your device
2. Launch the app and complete initial setup
3. Choose between Demo or Live trading mode
4. Start exploring the features!

## Installation & Setup

### Development Installation

#### Prerequisites
- Node.js 16.0 or higher
- React Native CLI
- Android Studio (for Android)
- Xcode (for iOS, macOS only)

#### Step-by-Step Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NevessSt/Trading-bots.git
   cd Trading-bots/TradingBotMobile
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **iOS Setup (macOS only):**
   ```bash
   cd ios
   pod install
   cd ..
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory:
   ```env
   API_BASE_URL=http://localhost:5000
   WS_URL=ws://localhost:5000
   ENCRYPTION_KEY=your-encryption-key
   ```

5. **Run the app:**
   ```bash
   # For Android
   npx react-native run-android
   
   # For iOS
   npx react-native run-ios
   ```

### Production Installation

1. Download the app from:
   - **iOS:** App Store (coming soon)
   - **Android:** Google Play Store (coming soon)
   - **APK:** Direct download from releases

2. Install and launch the app
3. Follow the in-app setup wizard

## App Features

### 🏠 Dashboard
- **Portfolio Overview:** Real-time portfolio value and performance
- **Market Summary:** Key market indices and trending stocks
- **Quick Actions:** Fast access to buy/sell orders
- **Recent Activity:** Latest trades and notifications

### 📊 Trading
- **Order Placement:** Market, limit, and stop orders
- **Real-time Charts:** Interactive price charts with technical indicators
- **Watchlist:** Track your favorite stocks
- **Order History:** Complete trading history

### 💼 Portfolio
- **Holdings:** Current positions and performance
- **P&L Analysis:** Profit and loss breakdown
- **Asset Allocation:** Portfolio diversification view
- **Performance Metrics:** Returns, Sharpe ratio, and more

### 📈 Analytics
- **Performance Charts:** Historical portfolio performance
- **Risk Metrics:** Volatility, beta, and risk analysis
- **Sector Analysis:** Portfolio breakdown by sectors
- **Comparison Tools:** Benchmark against indices

### ⚙️ Settings
- **Account Management:** Profile and security settings
- **Trading Preferences:** Order defaults and confirmations
- **Notifications:** Alert preferences
- **Theme Selection:** Light/dark mode toggle

## Demo Trading Mode

### What is Demo Trading?
Demo trading allows you to practice trading with virtual money ($100,000 starting balance) without any financial risk. All trades are simulated but use real market data.

### Enabling Demo Mode
1. Open the app
2. Navigate to Settings or look for the Demo/Live toggle
3. Switch to "Demo" mode
4. Confirm the mode change

### Demo Features
- **Virtual Portfolio:** $100,000 starting balance
- **Real Market Data:** Live prices and charts
- **Full Trading Experience:** All order types available
- **Performance Tracking:** Complete analytics and reporting
- **Risk-Free Learning:** Perfect for beginners

### Demo Trading Workflow
1. **Switch to Demo Mode**
   - Use the Demo/Live toggle in the header
   - Confirm the mode switch

2. **Place Your First Trade**
   - Navigate to Trading screen
   - Search for a stock (e.g., AAPL)
   - Choose Buy or Sell
   - Enter quantity and price
   - Confirm the order

3. **Monitor Performance**
   - Check Portfolio screen for positions
   - View Paper Trading screen for detailed metrics
   - Track your progress over time

4. **Reset Portfolio**
   - Go to Paper Trading screen
   - Tap "Reset Portfolio" button
   - Confirm to start fresh with $100,000

### Paper Trading Screen
Access detailed demo trading analytics:
- **Portfolio Summary:** Equity, balance, and P&L
- **Performance Metrics:** Total return, win rate, trade count
- **Current Positions:** All open positions with unrealized P&L
- **Trade History:** Complete record of all demo trades
- **Reset Option:** Start over with fresh portfolio

## Live Trading Mode

### ⚠️ Important Warning
Live trading involves real money and actual financial risk. Only use live mode when you're confident in your trading strategy.

### Enabling Live Mode
1. Ensure you have a funded trading account
2. Configure API credentials in Settings
3. Switch to "Live" mode using the toggle
4. Confirm the mode change (warning dialog will appear)

### Live Trading Features
- **Real Money Trading:** Actual buy/sell orders
- **Account Integration:** Direct broker connectivity
- **Real-time Execution:** Immediate order processing
- **Regulatory Compliance:** All trades are properly recorded

### Safety Features
- **Confirmation Dialogs:** Double-check all orders
- **Position Limits:** Prevent over-leveraging
- **Stop Loss Orders:** Automatic risk management
- **Daily Loss Limits:** Configurable maximum daily losses

## Screen Navigation

### Bottom Tab Navigation
- **Dashboard** 🏠: Main overview screen
- **Trading** 📊: Order placement and charts
- **Portfolio** 💼: Holdings and performance
- **Analytics** 📈: Detailed analysis tools
- **Settings** ⚙️: App configuration

### Header Controls
- **Demo/Live Toggle:** Switch trading modes
- **Notifications:** 🔔 Alert center
- **Search:** 🔍 Find stocks quickly
- **Theme Toggle:** 🌙 Light/dark mode

### Gesture Controls
- **Pull to Refresh:** Update data on most screens
- **Swipe Navigation:** Move between chart timeframes
- **Long Press:** Access context menus
- **Pinch to Zoom:** Zoom in/out on charts

## Settings & Configuration

### Account Settings
- **Profile Information:** Name, email, phone
- **Security:** Password, 2FA, biometric login
- **API Configuration:** Broker connection settings

### Trading Preferences
- **Default Order Type:** Market, limit, or stop
- **Confirmation Settings:** Enable/disable order confirmations
- **Position Sizing:** Default trade amounts
- **Risk Management:** Stop loss and take profit defaults

### Notification Settings
- **Price Alerts:** Stock price notifications
- **Order Updates:** Trade execution alerts
- **Portfolio Alerts:** Performance notifications
- **News Alerts:** Market news updates

### Display Settings
- **Theme:** Light or dark mode
- **Chart Settings:** Default timeframes and indicators
- **Currency Display:** USD, EUR, etc.
- **Language:** App language selection

## Troubleshooting

### Common Issues

#### App Won't Start
- **Solution:** Clear app cache and restart
- **iOS:** Delete and reinstall app
- **Android:** Settings > Apps > Trading Bot > Storage > Clear Cache

#### Connection Issues
- **Check Internet:** Ensure stable connection
- **Server Status:** Check if backend services are running
- **Firewall:** Ensure app isn't blocked

#### Orders Not Executing
- **Demo Mode:** Check if you're in demo mode
- **API Credentials:** Verify broker connection
- **Market Hours:** Ensure markets are open
- **Insufficient Funds:** Check account balance

#### Data Not Updating
- **Pull to Refresh:** Swipe down on screens
- **Background Refresh:** Enable in device settings
- **App Permissions:** Ensure network access is allowed

#### Performance Issues
- **Close Other Apps:** Free up device memory
- **Restart App:** Force close and reopen
- **Update App:** Install latest version
- **Device Storage:** Ensure sufficient free space

### Error Messages

#### "Insufficient Balance"
- **Demo Mode:** Reset portfolio or reduce trade size
- **Live Mode:** Add funds to your account

#### "Market Closed"
- **Check Market Hours:** Trade during open hours
- **After Hours Trading:** Enable if supported

#### "Invalid Symbol"
- **Check Ticker:** Ensure correct stock symbol
- **Market Support:** Verify stock is supported

#### "Connection Failed"
- **Internet Connection:** Check network connectivity
- **Server Issues:** Try again later
- **VPN Issues:** Disable VPN if causing problems

### Getting Help

1. **In-App Support:** Settings > Help & Support
2. **Documentation:** Check this guide and FAQ
3. **Community:** Join our Discord/Telegram
4. **Email Support:** support@tradingbot.com
5. **GitHub Issues:** Report bugs on GitHub

## FAQ

### General Questions

**Q: Is the app free to use?**
A: The app is free to download and use in demo mode. Live trading may require broker fees.

**Q: What devices are supported?**
A: iOS 12.0+ and Android 8.0+ devices are supported.

**Q: Can I use multiple accounts?**
A: Currently, one account per app installation is supported.

### Demo Trading

**Q: Is demo trading data real?**
A: Yes, demo trading uses real market data but with virtual money.

**Q: Can I reset my demo portfolio?**
A: Yes, use the "Reset Portfolio" button in the Paper Trading screen.

**Q: How much virtual money do I start with?**
A: Demo accounts start with $100,000 virtual balance.

### Live Trading

**Q: Which brokers are supported?**
A: Currently supports major brokers via API integration. Check settings for full list.

**Q: Are there trading fees?**
A: Fees depend on your broker. The app doesn't charge additional fees.

**Q: Is my money safe?**
A: The app doesn't hold funds. All money remains with your broker.

### Technical Questions

**Q: Why is the app slow?**
A: Try closing other apps, restarting the device, or checking internet connection.

**Q: How do I update the app?**
A: Updates are available through the App Store (iOS) or Google Play (Android).

**Q: Can I use the app offline?**
A: No, the app requires internet connection for real-time data and trading.

### Security

**Q: How is my data protected?**
A: All data is encrypted and transmitted securely. We follow industry best practices.

**Q: Can I enable two-factor authentication?**
A: Yes, 2FA can be enabled in Security settings.

**Q: What if I lose my phone?**
A: Contact support immediately to secure your account.

---

## Support

For additional help:
- 📧 Email: support@tradingbot.com
- 💬 Discord: [Join our community](https://discord.gg/tradingbot)
- 📱 In-app support: Settings > Help & Support
- 🐛 Bug reports: [GitHub Issues](https://github.com/NevessSt/Trading-bots/issues)

---

*Last updated: January 2024*
*Version: 1.0.0*