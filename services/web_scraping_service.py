#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
웹 스크래핑 서비스 모듈
웹 페이지 데이터 추출 및 파싱 담당
"""

import re
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from services.http_service import request, fetch_html
from utils.debug_logger import debug_logger


class WebScrapingService:
    """
    웹 스크래핑 서비스 클래스
    다양한 웹사이트에서 데이터 추출
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
        }
    
    def get_naver_news(self, category: int) -> List[Dict[str, str]]:
        """
        네이버 뉴스 크롤링
        
        Args:
            category: 뉴스 카테고리 코드 (101: 경제, 105: IT 등)
        
        Returns:
            List[Dict]: 뉴스 목록 (title, link)
        """
        try:
            url = f'https://m.news.naver.com/main?mode=LSD&sid1={category}'
            soup = fetch_html(url, headers=self.headers)
            
            if not soup:
                return []
            
            news_list = []
            for item in soup.select('li.sa_item')[:10]:
                title_elem = item.select_one('.sa_text_strong')
                link_elem = item.select_one('.sa_text_title')
                
                if title_elem and link_elem:
                    news_list.append({
                        'title': title_elem.text.strip(),
                        'link': link_elem.get('href', '')
                    })
            
            return news_list
            
        except Exception as e:
            debug_logger.error(f"네이버 뉴스 크롤링 오류: {e}")
            return []
    
    def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """
        주식 가격 정보 크롤링
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            Dict: 주식 정보 (price, change, rate 등)
        """
        try:
            url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            soup = fetch_html(url, headers=self.headers)
            
            if not soup:
                return {}
            
            stock_info = {}
            
            # 현재가
            price_elem = soup.select_one('p.no_today em.no_up, p.no_today em.no_down, p.no_today em')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                stock_info['price'] = re.sub(r'[^\d,]', '', price_text)
            
            # 전일대비
            change_elem = soup.select_one('p.no_exday')
            if change_elem:
                blind_spans = change_elem.select('span.blind')
                if len(blind_spans) >= 2:
                    stock_info['change'] = blind_spans[0].get_text(strip=True)
                    stock_info['change_rate'] = blind_spans[1].get_text(strip=True)
                
                # 상승/하락 판단
                if change_elem.select_one('.ico.up'):
                    stock_info['trend'] = 'up'
                elif change_elem.select_one('.ico.down'):
                    stock_info['trend'] = 'down'
                else:
                    stock_info['trend'] = 'same'
            
            # 거래량, 시가총액
            info_table = soup.select_one('table.no_info')
            if info_table:
                for row in info_table.select('tr'):
                    ths = row.select('th')
                    tds = row.select('td')
                    for i, th in enumerate(ths):
                        if i < len(tds):
                            label = th.get_text(strip=True)
                            value = tds[i].get_text(strip=True)
                            if '거래량' in label:
                                stock_info['volume'] = value
                            elif '시가총액' in label:
                                stock_info['market_cap'] = value
            
            return stock_info
            
        except Exception as e:
            debug_logger.error(f"주식 정보 크롤링 오류: {e}")
            return {}
    
    def get_weather_info(self, location: str) -> Dict[str, Any]:
        """
        날씨 정보 크롤링
        
        Args:
            location: 지역명
        
        Returns:
            Dict: 날씨 정보
        """
        try:
            import urllib.parse
            encoded_location = urllib.parse.quote(f"{location} 날씨")
            url = f"https://search.naver.com/search.naver?query={encoded_location}"
            
            soup = fetch_html(url, headers=self.headers)
            
            if not soup:
                return {}
            
            weather_info = {}
            
            # 현재 온도
            temp_elem = soup.select_one('.temperature_text')
            if temp_elem:
                temp_text = temp_elem.get_text(strip=True)
                weather_info['temperature'] = temp_text.replace('현재 온도', '').replace('°', '').strip()
            
            # 날씨 상태
            weather_elem = soup.select_one('.weather.before_slash')
            if weather_elem:
                weather_info['status'] = weather_elem.get_text(strip=True)
            
            # 체감온도, 습도, 바람
            weather_details = soup.select('.weather_info .sort dd')
            for elem in weather_details:
                text = elem.get_text(strip=True)
                if '°' in text and 'feels_like' not in weather_info:
                    weather_info['feels_like'] = text
                elif '%' in text:
                    weather_info['humidity'] = text
                elif 'm/s' in text:
                    weather_info['wind'] = text
            
            # 미세먼지
            dust_info = []
            dust_elems = soup.select('.today_chart_list .item_today')
            for dust in dust_elems:
                title = dust.select_one('.title')
                value = dust.select_one('.txt')
                if title and value:
                    dust_info.append({
                        'type': title.get_text(strip=True),
                        'value': value.get_text(strip=True)
                    })
            
            if dust_info:
                weather_info['dust'] = dust_info
            
            return weather_info
            
        except Exception as e:
            debug_logger.error(f"날씨 정보 크롤링 오류: {e}")
            return {}
    
    def get_youtube_trending(self) -> List[Dict[str, str]]:
        """
        YouTube 인기 동영상 크롤링
        
        Returns:
            List[Dict]: 동영상 목록 (title, video_id)
        """
        try:
            url = 'https://www.youtube.com/feed/trending'
            response = request(url, headers={'Accept-Language': 'ko-KR,ko;q=0.9'})
            
            if not response:
                return []
            
            # 간단한 정규식으로 비디오 정보 추출
            video_pattern = r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"'
            videos = re.findall(video_pattern, response)[:10]
            
            video_list = []
            for video_id, title in videos:
                # HTML 엔티티 디코딩
                title = title.replace('\\u0026', '&').replace('\\u003c', '<').replace('\\u003e', '>')
                video_list.append({
                    'title': title,
                    'video_id': video_id,
                    'url': f"https://youtu.be/{video_id}"
                })
            
            return video_list
            
        except Exception as e:
            debug_logger.error(f"YouTube 트렌딩 크롤링 오류: {e}")
            return []
    
    def get_lotto_result(self) -> Dict[str, Any]:
        """
        로또 당첨번호 크롤링
        
        Returns:
            Dict: 로또 정보 (round, date, numbers, bonus, prize)
        """
        try:
            url = "https://search.naver.com/search.naver?query=로또"
            soup = fetch_html(url, headers=self.headers)
            
            if not soup:
                return {}
            
            lotto_info = {}
            
            # 회차 정보
            round_elem = soup.select_one('.win_number_date')
            if round_elem:
                text = round_elem.get_text()
                round_match = re.search(r'(\d+)회', text)
                date_match = re.search(r'\(([^)]+)\)', text)
                if round_match:
                    lotto_info['round'] = round_match.group(1)
                if date_match:
                    lotto_info['date'] = date_match.group(1)
            
            # 당첨번호
            numbers = []
            number_elems = soup.select('.win_number_box .win_ball')
            for elem in number_elems[:6]:
                num_text = elem.get_text(strip=True)
                if num_text.isdigit():
                    numbers.append(num_text)
            
            if numbers:
                lotto_info['numbers'] = numbers
            
            # 보너스 번호
            bonus_elem = soup.select_one('.win_number_box .bonus_ball')
            if bonus_elem:
                lotto_info['bonus'] = bonus_elem.get_text(strip=True)
            
            # 1등 당첨금
            prize_elem = soup.select_one('.win_prize_money')
            if prize_elem:
                lotto_info['prize'] = prize_elem.get_text(strip=True)
            
            return lotto_info
            
        except Exception as e:
            debug_logger.error(f"로또 정보 크롤링 오류: {e}")
            return {}


# 싱글톤 인스턴스
web_scraping_service = WebScrapingService()