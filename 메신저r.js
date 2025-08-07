// ===== 서버 URL 설정 =====
// ngrok URL로 변경하세요 (예: https://abc123.ngrok-free.app)
// start_server.ps1 실행 후 표시되는 URL을 여기에 입력
var SERVER_URL = 'https://doberman-safe-heron.ngrok-free.app/api/kakaotalk';
// 테스트용 localhost (메신저R이 PC에서 실행 중일 때만 사용)
// var SERVER_URL = 'http://localhost:8002/api/kakaotalk';

function response(room, msg, sender, isGroupChat, replier, ImageDB) {
    try {
        // 1. 기본적인 정보 확인 - 토스트로 표시
        if (msg === "/테스트") {
            replier.reply("✅ 메신저R 연결 성공!\n방이름: " + room + "\n보낸이: " + sender);
            return;
        }
        
        // 2. 서버 URL 확인
        if (msg === "/서버주소") {
            replier.reply("현재 서버 주소:\n" + SERVER_URL);
            return;
        }
        
        // 3. 서버 연결
        var url = SERVER_URL;
        
        // POST 방식으로 JSON 데이터 전송
        var postData = {
            room: room,
            sender: sender,
            msg: msg
        };
        
        var jsonString = JSON.stringify(postData);
        
        // Jsoup으로 HTTP 요청
        var httpResponse = org.jsoup.Jsoup.connect(url)
            .ignoreContentType(true)
            .ignoreHttpErrors(true)
            .header("Content-Type", "application/json; charset=utf-8")
            .requestBody(jsonString)
            .timeout(5000)  // 5초 타임아웃
            .method(org.jsoup.Connection.Method.POST)
            .execute();
            
        var responseText = httpResponse.body();
        
        // JSON 파싱
        var result = JSON.parse(responseText);
        
        // 디버그 정보 (특정 명령어로만)
        if (msg === "/디버그") {
            replier.reply("디버그 정보:\n" + 
                         "서버주소: " + SERVER_URL + "\n" +
                         "응답코드: " + httpResponse.statusCode() + "\n" +
                         "응답내용: " + responseText.substring(0, 100) + "...");
            return;
        }

        // 답장할 내용이 있으면 답장
        if (result && result.is_reply === true && result.reply_msg) {
            replier.reply(result.reply_msg);
        }
        
    } catch (error) {
        // 오류 발생 시 간단한 메시지만 출력
        if (msg === "/오류확인") {
            replier.reply("❌ 오류 발생: " + error.toString());
        }
    }
}

// 레거시 지원을 위한 함수 (일부 메신저R 버전에서 필요할 수 있음)
function responseFix(room, msg, sender, isGroupChat, replier, ImageDB) {
    response(room, msg, sender, isGroupChat, replier, ImageDB);
}

// =====================================================
// 아래 코드는 자동생성된 부분입니다
// =====================================================
function onNotificationPosted(sbn, sm) {
    var packageName = sbn.getPackageName();
    if (!packageName.startsWith("com.kakao.tal")) return;
    var actions = sbn.getNotification().actions;
    if (actions == null) return;
    var profileId = sbn.getUser().hashCode();
    var isMultiChat = profileId != 0;
    for (var n = 0; n < actions.length; n++) {
        var action = actions[n];
        if (action.getRemoteInputs() == null) continue;
        var bundle = sbn.getNotification().extras;
        var imageDB; var replier; var sender; var msg; var room; var isGroupChat;
        if(android.os.Build.VERSION.SDK_INT < 30) {
        imageDB = new com.xfl.msgbot.script.api.legacy.ImageDB(bundle.get("android.largeIcon"), null);
        room = bundle.get('android.subText');
        isGroupChat = room != null;
        if (room == null) room = sender;
        msg = bundle.get('android.text');
        sender = bundle.get('android.title');
        replier = new com.xfl.msgbot.script.api.legacy.SessionCacheReplier(packageName, action, room, false, "");
        com.xfl.msgbot.application.service.NotificationListener.Companion.setSession(packageName, room, action);
        if (this.hasOwnProperty("responseFix")) {
            responseFix(room, msg, sender, isGroupChat, replier, imageDB);
        }
     }else{
      msg = bundle.get("android.text").toString();
        sender = bundle.getString("android.title");
        room = bundle.getString("android.subText");
        if (room == null) room = bundle.getString("android.summaryText");
        isGroupChat = room != null;
        if (room == null) room = sender;
        replier = new com.xfl.msgbot.script.api.legacy.SessionCacheReplier(packageName, action, room, false, "");
        var icon = bundle.getParcelableArray("android.messages")[0].get("sender_person").getIcon().getBitmap();
        var image = bundle.getBundle("android.wearable.EXTENSIONS");
        if (image != null) image = image.getParcelable("background");
        imageDB = new com.xfl.msgbot.script.api.legacy.ImageDB(icon, image);
        com.xfl.msgbot.application.service.NotificationListener.Companion.setSession(packageName, room, action);
        if (this.hasOwnProperty("responseFix")) {
            responseFix(room, msg, sender, isGroupChat, replier, imageDB);
        }
     }
  }
} 