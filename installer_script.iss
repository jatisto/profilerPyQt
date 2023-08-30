#define MyAppName "PgSSR"
#define MyAppExeName "PgSSR.exe"
#define ApplicationVersion GetVersionNumbersString('PgSSR.exe')

[Setup]
AppId = "3502D097-DF67-49DD-X98X-59F0866127QQ"
AppName={#MyAppName}
AppVerName={#MyAppName} {#ApplicationVersion}
VersionInfoVersion={#ApplicationVersion}
SetupIconFile=icons\icon.ico
DefaultDirName={commonpf64}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist
OutputBaseFilename={#MyAppName}
Compression=lzma
SolidCompression=yes
AppPublisher = "Εβγενθι ΐαδώψεβ"
AppCopyright = "Copyright © 2023 iam@eabdyushev@ru Eugene Abdyushev"

[Files]
Source: "build\*.*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName}"; Flags: nowait postinstall shellexec

[UninstallDelete]
Type: files; Name: "!{app}\settings.json"; 
Type: files; Name: "!{app}\auth.json";   