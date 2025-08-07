#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
개선된 주식 정보 조회 함수
네이버 증권에서 직접 검색하여 실시간 데이터 제공
"""

import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def stock_improved(room: str, sender: str, msg: str):
    """개선된 주식 정보 조회 - 네이버 증권 실시간 데이터"""
    
    keyword = msg.replace("/주식", "").strip()
    if not keyword:
        return "📊 사용법: /주식 삼성전자"
    
    try:
        # 종목 코드 매핑 (자주 검색되는 종목들)
        stock_mapping = {
            '삼성전자': '005930',
            '삼전': '005930',
            'sk하이닉스': '000660',
            'SK하이닉스': '000660',
            '하이닉스': '000660',
            'NAVER': '035420',
            '네이버': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220',
            'LG에너지': '373220',
            '현대차': '005380',
            '현대자동차': '005380',
            '기아': '000270',
            '기아자동차': '000270',
            'SK': '034730',
            'SK이노베이션': '096770',
            'SK텔레콤': '017670',
            'LG화학': '051910',
            'LG전자': '066570',
            '포스코': '005490',
            'POSCO': '005490',
            '삼성바이오로직스': '207940',
            '삼성바이오': '207940',
            '셀트리온': '068270',
            '삼성SDI': '006400',
            '현대모비스': '012330',
            'KB금융': '105560',
            '신한지주': '055550',
            '하나금융지주': '086790',
            '삼성생명': '032830',
            '삼성화재': '000810',
            '삼성물산': '028260',
            'CJ제일제당': '097950',
            'CJ': '097950',
            '롯데케미칼': '011170',
            '한국전력': '015760',
            '한전': '015760',
            'KT': '030200',
            'KT&G': '033780',
            '대한항공': '003490',
            '아시아나항공': '020560',
            '아시아나': '020560',
            '제주항공': '089590'
        }
        
        # 종목 코드 확인
        stock_code = None
        stock_name = keyword
        
        # 입력이 종목 코드인지 확인 (6자리 숫자)
        if keyword.isdigit() and len(keyword) == 6:
            stock_code = keyword
            stock_name = keyword
        # 매핑된 종목명인지 확인
        elif keyword in stock_mapping:
            stock_code = stock_mapping[keyword]
            stock_name = keyword
        # 대소문자 구분 없이 매핑 확인
        else:
            for key, value in stock_mapping.items():
                if key.lower() == keyword.lower():
                    stock_code = value
                    stock_name = key
                    break
        
        # 종목 코드를 찾지 못한 경우 네이버 검색 시도
        if not stock_code:
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://finance.naver.com/search/searchList.naver?query={encoded_keyword}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            try:
                response = requests.get(search_url, headers=headers, timeout=5)
                response.encoding = 'euc-kr'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 검색 결과에서 첫 번째 종목 찾기
                first_result = soup.select_one('td.tit a')
                if first_result and 'code=' in first_result.get('href', ''):
                    href = first_result.get('href', '')
                    stock_code = href.split('code=')[1].split('&')[0]
                    stock_name = first_result.get_text(strip=True)
            except:
                pass
        
        if not stock_code:
            return f"❌ '{keyword}' 종목을 찾을 수 없습니다.\n\n💡 정확한 종목명이나 종목코드를 입력해주세요.\n예) /주식 삼성전자, /주식 005930"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        # 종목 상세 페이지에서 정보 추출
        detail_url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
        detail_response = requests.get(detail_url, headers=headers)
        detail_response.encoding = 'euc-kr'
        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
        
        # 현재가 정보 추출
        price_elem = detail_soup.select_one('p.no_today')
        
        if not price_elem:
            return f"❌ {stock_name}({stock_code}) 가격 정보를 가져올 수 없습니다."
        
        # 가격 정보 파싱 - span.blind 내의 텍스트를 먼저 찾기
        blind_elem = price_elem.select_one('span.blind')
        if blind_elem:
            price_text = blind_elem.get_text(strip=True)
        else:
            # span.blind가 없으면 em 태그나 첫 번째 텍스트 노드 사용
            em_elem = price_elem.select_one('em')
            if em_elem:
                price_text = em_elem.get_text(strip=True)
            else:
                price_text = price_elem.get_text(strip=True)
        
        # 숫자만 추출 (첫 번째 숫자만 사용)
        price_numbers = re.findall(r'[\d,]+', price_text)
        if price_numbers:
            current_price = price_numbers[0]
        else:
            current_price = "0"
        
        # 전일 대비 정보
        change_elem = detail_soup.select_one('p.no_exday')
        change_info = ""
        trend_emoji = "📊"
        
        if change_elem:
            # span 태그들을 개별적으로 추출
            spans = change_elem.select('span')
            change_values = []
            
            for span in spans:
                text = span.get_text(strip=True)
                # 숫자가 포함된 텍스트만 추출
                if re.search(r'\d', text):
                    # 숫자와 기호만 추출
                    numbers = re.findall(r'[\d,]+\.?\d*', text)
                    if numbers:
                        change_values.extend(numbers)
            
            # 상승/하락 판단
            if detail_soup.select_one('.ico.up') or '상승' in change_elem.get_text():
                trend_emoji = "📈"
                sign = "▲"
            elif detail_soup.select_one('.ico.down') or '하락' in change_elem.get_text():
                trend_emoji = "📉"
                sign = "▼"
            else:
                trend_emoji = "➡️"
                sign = "-"
            
            # 중복 제거 후 변동값과 변동률 설정
            if len(change_values) >= 2:
                change_value = change_values[0]
                change_rate = change_values[1]
                change_info = f"{sign} {change_value} ({change_rate}%)"
            elif len(change_values) == 1:
                change_info = f"{sign} {change_values[0]}"
        
        # 추가 정보 추출
        info_dict = {}
        
        # 시가, 고가, 저가, 거래량 추출
        info_table = detail_soup.select_one('table.no_info')
        if info_table:
            rows = info_table.select('tr')
            for row in rows:
                ths = row.select('th')
                tds = row.select('td')
                
                for i, th in enumerate(ths):
                    if i < len(tds):
                        label = th.get_text(strip=True)
                        value = tds[i].get_text(strip=True)
                        
                        if '시가' in label:
                            info_dict['시가'] = value
                        elif '고가' in label:
                            info_dict['고가'] = value
                        elif '저가' in label:
                            info_dict['저가'] = value
                        elif '거래량' in label:
                            info_dict['거래량'] = value
                        elif '시가총액' in label:
                            info_dict['시총'] = value
        
        # 결과 메시지 생성
        send_msg = f"{trend_emoji} {stock_name} ({stock_code})\n"
        send_msg += f"{'='*25}\n"
        send_msg += f"💰 현재가: {current_price}원\n"
        
        if change_info:
            send_msg += f"📊 전일대비: {change_info}\n"
        
        if info_dict:
            send_msg += f"\n"
            if '시가' in info_dict:
                send_msg += f"🔵 시가: {info_dict['시가']}\n"
            if '고가' in info_dict:
                send_msg += f"🔴 고가: {info_dict['고가']}\n"
            if '저가' in info_dict:
                send_msg += f"🔵 저가: {info_dict['저가']}\n"
            if '거래량' in info_dict:
                send_msg += f"📊 거래량: {info_dict['거래량']}\n"
            if '시총' in info_dict:
                send_msg += f"💎 시총: {info_dict['시총']}\n"
        
        send_msg += f"\n⏰ {datetime.now().strftime('%m/%d %H:%M')} 기준"
        send_msg += f"\n📈 네이버 증권"
        
        return send_msg
        
    except Exception as e:
        print(f"주식 조회 오류: {e}")
        return f"❌ 주식 정보 조회 중 오류가 발생했습니다.\n\n💡 다시 시도해주세요."

# 테스트
if __name__ == "__main__":
    # 다양한 종목 테스트
    test_stocks = ["삼성전자", "SK하이닉스", "NAVER", "카카오", "005930"]
    
    for stock_name in test_stocks:
        print(f"\n{'='*50}")
        result = stock_improved("테스트", "테스터", f"/주식 {stock_name}")
        print(result)