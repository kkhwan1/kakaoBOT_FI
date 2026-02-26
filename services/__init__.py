"""
서비스 레이어 패키지
외부 API 호출, 데이터 처리 등의 비즈니스 로직
"""

# HTTP 서비스
try:
    from .http_service import request, fetch_json, fetch_html, HTTPClient
except ImportError as e:
    print(f"HTTP service import error: {e}")

# DB 서비스
try:
    from .db_service import (
        get_conn,
        db_connection,
        execute_query,
        fetch_one,
        fetch_all,
        DatabaseService,
        db_service
    )
except ImportError as e:
    print(f"DB service import error: {e}")

# AI 서비스
try:
    from .ai_service import AIService, ai_service
except ImportError as e:
    print(f"AI service import error: {e}")

# 웹 스크래핑 서비스
try:
    from .web_scraping_service import WebScrapingService, web_scraping_service
except ImportError as e:
    print(f"Web scraping service import error: {e}")

# 스케줄 서비스
try:
    from .schedule_service import ScheduleService, schedule_service
except ImportError as e:
    print(f"Schedule service import error: {e}")

# 임시: fn.py에서 서비스 관련 함수들 노출 (점진적 마이그레이션)
try:
    from fn import (
        web_summary,
        fortune,
        zodiac,
        test
    )
except ImportError:
    pass

__all__ = [
    # HTTP
    'request',
    'fetch_json', 
    'fetch_html',
    'HTTPClient',
    
    # DB
    'get_conn',
    'db_connection',
    'execute_query',
    'fetch_one',
    'fetch_all',
    'DatabaseService',
    'db_service',
    
    # AI
    'AIService',
    'ai_service',
    
    # Web Scraping
    'WebScrapingService',
    'web_scraping_service',

    # Schedule
    'ScheduleService',
    'schedule_service',
]