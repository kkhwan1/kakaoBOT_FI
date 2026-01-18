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
# AI 핸들러
try:
    from .ai_handler import (
        get_ai_answer,
        gemini15_flash,
        perplexity_chat_fast,
        claude3_haiku,
        gpt4o_mini,
        get_ai_greeting,
        get_ai_style
    )
except ImportError as e:
    print(f"AI handler import error: {e}")

# 뉴스 핸들러
try:
    from .news_handler import (
        economy_news,
        it_news,
        realestate_news,
        world_news
    )
except ImportError as e:
    print(f"News handler import error: {e}")

# 주식/금융 핸들러
try:
    from .stock_handler import (
        stock,
        coin,
        exchange,
        gold,
        stock_upper,
        stock_lower
    )
except ImportError as e:
    print(f"Stock handler import error: {e}")

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