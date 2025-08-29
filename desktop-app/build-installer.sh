#!/bin/bash

echo "========================================"
echo "Trading Bot Pro - Cross-Platform Installer Builder"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed or not in PATH"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    print_error "npm is not available"
    echo "Please ensure Node.js is properly installed"
    exit 1
fi

print_success "Node.js and npm are available"
echo

# Detect platform
PLATFORM=$(uname -s)
case $PLATFORM in
    Darwin*)
        PLATFORM_NAME="macOS"
        BUILD_TARGET="darwin"
        ;;
    Linux*)
        PLATFORM_NAME="Linux"
        BUILD_TARGET="linux"
        ;;
    CYGWIN*|MINGW*|MSYS*)
        PLATFORM_NAME="Windows"
        BUILD_TARGET="win32"
        ;;
    *)
        PLATFORM_NAME="Unknown"
        BUILD_TARGET="linux"
        print_warning "Unknown platform: $PLATFORM, defaulting to Linux"
        ;;
esac

print_info "Detected platform: $PLATFORM_NAME"
echo

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_info "Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies"
        exit 1
    fi
    print_success "Dependencies installed successfully"
    echo
fi

# Install electron-builder if not present
if ! npm list electron-builder &> /dev/null; then
    print_info "Installing electron-builder..."
    npm install --save-dev electron-builder
    if [ $? -ne 0 ]; then
        print_error "Failed to install electron-builder"
        exit 1
    fi
    print_success "electron-builder installed successfully"
    echo
fi

# Build the application first
print_info "Building the application..."
npm run build
if [ $? -ne 0 ]; then
    print_error "Failed to build the application"
    exit 1
fi
print_success "Application built successfully"
echo

# Allow user to choose platform or build for current platform
if [ "$1" != "" ]; then
    BUILD_TARGET="$1"
    print_info "Building for specified platform: $1"
else
    echo "Choose build target:"
    echo "1) Current platform ($PLATFORM_NAME)"
    echo "2) Windows (win32)"
    echo "3) macOS (darwin)"
    echo "4) Linux (linux)"
    echo "5) All platforms"
    echo
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            # Use detected platform
            ;;
        2)
            BUILD_TARGET="win32"
            ;;
        3)
            BUILD_TARGET="darwin"
            ;;
        4)
            BUILD_TARGET="linux"
            ;;
        5)
            BUILD_TARGET="all"
            ;;
        *)
            print_warning "Invalid choice, using current platform"
            ;;
    esac
fi

# Build the installer
print_info "Building installer for $BUILD_TARGET..."
if [ "$BUILD_TARGET" = "all" ]; then
    print_info "Building for all platforms (this may take a while)..."
    node build-installer.js win32
    node build-installer.js darwin
    node build-installer.js linux
else
    node build-installer.js $BUILD_TARGET
fi

if [ $? -ne 0 ]; then
    print_error "Failed to build installer"
    exit 1
fi

echo
echo "========================================"
print_success "Installer(s) built successfully!"
echo "========================================"
echo
print_info "Installer files are located in: dist/installers"
echo

if [ "$BUILD_TARGET" = "darwin" ] || [ "$BUILD_TARGET" = "all" ]; then
    echo "macOS installers:"
    echo "  • DMG (.dmg) - Disk image for easy installation"
    echo "  • ZIP (.zip) - Compressed application bundle"
fi

if [ "$BUILD_TARGET" = "linux" ] || [ "$BUILD_TARGET" = "all" ]; then
    echo "Linux installers:"
    echo "  • AppImage (.AppImage) - Portable application"
    echo "  • DEB (.deb) - Debian/Ubuntu package"
    echo "  • RPM (.rpm) - Red Hat/Fedora package"
    echo "  • TAR.GZ (.tar.gz) - Compressed archive"
fi

if [ "$BUILD_TARGET" = "win32" ] || [ "$BUILD_TARGET" = "all" ]; then
    echo "Windows installers:"
    echo "  • NSIS Installer (.exe) - Full installer with uninstaller"
    echo "  • Portable (.exe) - Standalone executable"
fi

echo
print_success "You can now distribute these files to users!"
echo

# Open the output directory (macOS only)
if [ "$PLATFORM" = "Darwin" ]; then
    read -p "Open installer folder? (y/n): " open_folder
    if [ "$open_folder" = "y" ] || [ "$open_folder" = "Y" ]; then
        open "dist/installers"
    fi
fi

echo "Build completed successfully!"