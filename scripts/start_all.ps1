# ============================================================
# 一键启动整个系统：MySQL(便携) + Spring Boot 后端 + Vue 前端
# 用法：powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1
# 启动后浏览器访问 http://localhost:5173
# ============================================================
$root = 'D:\dev\projects\taobao-analysis'

# 1) MySQL（非系统服务，便携进程；已运行则跳过）
if(-not (Get-Process mysqld -ErrorAction SilentlyContinue)){
  Write-Host '[1/3] 启动 MySQL ...' -ForegroundColor Cyan
  Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$root\scripts\start_mysql.ps1`"" -WindowStyle Minimized
  Start-Sleep 8
}else{ Write-Host '[1/3] MySQL 已在运行' -ForegroundColor Green }

# 2) Spring Boot 后端（独立窗口常驻）
if(-not (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue)){
  Write-Host '[2/3] 启动 Spring Boot 后端(8080) ...' -ForegroundColor Cyan
  Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$root\scripts\start_backend.ps1`""
  Start-Sleep 14
}else{ Write-Host '[2/3] 后端 8080 已在运行' -ForegroundColor Green }

# 3) Vue 前端（独立窗口常驻）
if(-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)){
  Write-Host '[3/3] 启动 Vite 前端(5173) ...' -ForegroundColor Cyan
  Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$root\scripts\start_frontend.ps1`""
  Start-Sleep 6
}else{ Write-Host '[3/3] 前端 5173 已在运行' -ForegroundColor Green }

Write-Host "`n系统启动完成，请在浏览器访问： http://localhost:5173" -ForegroundColor Green
Write-Host '后端接口： http://localhost:8080/api/overview/metrics' -ForegroundColor Green
