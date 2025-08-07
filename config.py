"""
========================================
STORIUM Bot 통합 설정 시스템
========================================
모든 방별, 기능별 권한을 이곳에서 통합 관리합니다.
"""

# ========================================
# 통합 설정
# ========================================
BOT_CONFIG = {
    # 허용된 채팅방 목록
    "ALLOWED_ROOMS": ['이국환', '기타1', '기타2', '기타3', '테스트방'],
    
    # AI 인사말 및 스타일
    "AI_GREETING": "안녕하세요! 😊 STORIUM Bot입니다. 무엇을 도와드릴까요?",
    "AI_STYLE": "친근하고 간결하게 2-3문장으로 답변. 봇 기능 자연스럽게 안내. 이모지 적절히 사용.",
    
    # 채팅 히스토리 관리
    "CHAT_HISTORY": {
        "MAX_HISTORY_LENGTH": 4,
        "HISTORY_TIMEOUT": 1800000,  # 30분 (밀리초)
        "CONTEXT_TEMPLATE": """이전 대화를 참고해서 자연스럽게 대화를 이어가세요. 이전 대화 내용:
{history}

현재 질문: {question}"""
    },
    
    # 관리자 설정
    "ADMIN_USERS": ['이국환'],
    "ADMIN_ROOM": "이국환",
    
    # 봇 정보
    "BOT_NAME": "STORIUM Bot",
    "VERSION": "2.0.0"
}

# ========================================
# API 키 설정
# ========================================
API_KEYS = {
    "GEMINI": "AIzaSyCADxqkayictwOGe0BoXxO6aOGLbY6OZCY",  # Google Gemini API 키
    "CLAUDE": "YOUR_CLAUDE_API_KEY_HERE",  # Claude API 키
    "OPENAI": "YOUR_OPENAI_API_KEY_HERE",  # OpenAI API 키
    "YOUTUBE": "AIzaSyDvZ407rdm6_nFtjc-25XWibBO9d3pRqEI"  # YouTube API 키
}

# ========================================
# 편의 함수들
# ========================================

def get_allowed_rooms():
    """허용된 방 목록을 반환"""
    return BOT_CONFIG["ALLOWED_ROOMS"]

def get_admin_room():
    """관리자 방을 반환"""
    return BOT_CONFIG["ADMIN_ROOM"]

def is_room_enabled(room_name):
    """방이 활성화되어 있는지 확인"""
    return room_name in BOT_CONFIG["ALLOWED_ROOMS"]

def is_admin_user(username):
    """사용자가 관리자인지 확인"""
    return username in BOT_CONFIG["ADMIN_USERS"]

def get_ai_greeting():
    """AI 인사말 반환"""
    return BOT_CONFIG["AI_GREETING"]

def get_ai_style():
    """AI 스타일 가이드 반환"""
    return BOT_CONFIG["AI_STYLE"]

def get_chat_history_config():
    """채팅 히스토리 설정 반환"""
    return BOT_CONFIG["CHAT_HISTORY"]

def get_bot_info():
    """봇 정보 반환"""
    return {
        "name": BOT_CONFIG["BOT_NAME"],
        "version": BOT_CONFIG["VERSION"]
    }

# ========================================
# 기존 호환성을 위한 함수들
# ========================================

def check_room_feature(room, feature):
    """모든 방에서 모든 기능을 허용 (단순화)"""
    return is_room_enabled(room)

def get_special_user_response(sender):
    """특별 사용자 응답 없음 (단순화)"""
    return None

# ========================================
# ngrok URL 관리
# ========================================

# ngrok 설정
NGROK_CONFIG = {
    "ENABLED": True,
    "URL": None,  # 자동으로 감지됨
    "FALLBACK_URL": "http://localhost:8002"
}

def get_ngrok_url():
    """현재 ngrok URL 가져오기"""
    try:
        import requests
        # ngrok API로 현재 터널 정보 가져오기
        resp = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        tunnels = resp.json()['tunnels']
        
        # HTTPS 터널 우선, 없으면 HTTP
        for tunnel in tunnels:
            if tunnel['proto'] == 'https':
                NGROK_CONFIG['URL'] = tunnel['public_url']
                return tunnel['public_url']
        
        # HTTPS가 없으면 HTTP 사용
        for tunnel in tunnels:
            if tunnel['proto'] == 'http':
                NGROK_CONFIG['URL'] = tunnel['public_url']
                return tunnel['public_url']
                
    except Exception as e:
        print(f"ngrok URL 감지 실패: {e}")
    
    # ngrok이 실행 중이 아니면 로컬호스트 반환
    return NGROK_CONFIG.get('FALLBACK_URL', 'http://localhost:8002')

def is_ngrok_running():
    """ngrok이 실행 중인지 확인"""
    try:
        import requests
        resp = requests.get('http://localhost:4040/api/tunnels', timeout=1)
        return resp.status_code == 200
    except:
        return False

# ========================================
# 설정 출력 함수 (디버깅용)
# ========================================

def print_config_summary():
    """현재 설정 요약을 출력"""
    bot_info = get_bot_info()
    print(f"=== {bot_info['name']} 설정 요약 ===")
    print(f"허용된 방: {len(get_allowed_rooms())}개")
    print(f"관리자 방: {get_admin_room()}")
    print(f"관리자 사용자: {len(BOT_CONFIG['ADMIN_USERS'])}명")
    print(f"버전: {bot_info['version']}")
    print("✅ 설정이 정상입니다.")

if __name__ == "__main__":
    # 설정 파일을 직접 실행할 때 요약 정보 출력
    print_config_summary() 
