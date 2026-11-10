@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
title 淘宝用户购物行为分析系统 - 一键启动

REM ============ 本机实际环境路径 ============
set "ROOT=D:\Program Files\taobao-analysis"
set "JAVA=D:\Program Files\bin\java.exe"
set "JAR=%ROOT%\backend\target\taobao-analysis-backend-1.0.0.jar"
set "NODE=D:\Program Files\nodejs\node.exe"
set "NPM=D:\Program Files\nodejs\npm.cmd"
set "FRONT=%ROOT%\frontend"
set "MYSQL_SVC=MySQL84"

echo ================================================================
echo    淘宝用户购物行为大数据分析系统 - 一键启动
echo    MySQL 3306 / 后端 8080 / 前端 5173
echo ================================================================
echo.

REM ---------- 0. 关键文件检查 ----------
if not exist "%JAVA%" ( echo [错误] 找不到 Java: %JAVA% & goto :fail )
if not exist "%JAR%"  ( echo [错误] 找不到后端 jar 包: %JAR% & goto :fail )
if not exist "%NODE%" ( echo [错误] 找不到 Node: %NODE% & goto :fail )

REM ---------- 1. MySQL ----------
echo [1/4] 检查 MySQL 数据库 (3306) ...
call :check_port 3306
if "!PORT_UP!"=="1" (
    echo       MySQL 已在运行。
) else (
    echo       MySQL 未运行，正在尝试启动服务 %MYSQL_SVC% ...
    net start %MYSQL_SVC%
    call :wait_port 3306 30
    if "!PORT_UP!"=="0" (
        echo [错误] MySQL 启动失败：请右键本脚本“以管理员身份运行”，或手动启动 MySQL。
        goto :fail
    )
)
echo.

REM ---------- 2. 后端 ----------
echo [2/4] 检查 Spring Boot 后端 (8080) ...
call :check_port 8080
if "!PORT_UP!"=="1" (
    echo       后端 8080 已在运行，跳过。
) else (
    echo       正在新窗口启动后端服务 ...
    set "SPRING_DATASOURCE_URL=jdbc:mysql://localhost:3306/taobao_analysis?useSSL=false&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"
    set "SPRING_DATASOURCE_PASSWORD=CHANGE_ME"
    start "后端服务-8080" cmd /k ""%JAVA%" -jar "%JAR%""
    call :wait_port 8080 60
    if "!PORT_UP!"=="0" ( echo [警告] 后端 60 秒内未就绪，请查看“后端服务-8080”窗口日志。 ) else ( echo       后端已就绪。 )
)
echo.

REM ---------- 3. 前端 ----------
echo [3/4] 检查 Vite 前端 (5173) ...
call :check_port 5173
if "!PORT_UP!"=="1" (
    echo       前端 5173 已在运行，跳过。
) else (
    if not exist "%FRONT%\node_modules" (
        echo       首次运行，正在安装前端依赖（仅需一次，请耐心等待）...
        pushd "%FRONT%"
        call "%NPM%" install
        popd
    )
    echo       正在新窗口启动前端服务 ...
    start "前端服务-5173" /d "%FRONT%" cmd /k ""%NODE%" node_modules\vite\bin\vite.js"
    call :wait_port 5173 40
    if "!PORT_UP!"=="0" ( echo [警告] 前端 40 秒内未就绪，请查看“前端服务-5173”窗口日志。 ) else ( echo       前端已就绪。 )
)
echo.

REM ---------- 4. 打开浏览器 ----------
echo [4/4] 正在打开浏览器 ...
start "" http://localhost:5173
echo.
echo ================================================================
echo    启动完成！
echo    系统页面 : http://localhost:5173
echo    后端接口 : http://localhost:8080/api/overview/metrics
echo.
echo    注意：弹出的“后端服务-8080”“前端服务-5173”两个窗口
echo    请勿关闭，关闭窗口即停止对应服务。
echo ================================================================
echo.
pause
exit /b 0

:fail
echo.
echo 启动未完成，请根据上面的错误提示处理后重试。
pause
exit /b 1

REM ============ 子程序：端口检测 ============
:check_port
set "PORT_UP=0"
netstat -ano -p tcp | findstr "LISTENING" | findstr ":%~1 " >nul 2>&1 && set "PORT_UP=1"
goto :eof

:wait_port
set /a "_n=0"
:wp_loop
call :check_port %1
if "!PORT_UP!"=="1" goto :eof
set /a "_n+=1"
if !_n! geq %2 goto :eof
ping -n 2 127.0.0.1 >nul
goto wp_loop
