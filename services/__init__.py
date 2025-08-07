"""
서비스 패키지
외부 API 연동 및 복잡한 비즈니스 로직 처리
"""

# 임시: fn.py에서 서비스 관련 함수들 노출
try:
    from fn import (
        web_summary,
        fortune,
        zodiac,
        test
    )
except ImportError:
    print("⚠️ fn.py를 찾을 수 없습니다. 서비스 모듈을 개별적으로 import하세요.")

# 점진적으로 이동된 서비스들
try:
    from .web_scraper import *
except ImportError:
    pass

try:
    from .data_service import *
except ImportError:
    pass

try:
    from .fortune_service import *
except ImportError:
    pass