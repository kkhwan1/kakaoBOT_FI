"""
핸들러 패키지
각종 명령어를 처리하는 핸들러 모듈들
"""

# 임시: fn.py의 모든 함수를 노출 (점진적 마이그레이션용)
try:
    from fn import *
except ImportError:
    print("⚠️ fn.py를 찾을 수 없습니다. 핸들러 모듈을 개별적으로 import하세요.")

# 점진적으로 이동된 핸들러들 (이것들이 fn.py의 함수를 오버라이드)
try:
    from .ai_handler import *
except ImportError:
    pass

try:
    from .news_handler import *
except ImportError:
    pass

try:
    from .stock_handler import *
except ImportError:
    pass

try:
    from .media_handler import *
except ImportError:
    pass

try:
    from .game_handler import *
except ImportError:
    pass

try:
    from .utility_handler import *
except ImportError:
    pass

try:
    from .admin_handler import *
except ImportError:
    pass