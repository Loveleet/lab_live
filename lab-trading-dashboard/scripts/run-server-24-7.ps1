# Run server.js 24/7 — restarts on exit. Telegram alerts are sent by server.js itself.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir
Write-Host "Starting server.js 24/7 loop..."
while ($true) {
  node server/server.js
  $code = $LASTEXITCODE
  Write-Host "[run-server-24-7] server.js exited with code $code. Restarting in 5s..."
  Start-Sleep -Seconds 5
}
