; Inno Setup script for TASS — Text Analysis for Social Scientists
; Build with:  iscc installer.iss
;
; Prerequisites:
;   1. Run: pyinstaller tass.spec  (produces dist\TASS\)
;   2. Install Inno Setup 6.x from https://jrsoftware.org/isinfo.php
;   3. Run: iscc installer.iss
;
; Output: installer\TASS-Setup-1.0.0.exe

#define AppName      "TASS"
#define AppFullName  "TASS — Text Analysis for Social Scientists"
#define AppVersion   "1.0.0"
#define AppPublisher "SIM DAD LLC"
#define AppURL       "https://simdadllc.com/tass"
#define AppExeName   "TASS.exe"
#define DistDir      "dist\TASS"
#define OutDir       "installer"

[Setup]
AppId={{B3F2A1E9-7C4D-4B8E-9A2F-1D6E3C5F8A07}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppFullName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/support
AppUpdatesURL={#AppURL}/updates
DefaultDirName={autopf}\TASS
DefaultGroupName={#AppFullName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoAfterFile=
OutputDir={#OutDir}
OutputBaseFilename=TASS-Setup-{#AppVersion}
SetupIconFile=assets\icons\tass_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
; Windows 10 2004+ required (for high-DPI + modern Qt6)

UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppFullName}

; Create uninstall entry
CreateUninstallRegKey=yes

; Associate .tass files
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application bundle (from PyInstaller onedir output)
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; License file
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppFullName}";        FileName: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";  FileName: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#AppFullName}";  FileName: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (Windows XP/Vista)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; FileName: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Registry]
; Register .tass file association
Root: HKA; Subkey: "Software\Classes\.tass";                    ValueType: string; ValueName: "";          ValueData: "TASSProject"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\TASSProject";              ValueType: string; ValueName: "";          ValueData: "TASS Project File"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\TASSProject\DefaultIcon";  ValueType: string; ValueName: "";          ValueData: "{app}\{#AppExeName},0"
Root: HKA; Subkey: "Software\Classes\TASSProject\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""

; Notify shell of file association change
Root: HKA; Subkey: "Software\Classes\.tass\OpenWithProgids";    ValueType: string; ValueName: "TASSProject"; ValueData: ""

; App registration for uninstall info
Root: HKA; Subkey: "Software\SIM DAD LLC\TASS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\SIM DAD LLC\TASS"; ValueType: string; ValueName: "Version";     ValueData: "{#AppVersion}"

[Run]
; Optional: open app after install
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppFullName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing special needed; registry keys are auto-cleaned via Flags: uninsdeletekey

[Code]
// -------------------------------------------------------------------
// Check for existing installation and warn if downgrading
// -------------------------------------------------------------------
function GetCurrentVersion(): String;
var
  Version: String;
begin
  if RegQueryStringValue(HKA, 'Software\SIM DAD LLC\TASS', 'Version', Version) then
    Result := Version
  else
    Result := '';
end;

function InitializeSetup(): Boolean;
var
  CurVersion: String;
  Msg: String;
begin
  Result := True;
  CurVersion := GetCurrentVersion();
  if (CurVersion <> '') and (CurVersion > '{#AppVersion}') then
  begin
    Msg := 'A newer version of TASS (' + CurVersion + ') is already installed.' + #13#10 +
           'Installing version {#AppVersion} will downgrade your installation.' + #13#10#13#10 +
           'Continue anyway?';
    Result := MsgBox(Msg, mbConfirmation, MB_YESNO) = IDYES;
  end;
end;
