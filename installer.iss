; ============================================================
; 桌宠程序 - Inno Setup 安装脚本
; 使用前请先安装 Inno Setup 6（https://jrsoftware.org/isdl.php）
; 生成安装包：
;   1) 先执行 build_exe.bat 或手动打包得到 dist\桌宠.exe
;   2) 编译本脚本：命令行执行  ISCC.exe installer.iss
;      （或打开 Inno Setup 编译器拖入本文件）
; 产物：installer\桌宠安装程序.exe
; ============================================================

#define MyAppName "桌宠"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "桌宠工作室"
#define MyAppExeName "桌宠.exe"

[Setup]
; 应用标识（每个应用唯一，不要随意改动以免升级识别失败）
AppId={{8E6A2F1C-9B5D-4E2A-A1B3-6C7D8E9F0A1B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 安装包输出目录与文件名
OutputDir=installer
OutputBaseFilename=桌宠安装程序
Compression=lzma2
SolidCompression=yes
; 权限：普通用户即可安装（写入当前用户目录）
PrivilegesRequired=lowest
; 界面语言（简体中文）
ShowLanguageDialog=no
; 安装时关闭正在运行的程序
CloseApplications=yes
; 不允许旧版降级覆盖
DirExistsWarning=no

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式(&D)"; GroupDescription: "附加任务："
Name: "startup"; Description: "开机自动启动(&S)"; GroupDescription: "附加任务："

[Files]
; 打包 exe 为安装内容
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 默认桌宠图片（与 exe 放同目录，供相对路径 dagou.png 引用）
Source: "dagou.png"; DestDir: "{app}"; Flags: ignoreversion
; 默认音效（与 exe 放同目录，供相对路径 dagoujiao.MP3 引用）
Source: "dagoujiao.MP3"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; 卸载快捷方式
Name: "{group}\卸载{#MyAppName}"; Filename: "{uninstallexe}"
; 桌面快捷方式（按用户勾选）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 安装完成后运行程序
Filename: "{app}\{#MyAppExeName}"; Description: "立即运行 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; 开机自启动（按用户勾选，写入当前用户注册表）
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup