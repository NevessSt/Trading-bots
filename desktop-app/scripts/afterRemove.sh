#!/bin/bash

# Post-removal script for Trading Bot Desktop
# This script runs after the package is removed

set -e

APP_NAME="trading-bot-desktop"
DESKTOP_FILE="/usr/share/applications/trading-bot-desktop.desktop"
ICON_DIR="/usr/share/icons/hicolor"
SYMLINK="/usr/local/bin/trading-bot-desktop"

echo "Cleaning up Trading Bot Desktop..."

# Remove desktop entry
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo "Removed desktop entry"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# Remove icons
find "$ICON_DIR" -name "trading-bot-desktop.*" -type f -delete 2>/dev/null || true

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

# Remove symlink
if [ -L "$SYMLINK" ]; then
    rm -f "$SYMLINK"
    echo "Removed command line symlink"
fi

# Remove URL handler association
if command -v xdg-mime >/dev/null 2>&1; then
    # Get current default handler
    CURRENT_HANDLER=$(xdg-mime query default x-scheme-handler/trading-bot 2>/dev/null || true)
    if [ "$CURRENT_HANDLER" = "trading-bot-desktop.desktop" ]; then
        # Reset to system default (usually browser)
        xdg-mime default firefox.desktop x-scheme-handler/trading-bot 2>/dev/null || true
    fi
fi

# Note: We don't remove user data directories (/var/lib/trading-bot-desktop, /var/log/trading-bot-desktop)
# as they may contain important user data. Users can manually remove them if needed.

echo "Trading Bot Desktop cleanup completed."
echo "Note: User data and logs have been preserved in /var/lib/trading-bot-desktop and /var/log/trading-bot-desktop"
echo "You can manually remove these directories if you no longer need the data."

exit 0