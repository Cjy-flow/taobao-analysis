$ErrorActionPreference='Continue'
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
Set-Location 'D:\dev\projects\taobao-analysis\frontend'
& 'D:\dev\node\npm.cmd' install --registry=https://registry.npmmirror.com 2>&1 | Tee-Object -FilePath 'D:\dev\projects\taobao-analysis\outputs\npm_install.log'
if(Test-Path 'node_modules'){ Write-Output 'NPM=SUCCESS' } else { Write-Output 'NPM=FAILED' }
