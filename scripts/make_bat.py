# -*- coding: utf-8 -*-
import os
ROOT = r'D:\dev\projects\taobao-analysis'

start = """@echo off
chcp 936 >nul
title 淘宝用户行为分析系统-启动
echo ================================================
echo    正在启动 淘宝用户购物行为大数据分析系统...
echo    依次启动: MySQL数据库 / 后端8080 / 前端5173
echo ================================================
powershell -ExecutionPolicy Bypass -File "%s\\scripts\\start_all.ps1"
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
""" % ROOT

stop = """@echo off
chcp 936 >nul
title 淘宝用户行为分析系统-停止
echo 正在停止后端、前端和 MySQL 数据库...
powershell -ExecutionPolicy Bypass -File "%s\\scripts\\stop_all.ps1" -StopMysql
echo.
echo 已全部停止。
pause
""" % ROOT

for t in [ROOT, r'C:\Users\admin\Desktop']:
    with open(os.path.join(t, '启动系统.bat'), 'wb') as f:
        f.write(start.encode('gbk'))
    with open(os.path.join(t, '停止系统.bat'), 'wb') as f:
        f.write(stop.encode('gbk'))
    print('written ->', t)
print('done')
