"""
========================================
오류 모니터링 명령어 (관리자 전용)
========================================
"""

def error_logs(room: str, sender: str, msg: str):
    """오류 로그 조회 (관리자 전용)"""
    import config
    from error_monitor import error_monitor
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    # 파라미터 파싱
    parts = msg.split()
    limit = 20  # 기본값
    if len(parts) > 1:
        try:
            limit = int(parts[1])
            limit = min(100, max(1, limit))  # 1~100 범위로 제한
        except:
            pass
    
    return error_monitor.get_error_logs(limit)

def error_stats(room: str, sender: str, msg: str):
    """오류 통계 조회 (관리자 전용)"""
    import config
    from error_monitor import error_monitor
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    return error_monitor.get_error_stats()

def usage_stats(room: str, sender: str, msg: str):
    """사용 통계 조회 (관리자 전용)"""
    import config
    from error_monitor import error_monitor
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    return error_monitor.get_usage_stats()

def enable_command(room: str, sender: str, msg: str):
    """명령어 활성화 (관리자 전용)"""
    import config
    from error_monitor import error_monitor
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    # 명령어 파싱
    parts = msg.split(maxsplit=1)
    if len(parts) < 2:
        return "사용법: /명령어활성화 [명령어이름]"
    
    command_name = parts[1].strip()
    
    if error_monitor.enable_command(command_name):
        return f"✅ {command_name} 명령어가 활성화되었습니다."
    else:
        return f"ℹ️ {command_name} 명령어는 이미 활성 상태입니다."

def reset_command_stats(room: str, sender: str, msg: str):
    """명령어 통계 리셋 (관리자 전용)"""
    import config
    from error_monitor import error_monitor
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    # 명령어 파싱
    parts = msg.split(maxsplit=1)
    if len(parts) < 2:
        return "사용법: /통계리셋 [명령어이름]"
    
    command_name = parts[1].strip()
    
    error_monitor.reset_command_stats(command_name)
    return f"✅ {command_name} 명령어의 모든 통계가 리셋되었습니다."

def performance_recommendations(room: str, sender: str, msg: str):
    """성능 최적화 추천 (관리자 전용)"""
    import config
    from error_monitor import error_monitor
    
    # 관리자 체크
    if not config.is_admin_user(sender):
        return "⚠️ 관리자만 사용할 수 있는 명령어입니다."
    
    recommendations = error_monitor.get_performance_recommendations()
    
    message = "⚡ 성능 최적화 추천\n\n"
    
    if recommendations['high_priority_cache']:
        message += "【우선 캐싱 추천】\n"
        for cmd in recommendations['high_priority_cache']:
            message += f"  • {cmd}\n"
        message += "\n"
    
    if recommendations['low_priority_cache']:
        message += "【캐시 시간 단축 추천】\n"
        for cmd in recommendations['low_priority_cache']:
            message += f"  • {cmd}\n"
        message += "\n"
    
    if recommendations['needs_optimization']:
        message += "【최적화 필요】\n"
        for cmd in recommendations['needs_optimization']:
            message += f"  • {cmd}\n"
        message += "\n"
    
    if not any(recommendations.values()):
        message += "현재 성능이 양호합니다."
    
    return message