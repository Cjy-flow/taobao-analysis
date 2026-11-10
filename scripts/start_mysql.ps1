$mysql='D:\dev\mysql'
# start mysqld as a background process (no Windows service -> no admin needed)
$running = Get-Process mysqld -ErrorAction SilentlyContinue
if(-not $running){
  Start-Process -FilePath (Join-Path $mysql 'bin\mysqld.exe') -ArgumentList '--defaults-file=D:\dev\mysql\my.ini','--console' -WindowStyle Hidden
  Write-Output 'mysqld starting ...'
} else { Write-Output 'mysqld already running' }
# wait for port 3306
$ok=$false
for($i=0;$i -lt 40;$i++){
  Start-Sleep -Milliseconds 1000
  $t = Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue
  if($t.TcpTestSucceeded){ $ok=$true; Write-Output ('MySQL is up after '+$i+'s'); break }
}
if(-not $ok){ Write-Output 'MYSQL DID NOT COME UP'; exit 1 }
# set password + create db (first login uses empty password)
$sql = "ALTER USER 'root'@'localhost' IDENTIFIED BY 'CHANGE_ME'; CREATE DATABASE IF NOT EXISTS taobao_behavior CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci; FLUSH PRIVILEGES;"
& (Join-Path $mysql 'bin\mysql.exe') -u root --connect-expired-password -e $sql
Write-Output '--- verify with new password ---'
& (Join-Path $mysql 'bin\mysql.exe') -u root -pCHANGE_ME -e "SHOW DATABASES; SELECT VERSION();"
