# STORIUM Bot ngrok 설정 가이드

## 📋 개요
포트포워딩 없이 ngrok을 사용하여 카카오톡 봇 서버를 외부에서 접속 가능하게 만듭니다.

### ngrok 무료 플랜 제한사항
- **인증된 계정 (authtoken 사용)**: 세션 시간 제한 없음 ✅
- **익명 사용**: 2시간 세션 제한
- **기타 제한**: 
  - 월 대역폭 제한
  - 분당 40개 연결 제한
  - 브라우저 트래픽에 경고 페이지 표시
  - 상업적 사용 불가

## 🚀 빠른 시작

### 1. ngrok 설치
- 이미 설치됨: `C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64 (1)\ngrok.exe`
- 추가 설치 필요시: https://ngrok.com/download

### 2. ngrok 인증 (최초 1회)
```powershell
# ngrok 계정 생성 후 인증 토큰 설정
"C:\Users\USER\Downloads\ngrok-v3-stable-windows-amd64 (1)\ngrok.exe" config add-authtoken YOUR_AUTH_TOKEN
```

### 3. 서버 실행 (통합 스크립트)
```powershell
# 프로젝트 폴더에서 실행
.\start_server.ps1
```

이 스크립트는:
- FastAPI 서버를 백그라운드에서 시작
- ngrok 터널을 자동으로 생성
- ngrok URL을 화면에 표시
- 서버 로그를 실시간으로 모니터링

### 4. 메신저r.js 업데이트
start_server.ps1 실행 후 표시되는 URL을 복사하여 메신저r.js 파일의 상단에 있는 SERVER_URL을 수정:

```javascript
// 예시
var SERVER_URL = 'https://abc123.ngrok-free.app/api/kakaotalk';
```

## 📁 파일 설명

### 실행 스크립트
- **start_server.ps1**: FastAPI + ngrok 통합 실행 (권장)
- **start_ngrok.ps1**: ngrok만 단독 실행
- **get_ngrok_url.ps1**: 실행 중인 ngrok의 URL 확인

### 테스트 스크립트
- **test_ngrok.ps1**: ngrok URL로 API 테스트
- **test_server.ps1**: localhost로 로컬 테스트

### 설정 파일
- **main.py**: FastAPI 서버 (CORS 및 로깅 개선됨)
- **메신저r.js**: 카카오톡 봇 스크립트 (ngrok URL 사용)

## 🔧 개별 실행 방법

### 서버와 ngrok 별도 실행
```powershell
# 터미널 1: FastAPI 서버 실행
python main.py

# 터미널 2: ngrok 터널 실행
.\start_ngrok.ps1

# 터미널 3: ngrok URL 확인
.\get_ngrok_url.ps1
```

## 📊 테스트

### API 테스트
```powershell
# ngrok URL로 테스트
.\test_ngrok.ps1

# 로컬 테스트
.\test_server.ps1
```

## ⚠️ 주의사항

1. **무료 ngrok 제한사항**
   - 세션당 최대 2시간 (재시작 필요)
   - 동시 터널 1개만 가능
   - 랜덤 URL (고정 도메인은 유료)

2. **고정 도메인 사용 (권장)**
   - ngrok 대시보드에서 무료 고정 도메인 생성 가능
   - start_ngrok.ps1에서 `ngrok http --domain=your-domain.ngrok-free.app 8002` 사용

3. **보안**
   - ngrok URL은 공개되므로 적절한 인증 필요
   - ALLOWED_ROOMS 설정으로 접근 제한 중

## 🛠️ 문제 해결

### ngrok이 시작되지 않을 때
```powershell
# ngrok 프로세스 확인
Get-Process | Where-Object {$_.Name -like "*ngrok*"}

# 기존 프로세스 종료
Stop-Process -Name ngrok -Force
```

### URL을 가져올 수 없을 때
- ngrok이 실행 중인지 확인
- http://localhost:4040 접속하여 ngrok 웹 인터페이스 확인

### 메신저R 연결 실패
1. `/서버주소` 명령으로 현재 설정된 URL 확인
2. `/테스트` 명령으로 기본 연결 확인
3. `/디버그` 명령으로 상세 정보 확인

## 📝 명령어 요약

### PowerShell 명령어
- `.\start_server.ps1` - 서버 + ngrok 실행
- `.\get_ngrok_url.ps1` - ngrok URL 확인
- `.\test_ngrok.ps1` - API 테스트

### 카카오톡 명령어
- `/테스트` - 메신저R 연결 확인
- `/서버주소` - 현재 서버 URL 확인
- `/디버그` - 디버그 정보 표시
- `!버전` - 봇 버전 확인
- `!명령어` - 명령어 목록