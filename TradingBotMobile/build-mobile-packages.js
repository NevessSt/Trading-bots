#!/usr/bin/env node

/**
 * Mobile App Packaging Script for Trading Bot Pro
 * Builds Android APK and prepares iOS for TestFlight distribution
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const os = require('os');

// Configuration
const CONFIG = {
  appName: 'TradingBotMobile',
  version: '1.0.0',
  buildNumber: Date.now().toString(),
  outputDir: path.join(__dirname, 'dist'),
  androidOutputDir: path.join(__dirname, 'android', 'app', 'build', 'outputs', 'apk', 'release'),
  iosOutputDir: path.join(__dirname, 'ios', 'build'),
  keystorePath: path.join(__dirname, 'android', 'app', 'release-key.keystore'),
  keystoreAlias: 'release-key',
  packageName: 'com.tradingbotpro.mobile'
};

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Utility functions
function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function error(message) {
  log(`❌ ${message}`, 'red');
}

function success(message) {
  log(`✅ ${message}`, 'green');
}

function info(message) {
  log(`ℹ️  ${message}`, 'blue');
}

function warning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

function executeCommand(command, options = {}) {
  try {
    log(`Executing: ${command}`, 'cyan');
    const result = execSync(command, {
      stdio: 'inherit',
      cwd: __dirname,
      ...options
    });
    return result;
  } catch (err) {
    error(`Command failed: ${command}`);
    error(err.message);
    process.exit(1);
  }
}

function checkPrerequisites() {
  info('Checking prerequisites...');
  
  // Check Node.js
  try {
    const nodeVersion = execSync('node --version', { encoding: 'utf8' }).trim();
    success(`Node.js version: ${nodeVersion}`);
  } catch (err) {
    error('Node.js is not installed or not in PATH');
    process.exit(1);
  }
  
  // Check React Native CLI
  try {
    execSync('npx react-native --version', { stdio: 'pipe' });
    success('React Native CLI is available');
  } catch (err) {
    warning('React Native CLI not found, will use npx');
  }
  
  // Check Java (for Android)
  try {
    const javaVersion = execSync('java -version 2>&1', { encoding: 'utf8' });
    if (javaVersion.includes('version')) {
      success('Java is installed');
    }
  } catch (err) {
    warning('Java not found - required for Android builds');
  }
  
  // Check Android SDK
  const androidHome = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT;
  if (androidHome && fs.existsSync(androidHome)) {
    success(`Android SDK found at: ${androidHome}`);
  } else {
    warning('Android SDK not found - set ANDROID_HOME environment variable');
  }
  
  // Check Xcode (macOS only)
  if (os.platform() === 'darwin') {
    try {
      execSync('xcodebuild -version', { stdio: 'pipe' });
      success('Xcode is installed');
    } catch (err) {
      warning('Xcode not found - required for iOS builds');
    }
  }
}

function installDependencies() {
  info('Installing dependencies...');
  
  if (!fs.existsSync('node_modules')) {
    executeCommand('npm install');
  } else {
    info('Dependencies already installed');
  }
  
  // Install iOS pods (macOS only)
  if (os.platform() === 'darwin' && fs.existsSync('ios')) {
    info('Installing iOS CocoaPods dependencies...');
    executeCommand('cd ios && pod install && cd ..', { shell: true });
  }
}

function createOutputDirectory() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    success(`Created output directory: ${CONFIG.outputDir}`);
  }
}

function generateKeystore() {
  if (!fs.existsSync(CONFIG.keystorePath)) {
    warning('Release keystore not found. Generating a new one...');
    warning('In production, use a proper keystore with strong passwords!');
    
    const keystoreDir = path.dirname(CONFIG.keystorePath);
    if (!fs.existsSync(keystoreDir)) {
      fs.mkdirSync(keystoreDir, { recursive: true });
    }
    
    const command = `keytool -genkeypair -v -storetype PKCS12 -keystore "${CONFIG.keystorePath}" -alias ${CONFIG.keystoreAlias} -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Trading Bot Pro, OU=Mobile, O=Trading Bot Pro, L=City, S=State, C=US"`;
    
    try {
      executeCommand(command);
      success('Keystore generated successfully');
    } catch (err) {
      error('Failed to generate keystore. Please install Java JDK.');
      process.exit(1);
    }
  } else {
    success('Release keystore found');
  }
}

function updateGradleProperties() {
  const gradlePropsPath = path.join(__dirname, 'android', 'gradle.properties');
  const keystoreConfig = `
# Release keystore configuration
RELEASE_STORE_FILE=${CONFIG.keystorePath}
RELEASE_KEY_ALIAS=${CONFIG.keystoreAlias}
RELEASE_STORE_PASSWORD=android
RELEASE_KEY_PASSWORD=android
`;
  
  if (fs.existsSync(gradlePropsPath)) {
    let content = fs.readFileSync(gradlePropsPath, 'utf8');
    if (!content.includes('RELEASE_STORE_FILE')) {
      fs.appendFileSync(gradlePropsPath, keystoreConfig);
      success('Updated gradle.properties with keystore configuration');
    }
  } else {
    fs.writeFileSync(gradlePropsPath, keystoreConfig);
    success('Created gradle.properties with keystore configuration');
  }
}

function buildAndroidAPK() {
  info('Building Android APK...');
  
  // Clean previous builds
  executeCommand('cd android && ./gradlew clean', { shell: true });
  
  // Build release APK
  executeCommand('cd android && ./gradlew assembleRelease', { shell: true });
  
  // Copy APK to output directory
  const apkPath = path.join(CONFIG.androidOutputDir, 'app-release.apk');
  const outputApkPath = path.join(CONFIG.outputDir, `${CONFIG.appName}-${CONFIG.version}.apk`);
  
  if (fs.existsSync(apkPath)) {
    fs.copyFileSync(apkPath, outputApkPath);
    success(`Android APK built successfully: ${outputApkPath}`);
    
    // Get APK size
    const stats = fs.statSync(outputApkPath);
    const fileSizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
    info(`APK size: ${fileSizeInMB} MB`);
    
    return outputApkPath;
  } else {
    error('APK build failed - output file not found');
    process.exit(1);
  }
}

function buildAndroidAAB() {
  info('Building Android App Bundle (AAB)...');
  
  // Build release AAB
  executeCommand('cd android && ./gradlew bundleRelease', { shell: true });
  
  // Copy AAB to output directory
  const aabPath = path.join(__dirname, 'android', 'app', 'build', 'outputs', 'bundle', 'release', 'app-release.aab');
  const outputAabPath = path.join(CONFIG.outputDir, `${CONFIG.appName}-${CONFIG.version}.aab`);
  
  if (fs.existsSync(aabPath)) {
    fs.copyFileSync(aabPath, outputAabPath);
    success(`Android AAB built successfully: ${outputAabPath}`);
    
    // Get AAB size
    const stats = fs.statSync(outputAabPath);
    const fileSizeInMB = (stats.size / (1024 * 1024)).toFixed(2);
    info(`AAB size: ${fileSizeInMB} MB`);
    
    return outputAabPath;
  } else {
    error('AAB build failed - output file not found');
    return null;
  }
}

function prepareiOSBuild() {
  if (os.platform() !== 'darwin') {
    warning('iOS builds are only supported on macOS');
    return null;
  }
  
  info('Preparing iOS build...');
  
  // Clean previous builds
  executeCommand('cd ios && xcodebuild clean -workspace TradingBotMobile.xcworkspace -scheme TradingBotMobile', { shell: true });
  
  // Archive the app
  const archivePath = path.join(CONFIG.iosOutputDir, `${CONFIG.appName}.xcarchive`);
  const command = `cd ios && xcodebuild archive -workspace TradingBotMobile.xcworkspace -scheme TradingBotMobile -configuration Release -archivePath "${archivePath}" -allowProvisioningUpdates`;
  
  try {
    executeCommand(command, { shell: true });
    success(`iOS archive created: ${archivePath}`);
    
    info('To distribute via TestFlight:');
    info('1. Open Xcode');
    info('2. Go to Window > Organizer');
    info('3. Select your archive and click "Distribute App"');
    info('4. Choose "App Store Connect" and follow the prompts');
    
    return archivePath;
  } catch (err) {
    error('iOS archive failed. Check Xcode configuration and certificates.');
    return null;
  }
}

function generateChecksums(filePaths) {
  const crypto = require('crypto');
  const checksums = {};
  
  filePaths.forEach(filePath => {
    if (fs.existsSync(filePath)) {
      const fileBuffer = fs.readFileSync(filePath);
      const hashSum = crypto.createHash('sha256');
      hashSum.update(fileBuffer);
      const hex = hashSum.digest('hex');
      checksums[path.basename(filePath)] = hex;
    }
  });
  
  const checksumPath = path.join(CONFIG.outputDir, 'checksums.txt');
  const checksumContent = Object.entries(checksums)
    .map(([file, hash]) => `${hash}  ${file}`)
    .join('\n');
  
  fs.writeFileSync(checksumPath, checksumContent);
  success(`Checksums generated: ${checksumPath}`);
}

function createBuildInfo() {
  const buildInfo = {
    appName: CONFIG.appName,
    version: CONFIG.version,
    buildNumber: CONFIG.buildNumber,
    buildDate: new Date().toISOString(),
    platform: os.platform(),
    nodeVersion: process.version,
    reactNativeVersion: require('./package.json').dependencies['react-native']
  };
  
  const buildInfoPath = path.join(CONFIG.outputDir, 'build-info.json');
  fs.writeFileSync(buildInfoPath, JSON.stringify(buildInfo, null, 2));
  success(`Build info created: ${buildInfoPath}`);
}

function main() {
  const args = process.argv.slice(2);
  const platform = args[0] || 'all';
  
  log('🚀 Trading Bot Pro - Mobile App Packaging', 'magenta');
  log('==========================================', 'magenta');
  
  checkPrerequisites();
  installDependencies();
  createOutputDirectory();
  
  const builtFiles = [];
  
  if (platform === 'android' || platform === 'all') {
    generateKeystore();
    updateGradleProperties();
    
    const apkPath = buildAndroidAPK();
    if (apkPath) builtFiles.push(apkPath);
    
    const aabPath = buildAndroidAAB();
    if (aabPath) builtFiles.push(aabPath);
  }
  
  if (platform === 'ios' || platform === 'all') {
    const archivePath = prepareiOSBuild();
    if (archivePath) builtFiles.push(archivePath);
  }
  
  if (builtFiles.length > 0) {
    generateChecksums(builtFiles);
    createBuildInfo();
    
    log('\n🎉 Build completed successfully!', 'green');
    log('Built files:', 'cyan');
    builtFiles.forEach(file => log(`  - ${file}`, 'cyan'));
    
    log('\nNext steps:', 'yellow');
    log('📱 Android: Upload APK/AAB to Google Play Console', 'yellow');
    log('🍎 iOS: Use Xcode Organizer to distribute via TestFlight', 'yellow');
  } else {
    error('No files were built successfully');
    process.exit(1);
  }
}

// Handle command line arguments
if (require.main === module) {
  main();
}

module.exports = {
  buildAndroidAPK,
  buildAndroidAAB,
  prepareiOSBuild,
  CONFIG
};