# 📦 Installation Guide - Complete Setup Instructions

## 🎯 Overview

This guide will help you install and set up your trading bot system. Choose the installation method that works best for you:

- **Desktop App** (Recommended): Full-featured Windows application
- **Web Dashboard**: Browser-based interface
- **Both**: Maximum flexibility

---

## 🖥️ Desktop App Installation

### System Requirements

**Minimum Requirements:**
- Windows 10 (64-bit) or later
- 4GB RAM
- 1GB free disk space
- Internet connection
- Administrator privileges

**Recommended:**
- Windows 11
- 8GB+ RAM
- SSD storage
- Stable broadband connection

### Step-by-Step Installation

#### Step 1: Download the Installer

1. **Navigate to Installation Files**
   ```
   C:\Users\pc\Desktop\trading bots\desktop-app\dist\
   ```

2. **Find the Installer**
   - Look for file ending in `.exe`
   - Example: `Trading-Bot-Setup-1.0.0.exe`
   - File size should be 100-200MB

3. **Verify File Integrity** (Optional but Recommended)
   - Right-click installer → Properties
   - Check file size matches expected
   - Scan with antivirus if desired

#### Step 2: Run the Installer

1. **Right-click the installer**
2. **Select "Run as administrator"**
   - This ensures proper installation
   - Windows may show security warning - click "Yes"

3. **Follow Installation Wizard**
   - **Welcome Screen**: Click "Next"
   - **License Agreement**: Read and accept
   - **Installation Location**: 
     - Default: `C:\Program Files\Trading Bot\`
     - Change if desired, click "Next"
   - **Start Menu Folder**: Keep default, click "Next"
   - **Desktop Shortcut**: Check box if wanted
   - **Ready to Install**: Click "Install"

4. **Wait for Installation**
   - Progress bar will show installation status
   - Takes 2-5 minutes depending on system
   - Don't close or interrupt the process

5. **Complete Installation**
   - Check "Launch Trading Bot" if you want to start immediately
   - Click "Finish"

#### Step 3: First Launch

1. **Start the Application**
   - From Start Menu: Search "Trading Bot"
   - From Desktop: Double-click shortcut
   - From Programs: Navigate to installation folder

2. **Windows Security Prompt**
   - Windows may ask for firewall permission
   - Click "Allow access" for both private and public networks
   - This allows the app to connect to exchanges

3. **Initial Setup Wizard**
   - App will launch setup wizard on first run
   - Follow prompts to configure basic settings
   - You can skip and configure later if preferred

### Troubleshooting Desktop Installation

**"Windows protected your PC" message:**
- Click "More info"
- Click "Run anyway"
- This is normal for new applications

**Installation fails:**
- Ensure you're running as administrator
- Temporarily disable antivirus
- Check available disk space
- Try installing to different location

**App won't start after installation:**
- Right-click app icon → "Run as administrator"
- Check Windows Event Viewer for error details
- Try compatibility mode (Windows 8/7)

---

## 🌐 Web Dashboard Installation

### Prerequisites

**Required Software:**
- Node.js (version 18.16.0 or later)
- npm (comes with Node.js)
- Modern web browser

### Step-by-Step Setup

#### Step 1: Verify Node.js Installation

1. **Open Command Prompt**
   - Press `Windows + R`
   - Type `cmd` and press Enter

2. **Check Node.js Version**
   ```
   node --version
   ```
   - Should show v18.16.0 or higher
   - If not installed, download from nodejs.org

3. **Check npm Version**
   ```
   npm --version
   ```
   - Should show version 6.0 or higher

#### Step 2: Navigate to Web Dashboard

1. **Open Command Prompt as Administrator**
   - Right-click Start button
   - Select "Windows PowerShell (Admin)" or "Command Prompt (Admin)"

2. **Navigate to Project Directory**
   ```
   cd "C:\Users\pc\Desktop\trading bots\web-dashboard"
   ```

3. **Verify You're in Correct Directory**
   ```
   dir
   ```
   - Should see files like `package.json`, `src` folder, etc.

#### Step 3: Install Dependencies

1. **Install Required Packages**
   ```
   npm install
   ```
   - This downloads all required libraries
   - Takes 2-5 minutes depending on internet speed
   - You'll see progress indicators

2. **Wait for Completion**
   - Process completes when you see command prompt again
   - Should show "added X packages" message
   - Ignore warning messages (they're normal)

#### Step 4: Start Development Server

1. **Launch the Server**
   ```
   npm run dev
   ```

2. **Wait for Server to Start**
   - You'll see "VITE v4.5.3 ready" message
   - Server URL will be displayed: `http://localhost:5173/`
   - Keep this command prompt window open

3. **Open in Browser**
   - Open your web browser
   - Go to `http://localhost:5173/`
   - Dashboard should load automatically

### Web Dashboard Troubleshooting

**"npm is not recognized" error:**
- Node.js not installed or not in PATH
- Download and install Node.js from nodejs.org
- Restart command prompt after installation

**"EACCES permission denied" error:**
- Run command prompt as administrator
- Or use: `npm install --unsafe-perm=true`

**Port 5173 already in use:**
- Another application is using the port
- Kill other processes or use different port:
  ```
  npm run dev -- --port 3000
  ```

**Browser shows "This site can't be reached":**
- Ensure development server is running
- Check firewall isn't blocking port 5173
- Try `http://127.0.0.1:5173/` instead

---

## 🔧 Post-Installation Configuration

### Desktop App Configuration

#### Initial Settings

1. **Launch Application**
2. **Go to Settings** (gear icon or Settings menu)
3. **Configure Basic Preferences:**
   - **Theme**: Light/Dark mode
   - **Language**: Select preferred language
   - **Notifications**: Enable/disable alerts
   - **Auto-start**: Launch with Windows (optional)

#### API Configuration

1. **Navigate to API Settings**
   - Settings → "API Configuration"
   - Or "Exchange" tab in main interface

2. **Add Exchange Credentials**
   - Select your exchange (Binance, Coinbase, etc.)
   - Enter API Key and Secret
   - **Important**: Never share these credentials

3. **Test Connection**
   - Click "Test Connection" button
   - Should show green checkmark if successful
   - Red X indicates configuration issues

4. **Set Permissions**
   - Ensure API key has "Spot Trading" permissions
   - Enable "Read" and "Trade" permissions
   - Disable "Withdraw" for security

### Web Dashboard Configuration

#### Browser Settings

1. **Recommended Browsers**
   - Google Chrome (preferred)
   - Microsoft Edge
   - Mozilla Firefox
   - Safari (Mac)

2. **Browser Configuration**
   - Enable JavaScript
   - Allow pop-ups for localhost
   - Clear cache if experiencing issues

#### Performance Optimization

1. **Close Unnecessary Tabs**
   - Web dashboard uses significant resources
   - Close other heavy websites

2. **Disable Extensions**
   - Ad blockers may interfere
   - Temporarily disable if issues occur

---

## 🔒 Security Setup

### API Key Security

1. **Create Dedicated API Keys**
   - Don't use existing keys from other applications
   - Create new keys specifically for trading bot

2. **Enable IP Restrictions**
   - Add your current IP address to whitelist
   - Find IP at whatismyipaddress.com
   - Update if your IP changes

3. **Set Appropriate Permissions**
   - ✅ Enable: Read, Spot Trading
   - ❌ Disable: Withdraw, Futures (unless needed)
   - ❌ Disable: Margin Trading (unless experienced)

### System Security

1. **Windows Firewall**
   - Allow trading bot through firewall
   - Both private and public networks

2. **Antivirus Configuration**
   - Add trading bot to exceptions
   - Prevents false positive detections
   - Improves performance

3. **Regular Updates**
   - Keep Windows updated
   - Update trading bot when new versions available
   - Update browser regularly

---

## 📋 Installation Checklist

### Pre-Installation
- [ ] System meets minimum requirements
- [ ] Administrator access available
- [ ] Stable internet connection
- [ ] Antivirus temporarily disabled (if needed)

### Desktop App Installation
- [ ] Installer downloaded from correct location
- [ ] Ran installer as administrator
- [ ] Installation completed successfully
- [ ] App launches without errors
- [ ] Firewall permissions granted

### Web Dashboard Installation
- [ ] Node.js installed and working
- [ ] Dependencies installed successfully
- [ ] Development server starts
- [ ] Dashboard loads in browser
- [ ] No console errors in browser

### Post-Installation
- [ ] API keys configured and tested
- [ ] Basic settings configured
- [ ] Security measures implemented
- [ ] Test trades executed successfully
- [ ] Documentation reviewed

---

## 🔄 Updating the Software

### Desktop App Updates

1. **Automatic Updates** (if enabled)
   - App will notify when updates available
   - Click "Update Now" to download and install
   - App will restart automatically

2. **Manual Updates**
   - Download new installer
   - Run installer (will update existing installation)
   - Settings and data are preserved

### Web Dashboard Updates

1. **Pull Latest Changes**
   ```
   cd "C:\Users\pc\Desktop\trading bots\web-dashboard"
   git pull origin main
   ```

2. **Update Dependencies**
   ```
   npm install
   ```

3. **Restart Server**
   - Stop current server (Ctrl+C)
   - Start again: `npm run dev`

---

## 🆘 Getting Help

### Self-Help Resources

1. **Documentation**
   - Read `USER_GUIDE.md` for detailed usage
   - Check `TROUBLESHOOTING.md` for common issues
   - Review `QUICK_START.md` for basic setup

2. **Application Logs**
   - Desktop: Settings → View Logs
   - Web: Browser console (F12)

3. **Online Resources**
   - Exchange documentation
   - Trading bot forums and communities
   - YouTube tutorials

### When to Seek Support

- Installation fails repeatedly
- Security concerns
- Data corruption issues
- Persistent technical problems

---

**🎉 Congratulations! Your trading bot system is now installed and ready to use.**

*Next Steps: Read the `QUICK_START.md` guide to begin trading in 5 minutes!*

---

**Last Updated**: January 2024  
**Version**: 1.0