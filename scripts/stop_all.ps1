# ============================================================
# 一键停止系统：后端(8080)、前端(5173)。MySQL 默认保留运行；加 -StopMysql 一并停止
# 用法：powershell -ExecutionPolicy Bypass -File scripts\stop_all.ps1 [-StopMysql]
# ============================================================
param([switch]$StopMysql)
foreach($port in 8080,5173){
  $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if($c){ $c.OwningProcess | Select-Object -Unique | ForEach-Object {
    Write-Host ("停止端口 {0} 的进程 PID {1}" -f $port,$_)
    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
  }}
}
# vite/node 子进程
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like 'D:\dev\node*' } | Stop-Process -Force -ErrorAction SilentlyContinue
if($StopMysql){ Get-Process mysqld -ErrorAction SilentlyContinue | Stop-Process -Force; Write-Host 'MySQL 已停止' }
Write-Host '系统已停止（MySQL 保留运行，如需停止请加 -StopMysql）' -ForegroundColor Green
