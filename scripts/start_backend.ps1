$ErrorActionPreference='Continue'
foreach($n in 'JAVA_HOME'){ $v=[Environment]::GetEnvironmentVariable($n,'User'); if($v){ Set-Item ("env:"+$n) $v } }
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
Set-Location 'D:\dev\projects\taobao-analysis\backend'
& 'D:\dev\jdk17\bin\java.exe' -jar 'target\taobao-analysis-backend-1.0.0.jar' 2>&1 | Tee-Object -FilePath 'D:\dev\projects\taobao-analysis\outputs\backend_run.log'
