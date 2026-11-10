@echo off
chcp 936 >nul
title 淘宝用户行为分析系统-停止
echo 正在停止后端、前端和 MySQL 数据库...
powershell -ExecutionPolicy Bypass -File "D:\dev\projects\taobao-analysis\scripts\stop_all.ps1" -StopMysql
echo.
echo 已全部停止。
pause
