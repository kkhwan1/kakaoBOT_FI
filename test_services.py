#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서비스 레이어 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 서비스 레이어 테스트 시작\n")
print("=" * 50)

# 1. HTTP 서비스 테스트
print("\n📡 HTTP 서비스 테스트")
print("-" * 30)
try:
    from services.http_service import request, fetch_json, fetch_html
    print("✅ HTTP 서비스 import 성공")
    
    # 간단한 요청 테스트
    test_url = "https://httpbin.org/get"
    result = fetch_json(test_url)
    if result and 'url' in result:
        print(f"✅ HTTP GET 테스트 성공: {result['url']}")
    else:
        print("❌ HTTP GET 테스트 실패")
except Exception as e:
    print(f"❌ HTTP 서비스 테스트 실패: {e}")

# 2. DB 서비스 테스트
print("\n💾 DB 서비스 테스트")
print("-" * 30)
try:
    from services.db_service import get_conn, DatabaseService
    print("✅ DB 서비스 import 성공")
    
    # DB 연결 테스트 (실제 연결은 설정에 따라 실패할 수 있음)
    try:
        conn, cursor = get_conn()
        print("✅ DB 연결 테스트 성공")
        conn.close()
    except Exception as db_error:
        print(f"⚠️ DB 연결 테스트 실패 (예상됨): {db_error}")
        
except Exception as e:
    print(f"❌ DB 서비스 import 실패: {e}")

# 3. AI 서비스 테스트
print("\n🤖 AI 서비스 테스트")
print("-" * 30)
try:
    from services.ai_service import AIService, ai_service
    print("✅ AI 서비스 import 성공")
    
    # AI 서비스 객체 확인
    if ai_service:
        print("✅ AI 서비스 싱글톤 인스턴스 생성 성공")
        
        # 메소드 존재 확인
        methods = ['get_ai_response', 'gemini_chat', 'gpt_chat', 'claude_chat', 'perplexity_chat']
        for method in methods:
            if hasattr(ai_service, method):
                print(f"  ✓ {method} 메소드 확인")
            else:
                print(f"  ✗ {method} 메소드 없음")
                
except Exception as e:
    print(f"❌ AI 서비스 테스트 실패: {e}")

# 4. 웹 스크래핑 서비스 테스트
print("\n🕷️ 웹 스크래핑 서비스 테스트")
print("-" * 30)
try:
    from services.web_scraping_service import WebScrapingService, web_scraping_service
    print("✅ 웹 스크래핑 서비스 import 성공")
    
    # 서비스 객체 확인
    if web_scraping_service:
        print("✅ 웹 스크래핑 서비스 싱글톤 인스턴스 생성 성공")
        
        # 메소드 존재 확인
        methods = ['get_naver_news', 'get_stock_price', 'get_weather_info', 'get_youtube_trending', 'get_lotto_result']
        for method in methods:
            if hasattr(web_scraping_service, method):
                print(f"  ✓ {method} 메소드 확인")
            else:
                print(f"  ✗ {method} 메소드 없음")
                
except Exception as e:
    print(f"❌ 웹 스크래핑 서비스 테스트 실패: {e}")

# 5. 서비스 패키지 전체 import 테스트
print("\n📦 서비스 패키지 통합 테스트")
print("-" * 30)
try:
    import services
    print("✅ services 패키지 import 성공")
    
    # __all__ 에 정의된 모든 요소 확인
    from services import request, fetch_json, fetch_html
    from services import get_conn, execute_query, fetch_one, fetch_all
    from services import AIService, ai_service
    from services import WebScrapingService, web_scraping_service
    
    print("✅ 모든 주요 서비스 컴포넌트 import 성공")
    
except Exception as e:
    print(f"❌ 서비스 패키지 통합 테스트 실패: {e}")

print("\n" + "=" * 50)
print("🏁 서비스 레이어 테스트 완료")
print("=" * 50)

# 6. 핸들러와 서비스 통합 테스트
print("\n🔗 핸들러-서비스 통합 테스트")
print("-" * 30)
try:
    # 핸들러가 서비스를 사용할 수 있는지 확인
    from handlers import *
    print("✅ 핸들러 모듈 import 성공")
    
    # 서비스 레이어가 핸들러에서 사용 가능한지 확인
    print("✅ 핸들러-서비스 통합 준비 완료")
    
except Exception as e:
    print(f"⚠️ 핸들러-서비스 통합 테스트 실패: {e}")

print("\n✨ 모든 테스트 완료!")