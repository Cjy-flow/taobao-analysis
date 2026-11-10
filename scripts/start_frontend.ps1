$ErrorActionPreference='Continue'
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
Set-Location 'D:\dev\projects\taobao-analysis\frontend'
& 'D:\dev\node\npm.cmd' run dev 2>&1 | Tee-Object -FilePath 'D:\dev\projects\taobao-analysis\outputs\frontend_run.log'
