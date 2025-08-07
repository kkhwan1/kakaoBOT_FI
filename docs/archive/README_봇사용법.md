# 카카오톡 봇 사용 가이드

## 현재 상태

✅ **서버**: 정상 작동 중
✅ **영화 순위**: KOBIS 실시간 데이터 수신 성공
⚠️ **문제**: 응답이 카카오톡으로 전달되지 않음

## 문제 해결 방법

### 1. 메신저 봇 설정 확인

메신저 봇 앱에서 다음을 확인하세요:

1. **봇 상태**: 활성화되어 있는지 확인
2. **서버 주소**: ngrok URL이 올바른지 확인
3. **응답 설정**: 
   - 응답 전송 방식: `POST`
   - 응답 형식: `JSON`
   - 인코딩: `UTF-8`

### 2. ngrok 확인

```bash
# ngrok 상태 확인
curl https://YOUR_NGROK_URL.ngrok.io/health

# 예상 응답:
{
  "status": "healthy",
  "timestamp": "...",
  "allowed_rooms": ...,
  "admin_room": "..."
}
```

### 3. 서버 로그 확인

서버 로그에서 다음 패턴을 확인:

```
[영화순위] Selenium 성공  # ✅ 데이터 수신 성공
Response generated - Room: '이국환'  # ✅ 응답 생성됨
POST /api/kakaotalk 200 OK  # ✅ API 응답 성공
```

하지만 직후에:
```
Received body: '{}'  # ⚠️ 빈 요청이 다시 옴
Missing required fields  # ⚠️ 메신저 봇이 재시도
```

### 4. 메신저 봇 스크립트 확인

메신저 봇의 응답 스크립트가 다음과 같은지 확인:

```javascript
// 메신저 봇 응답 스크립트 예시
function response(room, msg, sender, isGroupChat, replier) {
    // API 호출
    var result = Api.callApi({
        url: "https://YOUR_NGROK_URL.ngrok.io/api/kakaotalk",
        method: "POST",
        data: {
            room: room,
            sender: sender,
            msg: msg
        }
    });
    
    // 응답 처리
    if (result && result.is_reply) {
        replier.reply(result.reply_msg);  // 이 부분이 중요!
    }
}
```

### 5. 응답 크기 문제 해결

카카오톡 메시지 제한이 있을 수 있으므로:

1. **메시지 길이 제한**: 이미 적용됨 (1000자)
2. **이모지 문제**: 일부 이모지가 문제일 수 있음

### 6. 디버그 모드 테스트

```python
# 서버에서 직접 테스트
python test_movie_api.py

# 응답이 정상인지 확인
# is_reply: true
# reply_room: "테스트방"
# reply_msg: "영화 순위..."
```

## 빠른 해결책

### 방법 1: 메신저 봇 재시작
1. 메신저 봇 앱 종료
2. 카카오톡 앱 종료
3. 메신저 봇 재시작
4. 카카오톡 재시작

### 방법 2: ngrok 재시작
```bash
# ngrok 종료 (Ctrl+C)
# ngrok 재시작
ngrok http 8002

# 새 URL을 메신저 봇에 등록
```

### 방법 3: 서버 재시작
```bash
# 서버 종료 (Ctrl+C)
# 서버 재시작
python main.py
```

## 테스트 명령어

카카오톡에서 테스트:
- `/영화순위` - 영화 순위 조회
- `/명령어` - 전체 명령어 목록
- `/주식 삼성전자` - 주식 정보 (작동 확인용)

## 로그 메시지 의미

| 로그 | 의미 | 상태 |
|------|------|------|
| `[영화순위] Playwright 시도 중...` | Playwright로 시도 | 진행중 |
| `[영화순위] Selenium 성공` | Selenium으로 데이터 수신 | ✅ 성공 |
| `Response generated` | 응답 JSON 생성됨 | ✅ 성공 |
| `200 OK` | API 응답 성공 | ✅ 성공 |
| `Received body: '{}'` | 빈 요청 수신 | ⚠️ 문제 |

## 최종 확인사항

1. **메신저 봇이 응답을 제대로 파싱하는지 확인**
   - JSON 파싱 오류가 없는지
   - `reply_msg` 필드를 제대로 읽는지

2. **네트워크 문제 확인**
   - ngrok 터널이 안정적인지
   - 타임아웃이 발생하지 않는지

3. **인코딩 문제 확인**
   - UTF-8 인코딩이 올바른지
   - 이모지가 문제가 되지 않는지

## 문의

문제가 지속되면 다음 정보와 함께 문의:
- 서버 로그 전체
- 메신저 봇 설정 스크린샷
- ngrok 대시보드 상태