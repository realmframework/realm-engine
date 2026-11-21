; Inno Setup installer script for REALM Engine (Windows 10/11 64-bit, per-user install — no Admin required)
#ifndef AppVersion
  #define AppVersion "0.4.0"
#endif

[Setup]
AppId={{8D6B2A1E-5B44-4E83-918C-3E8D9B5A4C10}
AppName=REALM Engine
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}
AppPublisher=REALM Framework
AppCopyright=Copyright (c) 2026 Luis Godoy Alvarez (MIT License)
AppPublisherURL=https://github.com/realmframework/realm-engine
AppSupportURL=https://github.com/realmframework/realm-engine/issues
LicenseFile=..\LICENSE
AppMutex=REALMEngineSingleInstanceMutex
DefaultDirName={autopf}\REALM Engine
DefaultGroupName=REALM Engine
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=REALM-Engine-{#AppVersion}-windows-x64-setup
#if FileExists("..\packaging\icons\realm-engine.ico")
SetupIconFile=..\packaging\icons\realm-engine.ico
#else
SetupIconFile=..\features\ui\static\favicon.ico
#endif
UninstallDisplayIcon={app}\REALM Engine.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\REALM Engine\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\REALM Engine"; Filename: "{app}\REALM Engine.exe"
Name: "{autodesktop}\REALM Engine"; Filename: "{app}\REALM Engine.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\REALM Engine.exe"; Description: "{cm:LaunchProgram,REALM Engine}"; Flags: nowait postinstall skipifsilent

[Code]
function HasWebView2(): Boolean;
var
  Ver: String;
begin
  Result :=
    (RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Ver) and (Ver <> '') and (Ver <> '0.0.0.0')) or
    (RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Ver) and (Ver <> '') and (Ver <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Ver) and (Ver <> '') and (Ver <> '0.0.0.0'));
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not HasWebView2() and not WizardSilent() then
  begin
    MsgBox('Microsoft Edge WebView2 Runtime was not detected. REALM Engine will still work by opening cleanly in your default browser, or you can install WebView2 from Microsoft for the embedded desktop window.', mbInformation, MB_OK);
  end;
end;
