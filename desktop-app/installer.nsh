; NSIS Installer Script for Trading Bot Desktop
; This script customizes the Windows installer

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Custom installer pages and functions

; Check if .NET Framework is installed
Function CheckDotNet
    ; Check for .NET Framework 4.7.2 or later
    ReadRegDWORD $0 HKLM "SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" "Release"
    IntCmp $0 461808 DotNetOK DotNetMissing DotNetOK
    
    DotNetMissing:
        MessageBox MB_YESNO|MB_ICONQUESTION \
            "Trading Bot Desktop requires .NET Framework 4.7.2 or later.$\n$\nWould you like to download and install it now?" \
            IDYES DownloadDotNet IDNO SkipDotNet
        
    DownloadDotNet:
        ExecShell "open" "https://dotnet.microsoft.com/download/dotnet-framework"
        MessageBox MB_OK "Please install .NET Framework and run this installer again."
        Quit
        
    SkipDotNet:
        MessageBox MB_OK "Warning: Trading Bot Desktop may not work properly without .NET Framework 4.7.2 or later."
        
    DotNetOK:
FunctionEnd

; Check available disk space
Function CheckDiskSpace
    ${GetRoot} "$INSTDIR" $0
    ${DriveSpace} "$0" "/D=F /S=M" $1
    
    ; Check if we have at least 500MB free space
    IntCmp $1 500 SpaceOK SpaceOK InsufficientSpace
    
    InsufficientSpace:
        MessageBox MB_OK|MB_ICONSTOP \
            "Insufficient disk space. Trading Bot Desktop requires at least 500MB of free space.$\n$\nAvailable space: $1 MB"
        Quit
        
    SpaceOK:
FunctionEnd

; Create application shortcuts
Function CreateShortcuts
    ; Desktop shortcut
    CreateShortCut "$DESKTOP\Trading Bot Desktop.lnk" "$INSTDIR\Trading Bot Desktop.exe" \
        "" "$INSTDIR\Trading Bot Desktop.exe" 0 SW_SHOWNORMAL \
        ALT|CONTROL|SHIFT|F1 "Professional Trading Bot Desktop Application"
    
    ; Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\Trading Bot Desktop"
    CreateShortCut "$SMPROGRAMS\Trading Bot Desktop\Trading Bot Desktop.lnk" \
        "$INSTDIR\Trading Bot Desktop.exe" "" "$INSTDIR\Trading Bot Desktop.exe" 0
    CreateShortCut "$SMPROGRAMS\Trading Bot Desktop\Uninstall.lnk" \
        "$INSTDIR\Uninstall Trading Bot Desktop.exe"
    
    ; Quick Launch shortcut (if Quick Launch exists)
    IfFileExists "$QUICKLAUNCH" 0 NoQuickLaunch
        CreateShortCut "$QUICKLAUNCH\Trading Bot Desktop.lnk" "$INSTDIR\Trading Bot Desktop.exe"
    NoQuickLaunch:
FunctionEnd

; Register URL protocol handler
Function RegisterProtocol
    WriteRegStr HKCR "trading-bot" "" "URL:Trading Bot Protocol"
    WriteRegStr HKCR "trading-bot" "URL Protocol" ""
    WriteRegStr HKCR "trading-bot\DefaultIcon" "" "$INSTDIR\Trading Bot Desktop.exe,0"
    WriteRegStr HKCR "trading-bot\shell\open\command" "" '"$INSTDIR\Trading Bot Desktop.exe" "%1"'
FunctionEnd

; Set up auto-start (optional)
Function SetupAutoStart
    ; Ask user if they want the app to start with Windows
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Would you like Trading Bot Desktop to start automatically when Windows starts?" \
        IDYES EnableAutoStart IDNO SkipAutoStart
    
    EnableAutoStart:
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" \
            "TradingBotDesktop" '"$INSTDIR\Trading Bot Desktop.exe" --minimized'
        Goto AutoStartDone
        
    SkipAutoStart:
        ; Remove any existing auto-start entry
        DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TradingBotDesktop"
        
    AutoStartDone:
FunctionEnd

; Custom installer initialization
Function .onInit
    ; Check system requirements
    Call CheckDotNet
    Call CheckDiskSpace
    
    ; Set default installation directory based on architecture
    ${If} ${RunningX64}
        StrCpy $INSTDIR "$PROGRAMFILES64\Trading Bot Desktop"
    ${Else}
        StrCpy $INSTDIR "$PROGRAMFILES32\Trading Bot Desktop"
    ${EndIf}
FunctionEnd

; Custom post-installation actions
Function .onInstSuccess
    Call CreateShortcuts
    Call RegisterProtocol
    Call SetupAutoStart
    
    ; Create application data directory
    CreateDirectory "$APPDATA\Trading Bot Desktop"
    
    ; Set up Windows Firewall exception
    ExecWait '"$SYSDIR\netsh.exe" advfirewall firewall add rule name="Trading Bot Desktop" dir=in action=allow program="$INSTDIR\Trading Bot Desktop.exe" enable=yes'
    
    ; Show completion message
    MessageBox MB_OK|MB_ICONINFORMATION \
        "Trading Bot Desktop has been successfully installed!$\n$\nYou can now launch it from the Start Menu or Desktop shortcut."
FunctionEnd

; Custom uninstaller actions
Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Are you sure you want to completely remove Trading Bot Desktop and all of its components?" \
        IDYES UninstallOK IDNO UninstallCancel
    
    UninstallCancel:
        Quit
        
    UninstallOK:
FunctionEnd

; Custom uninstaller completion
Function un.onUninstSuccess
    ; Remove shortcuts
    Delete "$DESKTOP\Trading Bot Desktop.lnk"
    Delete "$QUICKLAUNCH\Trading Bot Desktop.lnk"
    RMDir /r "$SMPROGRAMS\Trading Bot Desktop"
    
    ; Remove registry entries
    DeleteRegKey HKCR "trading-bot"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TradingBotDesktop"
    
    ; Remove Windows Firewall exception
    ExecWait '"$SYSDIR\netsh.exe" advfirewall firewall delete rule name="Trading Bot Desktop"'
    
    ; Ask about user data
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Do you want to remove all user data and settings?$\n$\nThis includes trading configurations, logs, and cached data." \
        IDYES RemoveUserData IDNO KeepUserData
    
    RemoveUserData:
        RMDir /r "$APPDATA\Trading Bot Desktop"
        RMDir /r "$LOCALAPPDATA\Trading Bot Desktop"
        Goto UninstallComplete
        
    KeepUserData:
        MessageBox MB_OK|MB_ICONINFORMATION \
            "User data has been preserved in:$\n$APPDATA\Trading Bot Desktop"
        
    UninstallComplete:
        MessageBox MB_OK|MB_ICONINFORMATION "Trading Bot Desktop has been successfully removed from your computer."
FunctionEnd