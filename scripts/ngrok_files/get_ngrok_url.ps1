# ngrok URL 가져오기 스크립트
Write-Host "Getting ngrok URL..." -ForegroundColor Yellow

try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
    $publicUrl = $tunnels.tunnels[0].public_url
    
    Write-Host "`nngrok URL found:" -ForegroundColor Green
    Write-Host $publicUrl -ForegroundColor Cyan
    Write-Host "`nFull API endpoint:" -ForegroundColor Green
    Write-Host "$publicUrl/api/kakaotalk" -ForegroundColor Cyan
    
    # URL을 파일로 저장
    $publicUrl | Out-File -FilePath "current_ngrok_url.txt" -Encoding UTF8
    Write-Host "`nURL saved to: current_ngrok_url.txt" -ForegroundColor Green
    
    # 클립보드에 복사 (선택사항)
    "$publicUrl/api/kakaotalk" | Set-Clipboard
    Write-Host "API endpoint copied to clipboard!" -ForegroundColor Green
    
} catch {
    Write-Host "[ERROR] Failed to get ngrok URL." -ForegroundColor Red
    Write-Host "Make sure ngrok is running on port 8002" -ForegroundColor Yellow
    Write-Host "Run: .\start_ngrok.ps1" -ForegroundColor Yellow
}