#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
뉴스 핸들러 모듈
뉴스 관련 명령어 처리
"""

import urllib.parse
from datetime import datetime
from utils.debug_logger import debug_logger

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
    """경제 뉴스"""
    area = 101
    url = f'https://m.news.naver.com/main?mode=LSD&sid1={area}'
    result = request(url, method="get", result="bs")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_msg = f"📰 경제 뉴스 📺\n📅 {current_time} 기준"
    for item in result.select('li.sa_item'):
        title = item.select_one('.sa_text_strong').text
        link = item.select_one('.sa_text_title').get('href')
        send_msg += f'\n\n{title}\n{link}'
    return send_msg


def it_news(room: str, sender: str, msg: str):
    """IT 뉴스"""
    area = 105
    url = f'https://m.news.naver.com/main?mode=LSD&sid1={area}'
    result = request(url, method="get", result="bs")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_msg = f"📰 IT 뉴스 📺\n📅 {current_time} 기준"
    for item in result.select('li.sa_item'):
        title = item.select_one('.sa_text_strong').text
        link = item.select_one('.sa_text_title').get('href')
        send_msg += f'\n\n{title}\n{link}'
    
    return send_msg


def realestate_news(room: str, sender: str, msg: str):
    """부동산 뉴스"""
    # 네이버 뉴스 부동산 섹션 직접 접근
    url = 'https://news.naver.com/breakingnews/section/101/260'
    
    try:
        result = request(url, method="get", result="bs")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"
        
        # 뉴스 아이템 찾기 - 여러 선택자 시도
        news_items = result.select('li.sa_item') or result.select('.sa_item')
        
        if news_items:
            for item in news_items[:10]:  # 최대 10개
                # 제목과 링크 추출
                title_elem = item.select_one('.sa_text_strong') or item.select_one('a.sa_text_title strong')
                link_elem = item.select_one('a.sa_text_title')
                
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    link = link_elem.get('href', '')
                    
                    # 링크가 상대경로인 경우 절대경로로 변환
                    if link and not link.startswith('http'):
                        link = 'https://n.news.naver.com' + link
                    
                    if title and link:
                        send_msg += f'\n\n{title}\n{link}'
        else:
            # 대체 방법: 모바일 버전 사용
            mobile_url = 'https://m.news.naver.com/rankingList?sid1=101&sid2=260'
            result = request(mobile_url, method="get", result="bs")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"
            
            news_items = result.select('li.sa_item')
            if news_items:
                for item in news_items[:10]:
                    title = item.select_one('.sa_text_strong')
                    link = item.select_one('.sa_text_title')
                    
                    if title and link:
                        send_msg += f'\n\n{title.text.strip()}\n{link.get("href")}'
            else:
                # 최후의 방법: 네이버 검색 사용
                search_url = 'https://search.naver.com/search.naver?where=news&query=부동산&sort=0&pd=1'
                result = request(search_url, method="get", result="bs")
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"
                
                news_titles = result.select('.news_tit')
                for title_elem in news_titles[:10]:
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    if title and link:
                        send_msg += f'\n\n{title}\n{link}'
        
        # 뉴스를 하나도 못 찾은 경우
        if send_msg == "🏠 부동산 뉴스 📺":
            send_msg += "\n\n현재 부동산 뉴스를 불러올 수 없습니다."
            
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"부동산 뉴스 오류: {str(e)}")
        return "🏠 부동산 뉴스를 불러오는 중 오류가 발생했습니다."


def search_news(room: str, sender: str, msg: str):
    """뉴스 검색"""
    keyword = msg.replace("/뉴스", "").strip()
    encode_keyword = urllib.parse.quote(keyword)
    url = f"https://s.search.naver.com/p/newssearch/2/search.naver?cluster_rank=69&de=&ds=&eid=&field=0&force_original=&is_dts=0&is_sug_officeid=0&mynews=0&news_office_checked=&nlu_query=&nqx_theme=%7B%22theme%22%3A%7B%22main%22%3A%7B%22name%22%3A%22corporation_hq%22%7D%2C%22sub%22%3A%5B%7B%22name%22%3A%22car_model%22%7D%2C%7B%22name%22%3A%22corporation_list%22%7D%2C%7B%22name%22%3A%22stock%22%7D%5D%7D%7D&nso=%26nso%3Dso%3Ar%2Cp%3Aall%2Ca%3Aall&nx_and_query=&nx_search_hlquery=&nx_search_query=&nx_sub_query=&office_category=0&office_section_code=0&office_type=0&pd=0&photo=0&query={encode_keyword}&query_original=&rev=31&service_area=0&sort=0&spq=0&start=31&where=news_tab_api&nso=so:r,p:all,a:all"
    
    result = request(url, method="get", result="json")
    
    news_api = result.get('contents', [])[0].get('json', {})
    articles = news_api.get('moreContents', [{}])[0].get('contents', [])
    
    if not articles:
        return f"'{keyword}'에 대한 뉴스를 찾을 수 없습니다."
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_msg = f"📰 {keyword} 뉴스 📺\n📅 {current_time} 기준"
    
    for article in articles[:10]:  # 최대 10개
        title = article.get('title', '').replace("<mark>", "").replace("</mark>", "")
        link = article.get('link', '')
        if title and link:
            send_msg += f'\n\n{title}\n{link}'
    
    return send_msg


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