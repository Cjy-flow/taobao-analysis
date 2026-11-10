# ============================================================
# 一键重跑数据分析全流程 01 -> 06(Spark) + 07(可视化)
# 前提：MySQL 已启动(scripts\start_mysql.ps1)，环境变量已配置
# 用法：powershell -ExecutionPolicy Bypass -File scripts\run_all_analysis.ps1
# ============================================================
$ErrorActionPreference = 'Stop'
$root = 'D:\dev\projects\taobao-analysis'
Set-Location $root

# 0) 确认 MySQL 端口
if(-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue).TcpTestSucceeded){
  Write-Host '[WARN] 3306 未监听，正在启动 MySQL ...' -ForegroundColor Yellow
  & "$root\scripts\start_mysql.ps1"
}

$sparkScripts = @(
  '01_load_clean.py',
  '02_behavior_stats.py',
  '03a_behavior_pattern.py',
  '03b_path_apriori.py',
  '04_rfm.py',
  '05_intent_xgboost.py',
  '06_als_recommend.py'
)
foreach($s in $sparkScripts){
  Write-Host "`n========== 运行 $s ==========" -ForegroundColor Cyan
  & "$root\scripts\run_spark.ps1" -Script $s
  $log = Join-Path $root ("outputs\" + $s.Replace('.py','.log'))
  if(Test-Path $log){
    $tail = Get-Content $log -Tail 3 | Out-String
    if($tail -notmatch 'DONE'){ Write-Host "[ERROR] $s 未正常结束，请查看 $log" -ForegroundColor Red; exit 1 }
  }
}

Write-Host "`n========== 运行 07_make_figures.py（生成图表） ==========" -ForegroundColor Cyan
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
& 'D:\dev\python38\python.exe' "$root\spark\07_make_figures.py"
if($LASTEXITCODE -ne 0){ Write-Host '[ERROR] 图表生成失败' -ForegroundColor Red; exit 1 }

Write-Host "`n[ALL DONE] 数据分析全流程完成：结果表见 MySQL taobao_behavior，CSV/JSON 见 outputs\tables，图见 outputs\figures" -ForegroundColor Green
