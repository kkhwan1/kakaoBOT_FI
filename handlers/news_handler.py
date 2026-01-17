#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
뉴스 핸들러 모듈
뉴스 관련 명령어 처리
"""

import urllib.parse
from datetime import datetime, timezone, timedelta
from utils.debug_logger import debug_logger

# 한국 시간대 (KST = UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_time():
    """한국 시간 반환"""
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M")

# request 함수를 fn.py에서 가져오기
try:
    from fn import request
except ImportError:
    # 폴백: 직접 구현
    import requests
    from bs4 import BeautifulSoup
    
    def request(url, method="get", result="text", params=None, headers=None):
        """HTTP 요청 헬퍼 함수"""
        try:
            if method.lower() == "get":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, params=params, headers=headers, timeout=10)
            
            if result == "json":
                return response.json()
            elif result == "bs":
                return BeautifulSoup(response.text, 'html.parser')
            else:
                return response.text
        except Exception as e:
            print(f"Request error: {e}")
            return None


def economy_news(room: str, sender: str, msg: str):
    """경제 뉴스 - 네이버 Open API 사용"""
    return _category_news("경제", "경제", "부동산 주식 경제")


def it_news(room: str, sender: str, msg: str):
    """IT 뉴스 - 네이버 Open API 사용"""
    return _category_news("IT", "IT과학", "테크 기술")


def realestate_news(room: str, sender: str, msg: str):
    """부동산 뉴스 - 네이버 Open API 사용"""
    return _category_news("부동산", "부동산", "아파트 주택 집값")


def _category_news(category_name: str, display_name: str, search_keywords: str):
    """
    카테고리별 뉴스 가져오기 - 네이버 Open API 사용

    Args:
        category_name: 카테고리 이름 (emoji용)
        display_name: 표시 이름
        search_keywords: 검색 키워드 (공백 구분)
    """
    # 네이버 Open API 키 가져오기
    try:
        import os
        client_id = os.getenv("NAVER_CLIENT_ID", "")
        client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            debug_logger.error("네이버 API 키가 설정되지 않음")
            return _fallback_category_news(category_name, display_name)
    except ImportError:
        return _fallback_category_news(category_name, display_name)

    try:
        # 네이버 Open API - 뉴스 검색
        encode_keyword = urllib.parse.quote(search_keywords.split()[0])
        url = f"https://openapi.naver.com/v1/search/news.json?query={encode_keyword}&display=5&sort=date"

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

        response = request(url, method="get", result="text", headers=headers)

        if not response:
            return _fallback_category_news(category_name, display_name)

        import json
        import re
        data = json.loads(response)

        if data.get('errorCode'):
            debug_logger.error(f"네이버 API 오류: {data.get('errorMessage')}")
            return _fallback_category_news(category_name, display_name)

        items = data.get('items', [])

        if not items:
            return _fallback_category_news(category_name, display_name)

        # 이모지 매핑
        emoji_map = {"경제": "💰", "IT": "💻", "부동산": "🏠"}
        emoji = emoji_map.get(category_name, "📰")

        send_msg = f"{emoji} {display_name} 뉴스 📺\n📅 {get_kst_time()} 기준"

        for idx, item in enumerate(items[:5], 1):
            title = item.get('title', '')
            description = item.get('description', '')
            link = item.get('originallink') or item.get('link', '')
            source = item.get('source', '')

            # HTML 태그 및 특수 문자 제거
            title = re.sub(r'<[^>]+>', '', title)
            title = title.replace('&quot;', '"').replace('&apos;', "'")
            title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            description = re.sub(r'<[^>]+>', '', description)
            description = description.replace('&quot;', '"').replace('&apos;', "'")
            description = description.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

            # 설명이 너무 길면 자르기
            if len(description) > 100:
                description = description[:97] + "..."

            # 해시태그 생성 (설명에서 키워드 추출)
            tags = []

            # 출처 추가
            if source:
                tags.append(f"(출처:{source})")

            # 설명에서 주요 키워드 추출 (2글자 이상 한글)
            words = re.findall(r'[가-힣]{2,}', description)
            unique_words = list(dict.fromkeys(words))[:3]  # 중복 제거, 최대 3개
            for word in unique_words:
                tags.append(f"#{word}")

            tag_str = ' '.join(tags) if tags else ""

            # 네이버 뉴스 링크 변환
            if link and 'news.naver.com' in link:
                match = re.search(r'/article/(\d+)/(\d+)', link)
                if match:
                    office_id, article_id = match.groups()
                    link = f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"

            # 메시지 구성
            news_item = f"\n\n{idx}. {title}"
            if description:
                news_item += f"\n{description}"
            if tag_str:
                news_item += f"\n{tag_str}"
            news_item += f"\n{link}"

            send_msg += news_item

        return send_msg

    except Exception as e:
        debug_logger.error(f"{display_name} 뉴스 오류: {str(e)}")
        return _fallback_category_news(category_name, display_name)


def _fallback_category_news(category_name: str, display_name: str):
    """API 실패시 폴백 - 스크래핑 방식"""
    emoji_map = {"경제": "💰", "IT": "💻", "부동산": "🏠"}
    emoji = emoji_map.get(category_name, "📰")

    # 카테고리별 URL 매핑
    area_map = {"경제": 101, "IT": 105, "부동산": 260}
    area = area_map.get(category_name, 101)

    try:
        if category_name == "부동산":
            url = f'https://m.news.naver.com/rankingList?sid1=101&sid2={area}'
        else:
            url = f'https://m.news.naver.com/main?mode=LSD&sid1={area}'

        result = request(url, method="get", result="bs")
        send_msg = f"{emoji} {display_name} 뉴스 📺\n📅 {get_kst_time()} 기준"

        news_items = result.select('li.sa_item')
        if not news_items:
            return f"{emoji} {display_name} 뉴스를 불러올 수 없습니다."

        for idx, item in enumerate(news_items[:5], 1):
            title_elem = item.select_one('.sa_text_strong')
            link_elem = item.select_one('.sa_text_title')

            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem.get('href', '')
                send_msg += f'\n\n{idx}. {title}\n{link}'

        return send_msg

    except Exception as e:
        debug_logger.error(f"{display_name} 뉴스 폴백 오류: {str(e)}")
        return f"{emoji} {display_name} 뉴스를 불러오는 중 오류가 발생했습니다."


def search_news(room: str, sender: str, msg: str):
    """뉴스 검색 - 네이버 Open API 사용"""
    keyword = msg.replace("/뉴스", "").strip()
    if not keyword:
        return "🔍 검색어를 입력해주세요 (사용법: /뉴스 키워드)"

    # 네이버 Open API 키 가져오기
    try:
        import os
        client_id = os.getenv("NAVER_CLIENT_ID", "")
        client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            debug_logger.error("네이버 API 키가 설정되지 않음")
            return _search_news_google_fallback(keyword, request)
    except ImportError:
        return _search_news_google_fallback(keyword, request)

    try:
        # 네이버 Open API - 뉴스 검색
        encode_keyword = urllib.parse.quote(keyword)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encode_keyword}&display=5&sort=date"

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

        response = request(url, method="get", result="text", headers=headers)

        if not response:
            return _search_news_google_fallback(keyword, request)

        import json
        data = json.loads(response)

        if data.get('errorCode'):
            debug_logger.error(f"네이버 API 오류: {data.get('errorMessage')}")
            return _search_news_google_fallback(keyword, request)

        items = data.get('items', [])

        if not items:
            return _search_news_google_fallback(keyword, request)

        send_msg = f"📰 {keyword} 뉴스 📺\n📅 {get_kst_time()} 기준"

        import re
        for item in items[:5]:
            title = item.get('title', '')
            link = item.get('originallink') or item.get('link', '')

            # 네이버 뉴스 링크 변환
            if link and 'news.naver.com' in link:
                match = re.search(r'/article/(\d+)/(\d+)', link)
                if match:
                    office_id, article_id = match.groups()
                    link = f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"

            # HTML 태그 및 특수 문자 제거
            title = re.sub(r'<[^>]+>', '', title)
            title = title.replace('&quot;', '"').replace('&apos;', "'")
            title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

            # 출처 추출
            source_elem = item.get('description', '')
            source_match = re.search(r'([가-힣A-Za-z]+)\s*\(', source_elem)
            source = source_match.group(1) if source_match else ''
            if not source:
                source = item.get('source', '')

            if title:
                # 해시태그 생성
                tags = []
                keyword_parts = [w.strip() for w in keyword.split() if w.strip() and len(w) > 1]
                for part in keyword_parts[:3]:
                    tags.append(f"#{part}")

                if source:
                    tags.append(f"(출처:{source})")

                tag_str = ' '.join(tags) if tags else ""

                send_msg += f"\n\n{title}"
                if tag_str:
                    send_msg += f" {tag_str}"
                send_msg += f"\n{link}"

        return send_msg

    except Exception as e:
        debug_logger.error(f"뉴스 검색 오류 ({keyword}): {str(e)}")
        return _search_news_google_fallback(keyword, request)


def _search_news_google_fallback(keyword: str, request_func) -> str:
    """Google News RSS 폴백"""
    try:
        encode_keyword = urllib.parse.quote(keyword)
        url = f'https://news.google.com/rss/search?q={encode_keyword}&hl=ko&gl=KR&ceid=KR:ko'

        result = request_func(url, method="get", result="text")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result, 'xml')
        items = soup.find_all('item')[:5]

        if not items:
            return f"'{keyword}'에 대한 뉴스를 찾을 수 없습니다."

        send_msg = f"📰 {keyword} 뉴스 📺\n📅 {get_kst_time()} 기준"

        for item in items:
            title = item.find('title')
            link = item.find('link')
            source = item.find('source')

            title_text = title.text if title else ''
            link_text = link.text if link else ''
            source_text = source.text if source else ''

            if title_text:
                tags = []
                keyword_words = [w.strip() for w in keyword.split() if w.strip() and len(w) > 1]
                for word in keyword_words[:3]:
                    tags.append(f"#{word}")

                if source_text:
                    tags.append(f"(출처:{source_text})")

                tag_str = ' '.join(tags) if tags else ""

                send_msg += f"\n\n{title_text}"
                if tag_str:
                    send_msg += f" {tag_str}"
                send_msg += f"\n{link_text}"

        return send_msg

    except Exception as e:
        debug_logger.error(f"Google News 폴백 오류: {str(e)}")
        return f"'{keyword}' 뉴스 검색 중 오류가 발생했습니다."


def real_news(room: str, sender: str, msg: str):
    """실시간 뉴스"""
    url = 'https://news.naver.com/section/template/MOBILE_RANKING_ARTICLE'
    
    try:
        result = request(url, method="get", result="json")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 뉴스 데이터 추출
        news_list = result.get('renderedComponent', {}).get('props', {}).get('rankingArticleList', [])
        
        if not news_list:
            return "실시간 뉴스를 불러올 수 없습니다."
        
        send_msg = f"📰 실시간 인기 뉴스\n📅 {current_time} 기준\n"
        
        for idx, article in enumerate(news_list[:10], 1):
            title = article.get('title', '').strip()
            article_id = article.get('articleId', '')
            
            if title and article_id:
                # 네이버 뉴스 링크 형식
                link = f"https://n.news.naver.com/article/{article_id}"
                send_msg += f"\n{idx}. {title}\n{link}\n"
        
        return send_msg.strip()
        
    except Exception as e:
        debug_logger.error(f"실시간 뉴스 오류: {str(e)}")
        return "실시간 뉴스를 불러오는 중 오류가 발생했습니다."