@echo off
chcp 65001 >nul
REM ============================================================
REM  一键生成安装程序（需先安装 Inno Setup 6）
REM  下载：https://jrsoftware.org/isdl.php
REM
REM  流程：
REM   1) 用 PyInstaller 打包桌宠.exe（若 dist 已存在则跳过）
REM   2) 调用 Inno Setup 编译器生成安装程序
REM  产物：installer\桌宠安装程序.exe
REM ============================================================

setlocal

echo [1/3] 检查 Inno Setup 编译器...
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo [错误] 未找到 Inno Setup 编译器 ISCC.exe
    echo        请先安装 Inno Setup 6：https://jrsoftware.org/isdl.php
    echo        或手动将 ISCC.exe 所在目录加入 PATH。
    pause
    exit /b 1
)

echo [2/3] 检查/生成桌宠.exe...
if not exist "dist\桌宠.exe" (
    echo        未找到 dist\桌宠.exe，正在打包...
    python -m pip install --upgrade pyinstaller
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name 桌宠 main.py
    if errorlevel 1 (
        echo [错误] 打包失败！
        pause
        exit /b 1
    )
) else (
    echo        已存在 dist\桌宠.exe，跳过打包（如需更新请先删除或重新打包）。
)

echo [3/3] 生成安装程序...
"%ISCC%" installer.iss
if errorlevel 1 (
    echo [错误] 安装程序生成失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo  完成！安装程序位于：
echo  installer\桌宠安装程序.exe
echo ============================================
pause
endlocal