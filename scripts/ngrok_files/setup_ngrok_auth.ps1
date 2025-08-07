Write-Host "=== ngrok Authentication Setup ===" -ForegroundColor Green
Write-Host ""
Write-Host "ngrok 인증 토큰이 유효하지 않습니다." -ForegroundColor Yellow
Write-Host "올바른 인증 토큰을 설정하려면 다음 단계를 따라주세요:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. ngrok 대시보드에서 인증 토큰 확인:" -ForegroundColor Cyan
Write-Host "   https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
Write-Host ""
Write-Host "2. 인증 토큰 입력:" -ForegroundColor Cyan
$authToken = Read-Host "ngrok 인증 토큰을 입력하세요"

if ($authToken) {
    Write-Host ""
    Write-Host "인증 토큰 설정 중..." -ForegroundColor Yellow
    
    $ngrokPath = "C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64 (1)\ngrok.exe"
    
    try {
        # ngrok config 명령어 실행
        & $ngrokPath config add-authtoken $authToken
        
        Write-Host "인증 토큰이 성공적으로 설정되었습니다!" -ForegroundColor Green
        Write-Host ""
        Write-Host "이제 다음 명령어로 ngrok을 시작할 수 있습니다:" -ForegroundColor Yellow
        Write-Host ".\start_ngrok.ps1" -ForegroundColor Cyan
        Write-Host "또는"
        Write-Host ".\start_server.ps1" -ForegroundColor Cyan
        
    } catch {
        Write-Host "오류가 발생했습니다: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "인증 토큰이 입력되지 않았습니다." -ForegroundColor Red
}