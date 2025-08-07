#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
모듈 구조 테스트 스크립트
새로운 모듈 구조가 제대로 작동하는지 확인
"""

import sys
import traceback

def test_imports():
    """각 모듈이 제대로 import 되는지 테스트"""
    
    print("=" * 50)
    print("📦 모듈 Import 테스트 시작")
    print("=" * 50)
    
    results = []
    
    # 1. Core 모듈 테스트
    try:
        from core.router import get_reply_msg
        print("✅ core.router.get_reply_msg import 성공")
        results.append(("core.router", True))
    except ImportError as e:
        print(f"❌ core.router import 실패: {e}")
        results.append(("core.router", False))
    
    # 2. Core message_handler 테스트
    try:
        from core.message_handler import send_message
        print("✅ core.message_handler.send_message import 성공")
        results.append(("core.message_handler", True))
    except ImportError as e:
        print(f"❌ core.message_handler import 실패: {e}")
        results.append(("core.message_handler", False))
    
    # 3. Utils 모듈 테스트
    try:
        from utils.text_utils import clean_for_kakao
        print("✅ utils.text_utils.clean_for_kakao import 성공")
        results.append(("utils.text_utils", True))
    except ImportError as e:
        print(f"❌ utils.text_utils import 실패: {e}")
        results.append(("utils.text_utils", False))
    
    try:
        from utils.db_helper import get_conn
        print("✅ utils.db_helper.get_conn import 성공")
        results.append(("utils.db_helper", True))
    except ImportError as e:
        print(f"❌ utils.db_helper import 실패: {e}")
        results.append(("utils.db_helper", False))
    
    # 4. Handlers 테스트 (fn.py를 통한 브릿지)
    try:
        from handlers import stock, whether_today, youtube_popular_all
        print("✅ handlers (from fn.py) import 성공")
        results.append(("handlers (bridge)", True))
    except ImportError as e:
        print(f"❌ handlers import 실패: {e}")
        results.append(("handlers (bridge)", False))
    
    # 5. Services 테스트
    try:
        from services import web_summary, fortune
        print("✅ services (from fn.py) import 성공")
        results.append(("services (bridge)", True))
    except ImportError as e:
        print(f"❌ services import 실패: {e}")
        results.append(("services (bridge)", False))
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for module_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {module_name}: {'성공' if success else '실패'}")
    
    print(f"\n총 {total_count}개 중 {success_count}개 성공")
    
    if success_count == total_count:
        print("\n🎉 모든 모듈이 정상적으로 import됩니다!")
    else:
        print("\n⚠️ 일부 모듈 import에 실패했습니다. 확인이 필요합니다.")
    
    return success_count == total_count

def test_router_function():
    """라우터 함수가 제대로 작동하는지 테스트"""
    
    print("\n" + "=" * 50)
    print("🔧 라우터 기능 테스트")
    print("=" * 50)
    
    try:
        from core.router import get_reply_msg
        
        # 간단한 테스트 명령어들
        test_cases = [
            ("테스트방", "테스터", "/테스트"),
            ("테스트방", "테스터", "/시간"),
            ("테스트방", "테스터", "/안녕"),
        ]
        
        for room, sender, msg in test_cases:
            print(f"\n테스트: {msg}")
            try:
                result = get_reply_msg(room, sender, msg)
                if result:
                    print(f"  응답: {result[:50]}...")
                else:
                    print(f"  응답: None")
            except Exception as e:
                print(f"  에러: {e}")
        
        print("\n✅ 라우터 기능 테스트 완료")
        return True
        
    except Exception as e:
        print(f"\n❌ 라우터 기능 테스트 실패: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🚀 카카오봇 모듈 구조 테스트 시작\n")
    
    # Import 테스트
    import_success = test_imports()
    
    # 라우터 기능 테스트
    router_success = test_router_function()
    
    # 최종 결과
    print("\n" + "=" * 50)
    print("🏁 최종 결과")
    print("=" * 50)
    
    if import_success and router_success:
        print("✅ 모든 테스트 통과! 새로운 구조가 정상 작동합니다.")
        sys.exit(0)
    else:
        print("⚠️ 일부 테스트 실패. 추가 작업이 필요합니다.")
        sys.exit(1)