[Setup]
AppName=hAide
AppVersion=1.0
DefaultDirName={autopf}\hAide
DefaultGroupName=hAide
OutputDir=Output
OutputBaseFilename=hAide_Setup
Compression=lzma
SolidCompression=yes
DisableDirPage=no
DisableProgramGroupPage=no
AppId={{YOUR-GUID-HERE}}
AppPublisher=Indra Tang

[Files]
; 所有文件都安装到用户选择的目录
Source: "dist\haide.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "prompts\*"; DestDir: "{app}\prompts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "haide.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\hAide"; Filename: "{app}\haide.exe"; IconFilename: "{app}\haide.ico"
Name: "{group}\配置文件"; Filename: "{app}\config.py"
Name: "{group}\提示词目录"; Filename: "{app}\prompts"
Name: "{group}\卸载 hAide"; Filename: "{uninstallexe}"
Name: "{commondesktop}\hAide"; Filename: "{app}\haide.exe"; IconFilename: "{app}\haide.ico"

[Run]
Filename: "{app}\haide.exe"; Description: "立即运行 hAide"; Flags: postinstall nowait
