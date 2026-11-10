$ErrorActionPreference='Continue'
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
Set-Location 'D:\dev\projects\taobao-analysis\frontend'
& 'D:\dev\node\npm.cmd' run build 2>&1 | Tee-Object -FilePath 'D:\dev\projects\taobao-analysis\outputs\build_frontend.log'
if(Test-Path 'dist\index.html'){ Write-Output 'FRONTEND_BUILD=SUCCESS' } else { Write-Output 'FRONTEND_BUILD=FAILED' }
