@echo off
chcp 65001 >nul
REM ============================================================
REM  桌宠程序打包脚本（需先安装 PyInstaller）
REM  首次使用请执行： pip install pyinstaller
REM ============================================================

echo [1/3] 安装/更新 PyInstaller...
python -m pip install --upgrade pyinstaller

echo [2/3] 开始打包（单文件、无控制台窗口）...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name 桌宠 main.py

echo [3/3] 打包完成！
echo 可执行文件位于： dist\桌宠.exe
echo 将 dist\桌宠.exe 复制到任意目录即可运行，config.json 会生成在 exe 同目录。
pause