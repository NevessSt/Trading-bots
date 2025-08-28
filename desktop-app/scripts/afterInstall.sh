#!/bin/bash

# Post-installation script for Trading Bot Desktop
# This script runs after the package is installed

set -e

APP_NAME="trading-bot-desktop"
APP_DIR="/opt/Trading Bot Desktop"
DESKTOP_FILE="/usr/share/applications/trading-bot-desktop.desktop"
ICON_DIR="/usr/share/icons/hicolor"

echo "Setting up Trading Bot Desktop..."

# Create desktop entry
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Trading Bot Desktop
Comment=Professional Trading Bot Desktop Application
Exec="$APP_DIR/trading-bot-desktop" %U
Icon=trading-bot-desktop
Type=Application
Categories=Office;Finance;
MimeType=x-scheme-handler/trading-bot;
StartupNotify=true
StartupWMClass=Trading Bot Desktop
EOF

# Set proper permissions for desktop file
chmod 644 "$DESKTOP_FILE"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Install icon if it exists
if [ -f "$APP_DIR/resources/assets/icon.svg" ]; then
    # Create icon directories
    mkdir -p "$ICON_DIR/scalable/apps"
    mkdir -p "$ICON_DIR/256x256/apps"
    mkdir -p "$ICON_DIR/128x128/apps"
    mkdir -p "$ICON_DIR/64x64/apps"
    mkdir -p "$ICON_DIR/48x48/apps"
    mkdir -p "$ICON_DIR/32x32/apps"
    mkdir -p "$ICON_DIR/16x16/apps"
    
    # Copy SVG icon
    cp "$APP_DIR/resources/assets/icon.svg" "$ICON_DIR/scalable/apps/trading-bot-desktop.svg"
    
    # Update icon cache
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
    fi
fi

# Set up URL handler
if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default trading-bot-desktop.desktop x-scheme-handler/trading-bot
fi

# Create symlink in /usr/local/bin for command line access
if [ ! -L "/usr/local/bin/trading-bot-desktop" ]; then
    ln -sf "$APP_DIR/trading-bot-desktop" "/usr/local/bin/trading-bot-desktop"
fi

# Set proper permissions for the application
chmod +x "$APP_DIR/trading-bot-desktop"

# Create application data directory
APP_DATA_DIR="/var/lib/trading-bot-desktop"
if [ ! -d "$APP_DATA_DIR" ]; then
    mkdir -p "$APP_DATA_DIR"
    chmod 755 "$APP_DATA_DIR"
fi

# Create log directory
LOG_DIR="/var/log/trading-bot-desktop"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
fi

echo "Trading Bot Desktop installation completed successfully!"
echo "You can now launch the application from your applications menu or run 'trading-bot-desktop' from the command line."

exit 0