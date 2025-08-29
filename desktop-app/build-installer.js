const { build } = require('electron-builder');
const path = require('path');
const fs = require('fs');

// Configuration for building installers
const builderConfig = {
  appId: 'com.tradingbot.desktop',
  productName: 'Trading Bot Pro',
  directories: {
    output: 'dist/installers'
  },
  files: [
    'dist/**/*',
    'node_modules/**/*',
    'package.json',
    '!node_modules/.cache',
    '!node_modules/electron/dist'
  ],
  extraResources: [
    {
      from: '../backend',
      to: 'backend',
      filter: ['**/*', '!**/__pycache__', '!**/venv', '!**/node_modules']
    },
    {
      from: '../web-dashboard/dist',
      to: 'web-dashboard',
      filter: ['**/*']
    }
  ],
  win: {
    target: [
      {
        target: 'nsis',
        arch: ['x64', 'ia32']
      },
      {
        target: 'portable',
        arch: ['x64']
      }
    ],
    icon: 'assets/icon.ico',
    publisherName: 'Trading Bot Pro',
    verifyUpdateCodeSignature: false
  },
  nsis: {
    oneClick: false,
    allowElevation: true,
    allowToChangeInstallationDirectory: true,
    installerIcon: 'assets/icon.ico',
    uninstallerIcon: 'assets/icon.ico',
    installerHeaderIcon: 'assets/icon.ico',
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: 'Trading Bot Pro',
    include: 'installer-script.nsh'
  },
  portable: {
    artifactName: 'TradingBotPro-Portable-${version}-${arch}.${ext}'
  },
  mac: {
    target: [
      {
        target: 'dmg',
        arch: ['x64', 'arm64']
      },
      {
        target: 'zip',
        arch: ['x64', 'arm64']
      }
    ],
    icon: 'assets/icon.icns',
    category: 'public.app-category.finance',
    hardenedRuntime: true,
    gatekeeperAssess: false,
    entitlements: 'entitlements.mac.plist',
    entitlementsInherit: 'entitlements.mac.plist'
  },
  dmg: {
    title: 'Trading Bot Pro ${version}',
    icon: 'assets/icon.icns',
    background: 'assets/dmg-background.png',
    contents: [
      {
        x: 130,
        y: 220
      },
      {
        x: 410,
        y: 220,
        type: 'link',
        path: '/Applications'
      }
    ],
    window: {
      width: 540,
      height: 380
    }
  },
  linux: {
    target: [
      {
        target: 'AppImage',
        arch: ['x64']
      },
      {
        target: 'deb',
        arch: ['x64']
      },
      {
        target: 'rpm',
        arch: ['x64']
      },
      {
        target: 'tar.gz',
        arch: ['x64']
      }
    ],
    icon: 'assets/icon.png',
    category: 'Office',
    synopsis: 'Professional Trading Bot Application',
    description: 'Advanced cryptocurrency trading bot with multiple strategies and real-time monitoring.'
  },
  deb: {
    priority: 'optional',
    depends: ['python3', 'python3-pip', 'nodejs']
  },
  rpm: {
    depends: ['python3', 'python3-pip', 'nodejs', 'npm']
  },
  appImage: {
    artifactName: 'TradingBotPro-${version}-${arch}.${ext}'
  },
  publish: null // Disable auto-publishing
};

// Build function
async function buildInstaller(platform = process.platform) {
  console.log(`Building installer for ${platform}...`);
  
  try {
    // Ensure output directory exists
    const outputDir = path.join(__dirname, 'dist', 'installers');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Build configuration based on platform
    let targets;
    switch (platform) {
      case 'win32':
        targets = 'win';
        break;
      case 'darwin':
        targets = 'mac';
        break;
      case 'linux':
        targets = 'linux';
        break;
      default:
        targets = platform;
    }
    
    // Build the installer
    const result = await build({
      targets: targets ? [targets] : undefined,
      config: builderConfig,
      publish: 'never'
    });
    
    console.log('✅ Installer built successfully!');
    console.log('📦 Output files:');
    result.forEach(file => {
      console.log(`   ${file}`);
    });
    
    return result;
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// CLI handling
if (require.main === module) {
  const args = process.argv.slice(2);
  const platform = args[0] || process.platform;
  
  console.log('🚀 Trading Bot Pro Installer Builder');
  console.log('=====================================');
  
  buildInstaller(platform);
}

module.exports = { buildInstaller, builderConfig };