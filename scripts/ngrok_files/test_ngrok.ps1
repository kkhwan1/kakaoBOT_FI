Write-Host "=== ngrok URL Test Script ===" -ForegroundColor Green

# ngrok URL 가져오기 또는 사용자 입력
$ngrokUrl = ""

# current_ngrok_url.txt 파일에서 URL 읽기 시도
if (Test-Path "current_ngrok_url.txt") {
    $ngrokUrl = Get-Content "current_ngrok_url.txt" -Raw -Encoding UTF8
    $ngrokUrl = $ngrokUrl.Trim()
    Write-Host "Found saved ngrok URL: $ngrokUrl" -ForegroundColor Green
} else {
    # 파일이 없으면 사용자에게 입력 요청
    Write-Host "Enter your ngrok URL (e.g., https://abc123.ngrok-free.app):" -ForegroundColor Yellow
    $ngrokUrl = Read-Host
}

if (-not $ngrokUrl) {
    Write-Host "No ngrok URL provided. Exiting." -ForegroundColor Red
    exit 1
}

# API 엔드포인트 구성
$apiUrl = "$ngrokUrl/api/kakaotalk"
Write-Host "`nTesting API endpoint: $apiUrl" -ForegroundColor Yellow

# 1. 서버 상태 확인
Write-Host "`n1. Checking server status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri $ngrokUrl -Method GET -ErrorAction Stop
    Write-Host "[OK] Server is online: $($response.message)" -ForegroundColor Green
    Write-Host "Version: $($response.version)" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Failed to connect to server: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Health check endpoint 테스트
Write-Host "`n2. Testing health check endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$ngrokUrl/health" -Method GET -ErrorAction Stop
    Write-Host "[OK] Health status: $($health.status)" -ForegroundColor Green
    Write-Host "Allowed rooms: $($health.allowed_rooms)" -ForegroundColor Cyan
} catch {
    Write-Host "[WARNING] Health endpoint not available" -ForegroundColor Yellow
}

# 3. 카카오톡 메시지 테스트
Write-Host "`n3. Testing KakaoTalk message endpoint..." -ForegroundColor Yellow

# 테스트 케이스들
$testCases = @(
    @{
        Name = "Greeting test"
        Body = @{
            room = "이국환"
            sender = "테스터"
            msg = "안녕하세요"
        }
    },
    @{
        Name = "Version command"
        Body = @{
            room = "이국환"
            sender = "테스터"
            msg = "!버전"
        }
    },
    @{
        Name = "Command list"
        Body = @{
            room = "이국환"
            sender = "테스터"
            msg = "!명령어"
        }
    }
)

foreach ($test in $testCases) {
    Write-Host "`nRunning: $($test.Name)" -ForegroundColor Yellow
    $jsonBody = $test.Body | ConvertTo-Json -Depth 10
    
    try {
        $headers = @{
            "Content-Type" = "application/json; charset=utf-8"
        }
        
        $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body $jsonBody -Headers $headers -ErrorAction Stop
        
        if ($response.is_reply) {
            Write-Host "[OK] Got response:" -ForegroundColor Green
            Write-Host "Reply to: $($response.reply_room)" -ForegroundColor Cyan
            Write-Host "Message: $($response.reply_msg)" -ForegroundColor White
        } else {
            Write-Host "[INFO] No response generated" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 4. 권한 없는 방 테스트
Write-Host "`n4. Testing unauthorized room (should not respond)..." -ForegroundColor Yellow
$unauthorizedTest = @{
    room = "테스트방"
    sender = "테스터"
    msg = "안녕하세요"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body $unauthorizedTest -Headers @{"Content-Type"="application/json"} -ErrorAction Stop
    
    if ($response.is_reply) {
        Write-Host "[WARNING] Unexpected response from unauthorized room!" -ForegroundColor Red
    } else {
        Write-Host "[OK] No response from unauthorized room (correct behavior)" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "`nTo use this ngrok URL in 메신저r.js, update:" -ForegroundColor Yellow
Write-Host "var SERVER_URL = '$apiUrl';" -ForegroundColor Cyan