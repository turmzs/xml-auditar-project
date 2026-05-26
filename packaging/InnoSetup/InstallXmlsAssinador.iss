; Inno Setup script for distributing the PyInstaller folder-based build
; Compile with: Inno Setup Compiler

#define AppName "Assinador de XMLs"
#define AppPublisher "Auditar Contabilidade"
#define AppVersion "1.0.0"
#define ExeName "xmls_gui_app.exe"

[Setup]
AppId={{7C4C3E1C-4A5B-4E2B-9D2B-000000000001}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={pf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=dist_inno
OutputBaseFilename=Setup-{#AppName}
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Files]
; Copy everything produced by PyInstaller:
; Expected layout after build:
;   dist/xmls_gui_app/xmls_gui_app.exe
;   dist/xmls_gui_app/* (other files)
Source: "..\..\dist\xmls_gui_app\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; Add license file
Source: "..\..\LICENCE.txt"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"

[Run]
Filename: "{app}\{#ExeName}"; Description: "{#AppName}"; Flags: nowait postinstall skipifsilent

[Notes]
; PKCS#11 drivers/DLL for A3 (token) are provided by the user at runtime.
; The app will ask the user to select the driver DLL.
