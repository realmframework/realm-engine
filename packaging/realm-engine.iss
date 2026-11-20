; Inno Setup installer script for REALM Engine (Windows 10/11 64-bit, per-user install — no Admin required)
#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif

[Setup]
AppId={{8D6B2A1E-5B44-4E83-918C-3E8D9B5A4C10}
AppName=REALM Engine
AppVersion={#AppVersion}
AppPublisher=REALM Framework
AppPublisherURL=https://github.com/realmframework/realm-engine
AppSupportURL=https://github.com/realmframework/realm-engine/issues
DefaultDirName={autopf}\REALM Engine
DefaultGroupName=REALM Engine
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=REALM-Engine-{#AppVersion}-windows-x64-setup
SetupIconFile=..\features\ui\static\favicon.ico
UninstallDisplayIcon={app}\REALM Engine.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\REALM Engine\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\REALM Engine"; Filename: "{app}\REALM Engine.exe"
Name: "{autodesktop}\REALM Engine"; Filename: "{app}\REALM Engine.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\REALM Engine.exe"; Description: "{cm:LaunchProgram,REALM Engine}"; Flags: nowait postinstall skipifsilent
