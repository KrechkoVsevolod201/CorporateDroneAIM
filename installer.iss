; Inno Setup Script for CorporateDroneAIM
; Download Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "CorporateDroneAIM"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KrechkoVsevolod201"
#define MyAppURL "https://github.com/KrechkoVsevolod201/CorporateDroneAIM"
#define MyAppExeName "CorporateDroneAIM.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=CorporateDroneAIM_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=assets\icon\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\CorporateDroneAIM.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "sounds\shot\*"; DestDir: "{app}\sounds\shot"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "sounds\shell\*"; DestDir: "{app}\sounds\shell"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\weapons\*"; DestDir: "{app}\assets\weapons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\gloves\*"; DestDir: "{app}\assets\gloves"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
