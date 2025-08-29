# Custom NSIS installer script for Trading Bot Pro
# This script provides additional customization for the Windows installer

# Installer attributes
!define PRODUCT_NAME "Trading Bot Pro"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Trading Bot Pro Team"
!define PRODUCT_WEB_SITE "https://tradingbotpro.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\TradingBotPro.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

# Modern UI
!include "MUI2.nsh"

# Variables
Var StartMenuFolder

# Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\wizard.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "assets\wizard.bmp"

# Welcome page
!define MUI_WELCOMEPAGE_TITLE "Welcome to Trading Bot Pro Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Trading Bot Pro.$\r$\n$\r$\nTrading Bot Pro is a professional cryptocurrency trading application with advanced strategies and real-time monitoring.$\r$\n$\r$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

# License page
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

# Components page
!insertmacro MUI_PAGE_COMPONENTS

# Directory page
!insertmacro MUI_PAGE_DIRECTORY

# Start menu page
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Trading Bot Pro"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

# Installation page
!insertmacro MUI_PAGE_INSTFILES

# Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\TradingBotPro.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_LINK "Visit the Trading Bot Pro website"
!define MUI_FINISHPAGE_LINK_LOCATION "https://tradingbotpro.com"
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Languages
!insertmacro MUI_LANGUAGE "English"

# Custom functions
Function .onInit
  # Check if application is already running
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "TradingBotProInstaller") i .r1 ?e'
  Pop $R0
  StrCmp $R0 0 +3
    MessageBox MB_OK|MB_ICONEXCLAMATION "The installer is already running."
    Abort
    
  # Check Windows version
  ${IfNot} ${AtLeastWin7}
    MessageBox MB_OK|MB_ICONSTOP "Trading Bot Pro requires Windows 7 or later."
    Abort
  ${EndIf}
  
  # Check if Python is installed
  ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\3.8\InstallPath" ""
  StrCmp $0 "" 0 python_found
  ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\3.9\InstallPath" ""
  StrCmp $0 "" 0 python_found
  ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\3.10\InstallPath" ""
  StrCmp $0 "" 0 python_found
  ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\3.11\InstallPath" ""
  StrCmp $0 "" 0 python_found
  
  MessageBox MB_YESNO|MB_ICONQUESTION "Python 3.8+ is required but not found. Do you want to continue anyway?$\r$\n$\r$\nNote: You will need to install Python manually for the application to work properly." IDYES python_found
  Abort
  
  python_found:
FunctionEnd

# Installation sections
Section "Trading Bot Pro (required)" SecMain
  SectionIn RO
  
  # Set output path to the installation directory
  SetOutPath "$INSTDIR"
  
  # Install main application files
  File /r "dist\*.*"
  
  # Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  # Create start menu shortcuts
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Trading Bot Pro.lnk" "$INSTDIR\TradingBotPro.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
  
  # Create desktop shortcut
  CreateShortCut "$DESKTOP\Trading Bot Pro.lnk" "$INSTDIR\TradingBotPro.exe"
  
  # Register application
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\TradingBotPro.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\TradingBotPro.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section "Backend Services" SecBackend
  SetOutPath "$INSTDIR\backend"
  File /r "..\backend\*.*"
  
  # Install Python dependencies
  DetailPrint "Installing Python dependencies..."
  ExecWait '"$INSTDIR\backend\install_dependencies.bat"' $0
  
  # Create backend service shortcut
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Start Backend Service.lnk" "$INSTDIR\backend\start_backend.bat"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "Web Dashboard" SecWebDash
  SetOutPath "$INSTDIR\web-dashboard"
  File /r "..\web-dashboard\dist\*.*"
  
  # Create web dashboard shortcut
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Web Dashboard.lnk" "http://localhost:5173"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "Demo License" SecDemo
  SetOutPath "$INSTDIR"
  File "..\ACTIVATE_DEMO_LICENSE.bat"
  File "..\demo_license_setup.py"
  
  # Create demo activation shortcut
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Activate Demo License.lnk" "$INSTDIR\ACTIVATE_DEMO_LICENSE.bat"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

# Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "Main application files (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecBackend} "Backend trading services and API"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecWebDash} "Web-based dashboard interface"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDemo} "Demo license activation tools"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

# Uninstaller section
Section Uninstall
  # Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  # Remove files and directories
  RMDir /r "$INSTDIR"
  
  # Remove shortcuts
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\$StartMenuFolder\Trading Bot Pro.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Start Backend Service.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Web Dashboard.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Activate Demo License.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  
  Delete "$DESKTOP\Trading Bot Pro.lnk"
  
  SetAutoClose true
SectionEnd

# Custom uninstaller function
Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd