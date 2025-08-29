# Trading Bot Pro - Mobile App Packaging Guide

This guide explains how to package the Trading Bot Pro mobile app for Android (APK/AAB) and iOS (TestFlight) distribution.

## Quick Start

### Windows Users (Android APK)
```bash
# Run the automated Windows build script
.\BUILD_ANDROID_APK.bat
```

### Cross-Platform (All Formats)
```bash
# Install dependencies
npm install

# Build Android APK and AAB
npm run package:android

# Build iOS archive (macOS only)
npm run package:ios

# Build all platforms
npm run package:all
```

## Prerequisites

### All Platforms
- **Node.js** 16+ and npm
- **React Native CLI**: `npm install -g @react-native-community/cli`
- **Git** for version control

### Android Development
- **Java JDK** 11 or higher
- **Android Studio** with Android SDK
- **Android SDK Build-Tools** 30.0.3+
- **Environment Variables**:
  ```bash
  ANDROID_HOME=C:\Users\YourName\AppData\Local\Android\Sdk
  JAVA_HOME=C:\Program Files\Java\jdk-11.0.x
  ```

### iOS Development (macOS Only)
- **Xcode** 12+ with Command Line Tools
- **CocoaPods**: `sudo gem install cocoapods`
- **Apple Developer Account** (for distribution)
- **iOS Simulator** (for testing)

## Available Build Scripts

### NPM Scripts
- `npm run package:android` - Build Android APK and AAB
- `npm run package:ios` - Build iOS archive for TestFlight
- `npm run package:all` - Build all platforms
- `npm run build:apk` - Build Android APK only
- `npm run build:aab` - Build Android App Bundle only
- `npm run clean` - Clean all build artifacts

### Platform-Specific Scripts
- `BUILD_ANDROID_APK.bat` - Windows automated Android build
- `build-mobile-packages.js` - Cross-platform Node.js build script

## Android Packaging

### APK (Android Package)

**What is APK?**
- Direct installation file for Android devices
- Can be installed via "Unknown Sources"
- Larger file size (includes all architectures)
- Good for testing and direct distribution

**Build APK:**
```bash
# Method 1: Use automated script (Windows)
.\BUILD_ANDROID_APK.bat

# Method 2: Use npm script
npm run build:apk

# Method 3: Manual Gradle
cd android
./gradlew assembleRelease
```

**Output:** `dist/TradingBotMobile-1.0.0.apk`

### AAB (Android App Bundle)

**What is AAB?**
- Google Play's preferred format
- Smaller download size (optimized per device)
- Required for Google Play Store uploads
- Supports dynamic delivery

**Build AAB:**
```bash
# Use npm script
npm run build:aab

# Manual Gradle
cd android
./gradlew bundleRelease
```

**Output:** `dist/TradingBotMobile-1.0.0.aab`

### Android Signing

The build scripts automatically generate a debug keystore. For production:

1. **Generate Production Keystore:**
   ```bash
   keytool -genkeypair -v -storetype PKCS12 -keystore release-key.keystore -alias release-key -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Update `android/gradle.properties`:**
   ```properties
   RELEASE_STORE_FILE=release-key.keystore
   RELEASE_KEY_ALIAS=release-key
   RELEASE_STORE_PASSWORD=your_store_password
   RELEASE_KEY_PASSWORD=your_key_password
   ```

3. **Secure Your Keystore:**
   - Store keystore file securely
   - Never commit passwords to version control
   - Keep backup of keystore (cannot be recovered if lost)

## iOS Packaging

### Prerequisites
- macOS with Xcode installed
- Apple Developer Account ($99/year)
- Valid iOS Distribution Certificate
- App Store Connect access

### Build iOS Archive

```bash
# Install CocoaPods dependencies
cd ios && pod install && cd ..

# Build archive
npm run package:ios

# Manual Xcode build
cd ios
xcodebuild archive -workspace TradingBotMobile.xcworkspace -scheme TradingBotMobile -configuration Release -archivePath TradingBotMobile.xcarchive
```

### TestFlight Distribution

1. **Open Xcode Organizer:**
   - Xcode → Window → Organizer
   - Select your archive

2. **Distribute App:**
   - Click "Distribute App"
   - Choose "App Store Connect"
   - Select "Upload" or "Export"

3. **App Store Connect:**
   - Go to [App Store Connect](https://appstoreconnect.apple.com)
   - Select your app
   - Go to TestFlight tab
   - Add internal/external testers

## Output Files

After successful builds, files are available in the `dist/` directory:

### Android
- `TradingBotMobile-1.0.0.apk` - Direct installation file
- `TradingBotMobile-1.0.0.aab` - Google Play Store upload
- `checksums.txt` - SHA256 checksums for verification
- `build-info.json` - Build metadata

### iOS
- `TradingBotMobile.xcarchive` - Xcode archive for distribution
- Use Xcode Organizer for final IPA generation

## App Configuration

### Environment Setup

Create `.env` file in the mobile app root:

```env
# API Configuration
API_BASE_URL=https://api.tradingbotpro.com
WS_URL=wss://ws.tradingbotpro.com
LICENSE_SERVER_URL=https://license.tradingbotpro.com

# App Configuration
APP_NAME=Trading Bot Pro
APP_VERSION=1.0.0
PACKAGE_NAME=com.tradingbotpro.mobile

# Feature Flags
ENABLE_DEMO_MODE=true
ENABLE_BIOMETRIC_AUTH=true
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_PAPER_TRADING=true

# Demo Configuration
DEMO_API_DELAY=1000
DEMO_PRICE_VOLATILITY=0.02
DEMO_STARTING_BALANCE=10000
```

### App Icons and Branding

**Android Icons:**
- `android/app/src/main/res/mipmap-*/ic_launcher.png`
- Use Android Asset Studio for proper sizing

**iOS Icons:**
- `ios/TradingBotMobile/Images.xcassets/AppIcon.appiconset/`
- Use Xcode or online tools for proper sizing

**Splash Screens:**
- Android: `android/app/src/main/res/drawable/launch_screen.xml`
- iOS: `ios/TradingBotMobile/LaunchScreen.storyboard`

## Testing

### Android Testing

1. **Install APK on Device:**
   ```bash
   adb install dist/TradingBotMobile-1.0.0.apk
   ```

2. **Test on Emulator:**
   ```bash
   # Start emulator
   emulator -avd Pixel_4_API_30
   
   # Install and test
   adb install dist/TradingBotMobile-1.0.0.apk
   ```

3. **Internal Testing (Google Play):**
   - Upload AAB to Google Play Console
   - Create Internal Testing track
   - Add test users via email

### iOS Testing

1. **Simulator Testing:**
   ```bash
   npx react-native run-ios --simulator="iPhone 14"
   ```

2. **Device Testing:**
   - Connect device via USB
   - Enable Developer Mode in iOS Settings
   - Build and run via Xcode

3. **TestFlight Testing:**
   - Upload archive via Xcode Organizer
   - Add testers in App Store Connect
   - Testers receive TestFlight app invitation

## Distribution

### Google Play Store (Android)

1. **Create Play Console Account:**
   - Go to [Google Play Console](https://play.google.com/console)
   - Pay $25 one-time registration fee

2. **Create App Listing:**
   - App name, description, screenshots
   - Privacy policy, content rating
   - Pricing and distribution settings

3. **Upload AAB:**
   - Go to Release → Production
   - Upload `TradingBotMobile-1.0.0.aab`
   - Complete store listing requirements
   - Submit for review

### Apple App Store (iOS)

1. **App Store Connect Setup:**
   - Create app record
   - Set app information, pricing
   - Add screenshots, description

2. **Upload Build:**
   - Use Xcode Organizer or Application Loader
   - Build appears in App Store Connect

3. **Submit for Review:**
   - Select build for release
   - Complete App Store Review Guidelines
   - Submit for Apple review

## Troubleshooting

### Common Android Issues

**Build Fails:**
```bash
# Clean and rebuild
cd android
./gradlew clean
./gradlew assembleRelease
```

**Keystore Issues:**
```bash
# Verify keystore
keytool -list -v -keystore android/app/release-key.keystore
```

**SDK Issues:**
```bash
# Check SDK installation
sdkmanager --list
```

### Common iOS Issues

**CocoaPods Issues:**
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
```

**Xcode Build Issues:**
```bash
# Clean build folder
cd ios
xcodebuild clean -workspace TradingBotMobile.xcworkspace -scheme TradingBotMobile
```

**Certificate Issues:**
- Check Apple Developer account status
- Verify certificates in Keychain Access
- Update provisioning profiles

### Performance Optimization

**Reduce APK Size:**
- Enable ProGuard/R8 in `android/app/build.gradle`
- Use AAB format for Play Store
- Optimize images and assets

**iOS Optimization:**
- Enable Bitcode in Xcode
- Optimize images for iOS
- Use App Thinning features

## Security Best Practices

### Code Signing
- Use strong passwords for keystores
- Store certificates securely
- Never commit signing keys to version control
- Use CI/CD for automated signing

### API Security
- Use HTTPS for all API calls
- Implement certificate pinning
- Store sensitive data in secure storage
- Validate all user inputs

### App Store Security
- Follow platform security guidelines
- Implement proper authentication
- Use biometric authentication when available
- Regular security updates

## Continuous Integration

### GitHub Actions Example

```yaml
name: Build Mobile Apps

on:
  push:
    tags:
      - 'v*'

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '16'
      - uses: actions/setup-java@v3
        with:
          java-version: '11'
      - run: npm install
      - run: npm run package:android
      - uses: actions/upload-artifact@v3
        with:
          name: android-builds
          path: dist/

  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '16'
      - run: npm install
      - run: cd ios && pod install
      - run: npm run package:ios
```

## Support and Resources

### Documentation
- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [Android Developer Guide](https://developer.android.com/guide)
- [iOS Developer Guide](https://developer.apple.com/documentation/)

### Tools
- [Android Studio](https://developer.android.com/studio)
- [Xcode](https://developer.apple.com/xcode/)
- [React Native Debugger](https://github.com/jhen0409/react-native-debugger)

### Community
- [React Native Community](https://github.com/react-native-community)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/react-native)
- [Discord/Slack Communities](https://reactnative.dev/help)

---

**Note:** This guide covers the basic packaging process. For production apps, consider additional factors like analytics, crash reporting, performance monitoring, and automated testing.