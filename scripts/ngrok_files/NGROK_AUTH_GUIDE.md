# ngrok Authtoken 찾기 가이드

## ⚠️ 중요: API Key ≠ Authtoken

현재 제공해주신 것:
- **API Key**: `ak_30sMuuLkWlpsBAOAfaE1FQvPCT2...`
- **용도**: ngrok API를 프로그래밍적으로 사용할 때 필요

우리가 필요한 것:
- **Authtoken**: ngrok 터널을 생성할 때 필요
- **형식**: 더 짧고 다른 형식

## 🔍 Authtoken 찾는 방법

### 1. ngrok 대시보드 로그인
https://dashboard.ngrok.com/

### 2. 정확한 위치로 이동
다음 중 하나의 방법으로 이동:

#### 방법 A: 직접 URL
https://dashboard.ngrok.com/get-started/your-authtoken

#### 방법 B: 메뉴 네비게이션
1. 대시보드 좌측 메뉴에서 **"Getting Started"** 클릭
2. **"Your Authtoken"** 섹션 확인

### 3. Authtoken 확인
다음과 같은 형태로 표시됩니다:
```
Your authtoken is: 1rlHSX3HqrqmOWZdeJ6bIv8rfuo_4cmS1QswRGyxcQD8NOukF
```

## 📋 빠른 체크리스트

- [ ] https://dashboard.ngrok.com/ 로그인
- [ ] "Getting Started" → "Your Authtoken" 이동
- [ ] Authtoken 복사 (API Key가 아님!)
- [ ] 길이가 약 50자 정도인지 확인
- [ ] `.\setup_ngrok_auth.ps1` 실행하여 설정

## 🆘 Authtoken이 안 보이는 경우

### 옵션 1: 새로 생성
1. 대시보드에서 **"Authtokens"** 메뉴 찾기
2. **"Create Authtoken"** 또는 **"New Authtoken"** 클릭
3. 설명 입력 (예: "KakaoBot Server")
4. 생성된 토큰 복사

### 옵션 2: 기본 Authtoken 재생성
1. "Your Authtoken" 페이지에서
2. **"Regenerate"** 버튼 클릭
3. 새로 생성된 토큰 복사

## ✅ 올바른 Authtoken 예시

```
# 올바른 형식 (Authtoken)
2nxU9P5cW3M8vPqZdJ6bIv8rfuo_4cDS1QswRGyacQD9NOukF

# 틀린 형식 (API Key)
ak_30sMuuLkWlpsBAOAfaE1FQvPCT2...
```

## 🚀 Authtoken 받은 후

1. PowerShell에서 실행:
   ```powershell
   .\setup_ngrok_auth.ps1
   ```

2. 받은 Authtoken 입력

3. 서버 시작:
   ```powershell
   .\start_server.ps1
   ```

---

**참고**: Authtoken은 ngrok 에이전트(CLI)가 터널을 만들 때 사용하고, API Key는 ngrok API를 호출할 때 사용합니다. 우리는 터널을 만들어야 하므로 Authtoken이 필요합니다!