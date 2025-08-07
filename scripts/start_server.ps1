Write-Host "=== STORIUM Bot Server + ngrok Launcher ===" -ForegroundColor Green
Write-Host ""

# 경로 설정
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ngrokPath = "C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64 (1)\ngrok.exe"

# Python 확인
try {
    $pythonPath = Get-Command python -ErrorAction Stop
    Write-Host "[OK] Python found at: $($pythonPath.Source)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# ngrok 확인
if (Test-Path $ngrokPath) {
    Write-Host "[OK] ngrok found at: $ngrokPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] ngrok not found at: $ngrokPath" -ForegroundColor Red
    exit 1
}

# 1. FastAPI 서버를 백그라운드에서 시작
Write-Host "`nStarting FastAPI server in background..." -ForegroundColor Yellow
$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:scriptPath
    python main.py
}

# 서버가 시작될 때까지 잠시 대기
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 서버 상태 확인
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002" -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] FastAPI server is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] FastAPI server failed to start" -ForegroundColor Red
    Write-Host "Check server logs:" -ForegroundColor Yellow
    Receive-Job $serverJob
    Stop-Job $serverJob
    Remove-Job $serverJob
    exit 1
}

# 2. ngrok 터널 시작
Write-Host "`nStarting ngrok tunnel..." -ForegroundColor Yellow
$ngrokJob = Start-Job -ScriptBlock {
    & $using:ngrokPath http 8002 --log=stdout
}

# ngrok이 시작될 때까지 대기
Start-Sleep -Seconds 5

# 3. ngrok URL 가져오기
Write-Host "`nGetting ngrok URL..." -ForegroundColor Yellow
try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
    $publicUrl = $tunnels.tunnels[0].public_url
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  STORIUM Bot is ready!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Local URL: http://localhost:8002" -ForegroundColor White
    Write-Host "  Public URL: $publicUrl" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Update 메신저r.js with this URL:" -ForegroundColor Yellow
    Write-Host "$publicUrl/api/kakaotalk" -ForegroundColor Green
    Write-Host ""
    
    # URL을 파일로 저장 (자동화를 위해)
    $publicUrl | Out-File -FilePath "$scriptPath\current_ngrok_url.txt" -Encoding UTF8
    
} catch {
    Write-Host "[ERROR] Failed to get ngrok URL. Make sure ngrok is running." -ForegroundColor Red
}

Write-Host "Press Ctrl+C to stop both server and ngrok" -ForegroundColor Yellow
Write-Host ""

# 로그 모니터링
Write-Host "=== Server Logs ===" -ForegroundColor Yellow
try {
    while ($true) {
        # 서버 로그 표시
        Receive-Job $serverJob -Keep | Where-Object { $_ } | ForEach-Object {
            Write-Host "[Server] $_" -ForegroundColor Gray
        }
        
        # ngrok 로그 표시 (선택적)
        # Receive-Job $ngrokJob -Keep | Where-Object { $_ } | ForEach-Object {
        #     Write-Host "[ngrok] $_" -ForegroundColor DarkGray
        # }
        
        Start-Sleep -Milliseconds 500
    }
} finally {
    # 정리
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    Stop-Job $serverJob
    Stop-Job $ngrokJob
    Remove-Job $serverJob
    Remove-Job $ngrokJob
    Write-Host "[OK] All services stopped" -ForegroundColor Green
}