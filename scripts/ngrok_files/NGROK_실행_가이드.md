# ngrok 실행 가이드

## 실행 방법

### 방법 1: PowerShell에서 실행
```powershell
.\run_ngrok_now.bat
```

### 방법 2: PowerShell 스크립트 실행
```powershell
.\start_ngrok.ps1
```

### 방법 3: 직접 명령어 실행
```powershell
& "C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64 (1)\ngrok.exe" http 8002
```

### 방법 4: 통합 스크립트 실행 (권장) 
```powershell
.\start_server.ps1
```

## ngrok 실행 후 확인사항

ngrok이 성공적으로 실행되면 다음과 같은 화면이 표시됩니다:

```
Session Status                online
Account                       kkhwan1 (Plan: Free)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       xxx ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxxxx.ngrok-free.app -> http://localhost:8002
```

## 중요: URL 복사하기

`Forwarding` 줄에서 `https://xxxxxx.ngrok-free.app` 부분을 복사하세요.

## 메신저r.js 업데이트

복사한 URL을 메신저r.js 파일의 SERVER_URL에 붙여넣기:

```javascript
var SERVER_URL = 'https://xxxxxx.ngrok-free.app/api/kakaotalk';
```

## 문제 해결

### PowerShell 실행 정책 오류 시:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ngrok이 실행되지 않을 때:
1. 인증 토큰 확인
2. 포트 8002가 사용 중인지 확인
3. FastAPI 서버가 실행 중인지 확인