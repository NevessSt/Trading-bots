# Trading Bot Pro - Desktop Installer Guide

This guide explains how to build and distribute desktop installers for Trading Bot Pro across different platforms.

## Quick Start

### Windows Installer
```bash
# Run the automated Windows build script
.\BUILD_INSTALLER_WINDOWS.bat

# Or manually:
npm install
npm run build-installer:win
```

### Cross-Platform Installers (macOS/Linux)
```bash
# Make the script executable (Linux/macOS)
chmod +x build-installer.sh

# Run for specific platform
./build-installer.sh mac    # macOS
./build-installer.sh linux  # Linux
./build-installer.sh all    # All platforms
```

## Available Build Scripts

### NPM Scripts
- `npm run build-installer` - Build for current platform
- `npm run build-installer:win` - Build Windows installer
- `npm run build-installer:mac` - Build macOS installer
- `npm run build-installer:linux` - Build Linux installer
- `npm run dist` - Build using electron-builder directly
- `npm run pack` - Create unpacked directory

### Platform-Specific Scripts
- `BUILD_INSTALLER_WINDOWS.bat` - Automated Windows build
- `build-installer.sh` - Cross-platform build script
- `build-installer.js` - Node.js build configuration

## Output Files

After building, installers will be available in the `dist/` directory:

### Windows
- `Trading Bot Desktop-Setup-1.0.0.exe` - NSIS installer
- `Trading Bot Desktop-1.0.0-portable.exe` - Portable version

### macOS
- `Trading Bot Desktop-1.0.0-x64.dmg` - Intel Mac installer
- `Trading Bot Desktop-1.0.0-arm64.dmg` - Apple Silicon installer
- `Trading Bot Desktop-1.0.0-x64.zip` - Intel Mac ZIP
- `Trading Bot Desktop-1.0.0-arm64.zip` - Apple Silicon ZIP

### Linux
- `Trading Bot Desktop-1.0.0-x64.AppImage` - Universal Linux app
- `Trading Bot Desktop-1.0.0-x64.deb` - Debian/Ubuntu package
- `Trading Bot Desktop-1.0.0-x64.rpm` - Red Hat/Fedora package
- `Trading Bot Desktop-1.0.0-x64.tar.gz` - Generic Linux archive

## Prerequisites

### All Platforms
- Node.js 16+ and npm 8+
- Git (for version control)

### Windows
- Windows 7+ (build environment)
- Visual Studio Build Tools (automatically installed)
- NSIS (automatically handled by electron-builder)

### macOS
- macOS 10.15+ (for building)
- Xcode Command Line Tools
- Apple Developer account (for code signing)

### Linux
- Ubuntu 18.04+ or equivalent
- Build essentials: `sudo apt-get install build-essential`
- For RPM builds: `sudo apt-get install rpm`

## Included Components

Each installer includes:

1. **Desktop Application** - Main Electron app
2. **Backend Services** - Python trading engine and API
3. **Web Dashboard** - React-based web interface
4. **License Server** - Local license activation system
5. **Demo Data** - Sample trading data and configurations

## Installation Features

### Windows (NSIS)
- Custom installer with branding
- Desktop and Start Menu shortcuts
- Uninstaller with clean removal
- Registry entries for proper integration
- Python dependency checking
- Component selection (Backend, Web Dashboard, Demo License)

### macOS (DMG)
- Drag-and-drop installation
- Code signing support
- Gatekeeper compatibility
- Universal binaries (Intel + Apple Silicon)

### Linux (Multiple Formats)
- AppImage: Portable, no installation required
- DEB: Debian/Ubuntu package manager integration
- RPM: Red Hat/Fedora package manager integration
- TAR.GZ: Manual installation archive

## Customization

### Branding Assets
Place your custom assets in the `assets/` directory:
- `icon.ico` - Windows icon
- `icon.icns` - macOS icon
- `icon.png` - Linux icon
- `installer-sidebar.bmp` - Windows installer sidebar
- `dmg-background.png` - macOS DMG background

### Installer Scripts
- `installer-script.nsh` - Custom NSIS installer script
- `entitlements.mac.plist` - macOS entitlements
- `afterInstall.sh` / `afterRemove.sh` - Linux post-install scripts

## Code Signing

### Windows
```bash
# Set environment variables for code signing
set CSC_LINK=path/to/certificate.p12
set CSC_KEY_PASSWORD=your_password
npm run build-installer:win
```

### macOS
```bash
# Set environment variables for code signing
export CSC_LINK=path/to/certificate.p12
export CSC_KEY_PASSWORD=your_password
export APPLE_ID=your@apple.id
export APPLE_ID_PASS=app-specific-password
npm run build-installer:mac
```

## Troubleshooting

### Common Issues

1. **Build fails on Windows**
   - Ensure Visual Studio Build Tools are installed
   - Run as Administrator if permission issues occur
   - Check that Python 3.8+ is installed

2. **macOS code signing fails**
   - Verify Apple Developer certificate is valid
   - Check Keychain Access for certificate issues
   - Ensure Xcode Command Line Tools are installed

3. **Linux build missing dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential libnss3-dev libatk-bridge2.0-dev libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
   ```

4. **Large installer size**
   - The installer includes the full backend and web dashboard
   - This is intentional for a complete standalone installation
   - Size: ~200-300MB depending on platform

### Debug Mode
```bash
# Enable debug output
DEBUG=electron-builder npm run build-installer

# Verbose logging
npm run build-installer -- --verbose
```

## Distribution

### GitHub Releases
The build configuration supports automatic publishing to GitHub Releases:

```bash
# Set GitHub token
export GH_TOKEN=your_github_token

# Build and publish
npm run dist -- --publish=always
```

### Manual Distribution
1. Upload installers to your preferred hosting service
2. Provide download links with platform detection
3. Include checksums for security verification

## Security Best Practices

1. **Code Signing**: Always sign your installers for production
2. **Checksums**: Provide SHA256 checksums for all installers
3. **HTTPS**: Distribute installers over secure connections only
4. **Verification**: Test installers on clean systems before release

## Support

For build issues or questions:
1. Check the electron-builder documentation
2. Review the build logs in the `dist/` directory
3. Test on the target platform before distribution
4. Ensure all dependencies are properly included

---

**Note**: Building for macOS requires a macOS system, and building for Windows works best on Windows. Cross-compilation has limitations for certain native dependencies.