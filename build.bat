@echo off
chcp 65001 > nul
echo ========================================
echo   StudyMate 打包脚本
echo ========================================
echo.

echo [1/3] 检查并安装 Electron...
echo.
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
npm install electron@29.3.0 --save-dev

if %ERRORLEVEL% NEQ 0 (
    echo Electron 安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo [2/3] 开始打包 Electron 应用...
echo.
npm run electron:build:win

if %ERRORLEVEL% NEQ 0 (
    echo 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo ========================================
echo   打包成功！
echo ========================================
echo.
echo 安装包位置: release\
echo.
dir release\*.exe
echo.
echo 按任意键退出...
pause > nul
