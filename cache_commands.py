"""
========================================
캐시 관리 명령어 (관리자 전용)
========================================
"""

def clear_cache(room: str, sender: str, msg: str):
    """캐시 초기화 (관리자 전용)"""
    import config
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    # main_improved의 캐시 초기화
    try:
        import main_improved
        cache_size = len(main_improved.response_cache)
        main_improved.response_cache.clear()
        return f"✅ 캐시가 초기화되었습니다.\n📊 삭제된 캐시: {cache_size}개"
    except Exception as e:
        return f"❌ 캐시 초기화 실패: {str(e)}"

def cache_status(room: str, sender: str, msg: str):
    """캐시 상태 조회 (관리자 전용)"""
    import config
    import datetime
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    try:
        import main_improved
        cache_count = len(main_improved.response_cache)
        
        message = f"📊 캐시 상태\n\n"
        message += f"캐시된 항목: {cache_count}개\n\n"
        
        if cache_count > 0:
            message += "【최근 캐시 항목】\n"
            now = datetime.datetime.now()

            # 최근 10개만 표시 - 동시성 문제 방지를 위해 복사본 생성
            cache_snapshot = dict(main_improved.response_cache)
            items = list(cache_snapshot.items())[-10:]
            for key, (data, cached_time) in items:
                # 키에서 명령어 추출
                parts = key.split(':')
                if len(parts) >= 3:
                    cmd = parts[2][:20]  # 명령어 부분만
                    age = (now - cached_time).total_seconds()
                    message += f"  • {cmd}: {age:.0f}초 전\n"
        
        return message
        
    except Exception as e:
        return f"❌ 캐시 상태 조회 실패: {str(e)}"