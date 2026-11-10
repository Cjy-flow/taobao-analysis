param([Parameter(Mandatory=$true)][string]$Script)
$ErrorActionPreference='Continue'
foreach($n in 'JAVA_HOME','SPARK_HOME','HADOOP_HOME','MAVEN_HOME','PYSPARK_PYTHON','PYSPARK_DRIVER_PYTHON'){
  $v=[Environment]::GetEnvironmentVariable($n,'User'); if($v){ Set-Item ("env:"+$n) $v }
}
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
$env:PYTHONIOENCODING='utf-8'
$sparkDir='D:\dev\projects\taobao-analysis\spark'
Set-Location $sparkDir
$outDir='D:\dev\projects\taobao-analysis\outputs'
$logName = ($Script -replace '\.py$','') + '.log'
$log = Join-Path $outDir $logName
if(Test-Path $log){ Remove-Item $log -Force }
Write-Output ('running '+$Script+' ...')
& 'D:\dev\python38\python.exe' (Join-Path $sparkDir $Script) *> $log
$noise = 'Failed to delete|deleteRecursively|ShutdownHookManager|Exception while deleting|^\s*at [a-z]|java\.io\.IOException|NativeCommandError|CategoryInfo|FullyQualifiedErrorId|^\s*~|WindowExec: No Partition'
Get-Content $log | Where-Object { $_ -notmatch $noise } | ForEach-Object { Write-Output $_ }
if(Select-String -Path $log -Pattern 'DONE' -Quiet){ Write-Output 'RESULT=SUCCESS' } else { Write-Output 'RESULT=FAILED' }
