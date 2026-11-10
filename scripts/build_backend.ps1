$ErrorActionPreference='Continue'
foreach($n in 'JAVA_HOME','MAVEN_HOME'){
  $v=[Environment]::GetEnvironmentVariable($n,'User'); if($v){ Set-Item ("env:"+$n) $v }
}
$env:Path=([Environment]::GetEnvironmentVariable('Path','Machine')).TrimEnd(';')+';'+([Environment]::GetEnvironmentVariable('Path','User')).TrimEnd(';')
$env:JAVA_TOOL_OPTIONS='-Dfile.encoding=UTF-8'
Set-Location 'D:\dev\projects\taobao-analysis\backend'
& 'D:\dev\maven\bin\mvn.cmd' clean package -DskipTests -B 2>&1 | Tee-Object -FilePath 'D:\dev\projects\taobao-analysis\outputs\build_backend.log'
if(Test-Path 'target\taobao-analysis-backend-1.0.0.jar'){ Write-Output 'BUILD=SUCCESS' } else { Write-Output 'BUILD=FAILED' }
