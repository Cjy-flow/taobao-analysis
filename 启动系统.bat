@echo off
chcp 936 >nul
title 淘宝用户行为分析系统-启动
echo ================================================
echo    正在启动 淘宝用户购物行为大数据分析系统...
echo    依次启动: MySQL数据库 / 后端8080 / 前端5173
echo ================================================
powershell -ExecutionPolicy Bypass -File "D:\dev\projects\taobao-analysis\scripts\start_all.ps1"
echo.
echo    正在打开浏览器, 请稍候...
timeout /t 2 >nul
start "" http://localhost:5173
echo.
echo    ============== 启动完成 ==============
echo    系统页面: http://localhost:5173
echo    注意: 弹出的后端/前端黑色窗口请勿关闭, 关闭即停止服务
echo    要停止系统请双击 [停止系统.bat]
echo ================================================
pause
