Write-Host "=== STORIUM Bot ngrok Tunnel Starter ===" -ForegroundColor Green
Write-Host ""

# ngrok 경로 설정
$ngrokPath = "C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64 (1)\ngrok.exe"

# ngrok 설치 확인
if (Test-Path $ngrokPath) {
    Write-Host "[OK] ngrok found at: $ngrokPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] ngrok not found at expected path: $ngrokPath" -ForegroundColor Red
    # 시스템 PATH에서도 확인
    try {
        $ngrokPath = (Get-Command ngrok -ErrorAction Stop).Source
        Write-Host "[OK] ngrok found in PATH: $ngrokPath" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] ngrok not found. Please check installation." -ForegroundColor Red
        exit 1
    }
}

# ngrok 인증 확인
Write-Host "`nChecking ngrok authentication..." -ForegroundColor Yellow
$authCheck = & $ngrokPath config check 2>&1
if ($authCheck -match "Valid") {
    Write-Host "[OK] ngrok is authenticated" -ForegroundColor Green
} else {
    Write-Host "[WARNING] ngrok may not be authenticated" -ForegroundColor Yellow
    Write-Host "Run: $ngrokPath config add-authtoken YOUR_AUTH_TOKEN" -ForegroundColor Yellow
}

# 포트 8002로 HTTP 터널 시작
Write-Host "`nStarting ngrok tunnel on port 8002..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the tunnel" -ForegroundColor Yellow
Write-Host ""

# ngrok 실행
& $ngrokPath http 8002

# 종료 메시지
Write-Host "`n[INFO] ngrok tunnel closed" -ForegroundColor Yellow