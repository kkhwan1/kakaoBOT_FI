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


# 광고 필터링 키워드
AD_KEYWORDS = [
    '광고', 'AD', 'ad', '赞助', '広告', 'advert',
    '유료', '협찬', '소개', '홍보', '기획기사',
    '포장기사', '선정', 'Pick', 'PICK'
]


def _scrape_naver_section(section_url: str, display_name: str, emoji: str, use_mobile: bool = False) -> str:
    """
    네이버 섹션 페이지에서 뉴스 스크래핑 (광고 제거 필터 포함)

    Args:
        section_url: 네이버 섹션 URL
        display_name: 표시 이름
        emoji: 카테고리 이모지
        use_mobile: 모바일 페이지 사용 여부
    """
    import re

    try:
        result = request(section_url, method="get", result="bs")
        current_time = get_kst_time()

        send_msg = f"{emoji} {display_name} 뉴스 📺\n📅 {current_time} 기준"

        # 모바일 페이지인 경우
        if use_mobile:
            # 헤드라인 뉴스만 선택 (is_blind 제외)
            news_items = result.select('li.sa_item._SECTION_HEADLINE:not(.is_blind)')
            if not news_items:
                # 폴백: 기존 셀렉터
                news_items = result.select('li.sa_item')

            if not news_items:
                # 랭킹 페이지인 경우 직접 article 링크 사용
                all_links = result.select('a[href*="article"]')

                # 중복 제거하고 상위 10개만
                seen = set()
                for link in all_links:
                    href = link.get('href', '')
                    if href and href not in seen:
                        seen.add(href)
                        # 링크 바로 사용
                        news_items = list(all_links)[:10]
                        break

            if not news_items:
                return f"{emoji} {display_name} 뉴스를 불러올 수 없습니다."

            # 상위 10개 (광고 제외)
            count = 0
            for item in news_items:
                if count >= 10:
                    break

                # li 요소인 경우
                source = ""
                if item.name == 'li':
                    title_elem = item.select_one('.sa_text_strong')
                    link_elem = item.select_one('.sa_text_title')
                    source_elem = item.select_one('.sa_text_press')
                    if not title_elem:
                        title_elem = item.select_one('.sa_text_title')
                else:
                    # a 요소 직접 사용 (랭킹 페이지)
                    link_elem = item
                    title_elem = item

                if not link_elem:
                    continue

                title = title_elem.text.strip() if title_elem else ''
                link = link_elem.get('href', '')
                source = source_elem.text.strip() if source_elem else ''

                # 출처에서 "언론사 선정", "기자" 등 텍스트 제거
                if source:
                    source = source.replace('언론사 선정', '').replace('기자', '').strip()

                if not title or not link:
                    continue

                # 광고 필터링
                is_ad = False
                title_lower = title.lower()
                link_lower = link.lower()
                for ad_keyword in AD_KEYWORDS:
                    if ad_keyword.lower() in title_lower or ad_keyword.lower() in link_lower:
                        is_ad = True
                        break

                if is_ad:
                    continue

                # 해시태그 생성
                tags = []
                words = re.findall(r'[가-힣]{2,}', title)
                unique_words = list(dict.fromkeys(words))[:3]
                for word in unique_words:
                    tags.append(f"#{word}")
                tag_str = ' '.join(tags) if tags else ""

                # 제목과 출처, URL 포맷
                if source:
                    send_msg += f"\n\n{title} ({source})"
                else:
                    send_msg += f"\n\n{title}"
                send_msg += f"\n{tag_str}\n{link}"
                count += 1

            if count == 0:
                return f"{emoji} {display_name} 뉴스를 불러올 수 없습니다."

            return send_msg

        # 데스크톱 페이지인 경우
        # 메인 랭킹 뉴스 컨테이너 찾기
        main_ranking = result.select_one('.rankingnews.as_type_flat._SECTION_MAINNEWS')

        if main_ranking:
            news_items = main_ranking.select('li')
        else:
            # 폴백: 모든 rankingnews에서 가져오기
            all_ranking = result.select('.rankingnews li')
            news_items = all_ranking

        # 상위 10개 (광고 제외)
        count = 0
        for item in news_items:
            if count >= 10:
                break

            # article 링크가 있는 a 태그 찾기
            link_elem = item.select_one('a[href*="article"]')
            if not link_elem:
                continue

            title = link_elem.text.strip()
            link = link_elem.get('href', '')

            # 출처 추출 시도
            source_elem = item.select_one('.rankingnews_press')
            source = source_elem.text.strip() if source_elem else ''
            if source:
                source = source.replace('언론사 선정', '').replace('기자', '').strip()

            if not title or not link:
                continue

            # 광고 필터링
            is_ad = False
            title_lower = title.lower()
            link_lower = link.lower()
            for ad_keyword in AD_KEYWORDS:
                if ad_keyword.lower() in title_lower or ad_keyword.lower() in link_lower:
                    is_ad = True
                    break

            if is_ad:
                continue

            # 해시태그 생성
            tags = []
            words = re.findall(r'[가-힣]{2,}', title)
            unique_words = list(dict.fromkeys(words))[:3]
            for word in unique_words:
                tags.append(f"#{word}")
            tag_str = ' '.join(tags) if tags else ""

            # 제목과 출처, URL 포맷
            if source:
                send_msg += f"\n\n{title} ({source})"
            else:
                send_msg += f"\n\n{title}"
            send_msg += f"\n{tag_str}\n{link}"
            count += 1

        if count == 0:
            return f"{emoji} {display_name} 뉴스를 불러올 수 없습니다."

        return send_msg

    except Exception as e:
        debug_logger.error(f"{display_name} 스크래핑 오류: {str(e)}")
        return f"{emoji} {display_name} 뉴스를 불러오는 중 오류가 발생했습니다."


def economy_news(room: str, sender: str, msg: str):
    """경제 뉴스 - 스크래핑 방식 (모바일)"""
    return _scrape_naver_section(
        "https://m.news.naver.com/main?mode=LSD&sid1=101",
        "경제",
        "💰",
        use_mobile=True
    )


def it_news(room: str, sender: str, msg: str):
    """IT 뉴스 - 스크래핑 방식 (모바일)"""
    return _scrape_naver_section(
        "https://m.news.naver.com/main?mode=LSD&sid1=105",
        "IT",
        "💻",
        use_mobile=True
    )


def realestate_news(room: str, sender: str, msg: str):
    """부동산 뉴스 - 네이버 부동산 섹션 직접 스크래핑"""
    import re

    try:
        # 부동산 전용 섹션 URL (breakingnews)
        url = "https://news.naver.com/breakingnews/section/101/260"
        result = request(url, method="get", result="bs")
        current_time = get_kst_time()

        send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"

        # 부동산 섹션의 뉴스 아이템 가져오기
        news_items = result.select('li.sa_item')

        if not news_items:
            return f"🏠 부동산 뉴스를 불러올 수 없습니다."

        # 상위 10개 기사 추출
        count = 0
        seen = set()
        ad_keywords_lower = [k.lower() for k in AD_KEYWORDS]

        for item in news_items:
            if count >= 10:
                break

            # 제목과 링크 추출
            title_elem = item.select_one('.sa_text_strong')
            link_elem = item.select_one('a[href*="article"]')
            source_elem = item.select_one('.sa_text_press, .sa_text_info_left')

            if not link_elem:
                continue

            # 제목이 없으면 링크 텍스트 사용
            if title_elem:
                title = title_elem.text.strip()
            else:
                title = link_elem.text.strip()

            link = link_elem.get('href', '')

            if not title or not link or link in seen:
                continue

            # 광고 필터링
            is_ad = False
            title_lower = title.lower()
            for ad_keyword in ad_keywords_lower:
                if ad_keyword in title_lower:
                    is_ad = True
                    break
            if is_ad:
                continue

            seen.add(link)

            # 출처 추출 및 정리
            source = ''
            if source_elem:
                source = source_elem.text.strip()
                # 시간 정보 제거 (예: "조선일보\n25분전" -> "조선일보")
                source = source.split('\n')[0].strip()
                source = source.replace('언론사 선정', '').replace('기자', '').strip()

            # 해시태그 생성
            tags = []
            words = re.findall(r'[가-힣]{2,}', title)
            unique_words = list(dict.fromkeys(words))[:3]
            for word in unique_words:
                tags.append(f"#{word}")
            tag_str = ' '.join(tags) if tags else ""

            # 메시지 구성
            if source:
                send_msg += f"\n\n{title} ({source})"
            else:
                send_msg += f"\n\n{title}"
            send_msg += f"\n{tag_str}\n{link}"
            count += 1

        if count == 0:
            return f"🏠 부동산 뉴스를 불러올 수 없습니다."

        return send_msg

    except Exception as e:
        debug_logger.error(f"부동산 뉴스 스크래핑 오류: {str(e)}")
        return f"🏠 부동산 뉴스를 불러오는 중 오류가 발생했습니다."


def world_news(room: str, sender: str, msg: str):
    """세계 뉴스 - 스크래핑 방식 (모바일)"""
    return _scrape_naver_section(
        "https://m.news.naver.com/main?mode=LSD&sid1=104",
        "세계",
        "🌍",
        use_mobile=True
    )


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

        for item in items[:10]:
            title = item.get('title', '')
            link = item.get('originallink') or item.get('link', '')
            source = item.get('source', '')

            # HTML 태그 및 특수 문자 제거
            title = re.sub(r'<[^>]+>', '', title)
            title = title.replace('&quot;', '"').replace('&apos;', "'")
            title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

            # 해시태그 생성 (제목에서 키워드 추출)
            tags = []
            words = re.findall(r'[가-힣]{2,}', title)
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

            # 메시지 구성: 제목(출처) 형식
            if source:
                news_item = f"\n\n{title}({source})"
            else:
                news_item = f"\n\n{title}"

            news_item += f"\n{tag_str}\n{link}"

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

        # 헤드라인 뉴스만 선택 (is_blind 제외)
        news_items = result.select('li.sa_item._SECTION_HEADLINE:not(.is_blind)')
        if not news_items:
            # 폴백: 기존 셀렉터
            news_items = result.select('li.sa_item')
        if not news_items:
            return f"{emoji} {display_name} 뉴스를 불러올 수 없습니다."

        for item in news_items[:10]:
            title_elem = item.select_one('.sa_text_strong')
            link_elem = item.select_one('.sa_text_title')

            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem.get('href', '')
                send_msg += f'\n\n{title}\n{link}'

        return send_msg

    except Exception as e:
        debug_logger.error(f"{display_name} 뉴스 폴백 오류: {str(e)}")
        return f"{emoji} {display_name} 뉴스를 불러오는 중 오류가 발생했습니다."


