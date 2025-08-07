// 가장 간단한 테스트 - 서버 연결 없이 로컬에서만 작동
function response(room, msg, sender, isGroupChat, replier, ImageDB) {
    // 모든 메시지에 즉시 응답
    replier.reply("받은 메시지: " + msg);
}

// responseFix 비활성화
function responseFix(room, msg, sender, isGroupChat, replier, ImageDB) {
    return;
}