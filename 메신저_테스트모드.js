// ===== 테스트 모드 메신저봇 스크립트 =====
// 이 스크립트는 서버의 /test 엔드포인트를 사용합니다
// 서버 응답이 제대로 오는지 확인하는 용도입니다

// ngrok URL 설정
var SERVER_URL = 'https://doberman-safe-heron.ngrok-free.app/test'; // /test 엔드포인트 사용

function response(room, msg, sender, isGroupChat, replier, ImageDB) {
    try {
        // 1. 로컬 테스트 (서버 연결 없이)
        if (msg === "/로컬") {
            replier.reply("✅ 로컬 테스트 성공!");
            return;
        }
        
        // 2. 서버 테스트 - 간단한 JSON 전송
        var postData = {
            "room": room,
            "sender": sender,
            "msg": msg
        };
        
        // JSON 문자열로 변환
        var jsonString = JSON.stringify(postData);
        
        // 3. HTTP 요청 전송
        try {
            var httpResponse = org.jsoup.Jsoup.connect(SERVER_URL)
                .ignoreContentType(true)
                .ignoreHttpErrors(true)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .requestBody(jsonString)
                .timeout(3000)  // 3초 타임아웃
                .method(org.jsoup.Connection.Method.POST)
                .execute();
                
            var responseText = httpResponse.body();
            var statusCode = httpResponse.statusCode();
            
            // 4. 응답 확인
            if (statusCode === 200) {
                try {
                    var result = JSON.parse(responseText);
                    
                    // test_response 확인
                    if (result.test_response && result.test_response.is_reply) {
                        var replyMsg = result.test_response.reply_msg;
                        if (replyMsg) {
                            replier.reply(replyMsg);
                        } else {
                            replier.reply("⚠️ 응답 메시지가 비어있음");
                        }
                    } else {
                        replier.reply("⚠️ test_response 없음");
                    }
                } catch(e) {
                    replier.reply("❌ JSON 파싱 오류: " + e.toString());
                }
            } else {
                replier.reply("❌ HTTP 오류: " + statusCode);
            }
            
        } catch(e) {
            replier.reply("❌ 네트워크 오류: " + e.toString());
        }
        
    } catch(error) {
        replier.reply("❌ 스크립트 오류: " + error.toString());
    }
}

// responseFix 비활성화
function responseFix(room, msg, sender, isGroupChat, replier, ImageDB) {
    return;
}