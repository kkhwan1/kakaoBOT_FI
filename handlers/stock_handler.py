#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
주식/금융 핸들러 모듈
주식, 코인, 환율, 금값 등 금융 정보 처리
"""

import re
from datetime import datetime
from utils.text_utils import log
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


def stock(room: str, sender: str, msg: str):
    """주식 정보 조회 - 네이버 증권 실시간 데이터"""
    keyword = msg.replace("/주식", "").strip()
    if not keyword:
        return "📊 사용법: /주식 삼성전자"
    
    try:
        # 종목 코드 매핑 (자주 검색되는 종목들)
        stock_mapping = {
            '삼성전자': '005930', '삼전': '005930',
            'sk하이닉스': '000660', 'SK하이닉스': '000660', '하이닉스': '000660',
            'NAVER': '035420', '네이버': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220', 'LG에너지': '373220',
            '현대차': '005380', '현대자동차': '005380',
            '기아': '000270', '기아자동차': '000270',
            'SK': '034730', 'SK이노베이션': '096770', 'SK텔레콤': '017670',
            'LG화학': '051910', 'LG전자': '066570',
            '포스코': '005490', 'POSCO': '005490',
            '삼성바이오로직스': '207940', '삼성바이오': '207940',
            '셀트리온': '068270', '삼성SDI': '006400',
            '현대모비스': '012330', 'KB금융': '105560',
            '신한지주': '055550', '하나금융지주': '086790',
            '삼성생명': '032830', '삼성화재': '000810', '삼성물산': '028260'
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
        
        if stock_code:
            # 종목 상세 페이지에서 정보 추출
            detail_url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            detail_result = request(detail_url, method="get", result="bs")
            
            if detail_result:
                # 현재가
                price_elem = detail_result.select_one('p.no_today em.no_up, p.no_today em.no_down, p.no_today em')
                if not price_elem:
                    price_elem = detail_result.select_one('p.no_today')
                
                if price_elem:
                    # span 태그들을 찾아서 제대로 조합
                    price_spans = price_elem.select('span')
                    if price_spans:
                        # span 태그들의 텍스트를 조합 (중복 제거)
                        current_price = ''.join([span.get_text(strip=True) for span in price_spans[:1]])
                        if not current_price:
                            price_text = price_elem.get_text(strip=True)
                            price_numbers = re.findall(r'[\d,]+', price_text)
                            current_price = price_numbers[0] if price_numbers else "0"
                    else:
                        price_text = price_elem.get_text(strip=True)
                        # 숫자만 추출
                        price_numbers = re.findall(r'[\d,]+', price_text)
                        current_price = price_numbers[0] if price_numbers else "0"
                    
                    # 변동 정보 처리
                    trend_emoji = "📊"
                    change_info = ""
                    
                    # 전일대비
                    change_elem = detail_result.select_one('p.no_exday')
                    if change_elem:
                        # blind 클래스의 span 태그에서 실제 값 추출 (중복 방지)
                        blind_spans = change_elem.select('span.blind')
                        change_value = ""
                        change_rate = ""
                        
                        if blind_spans and len(blind_spans) >= 2:
                            change_value = blind_spans[0].get_text(strip=True)
                            change_rate = blind_spans[1].get_text(strip=True)
                        
                        # 상승/하락 판단
                        if change_elem.select_one('.ico.up'):
                            trend_emoji = "📈"
                            sign = "▲"
                        elif change_elem.select_one('.ico.down'):
                            trend_emoji = "📉"
                            sign = "▼"
                        else:
                            trend_emoji = "➡️"
                            sign = "-"
                        
                        if change_value and change_rate:
                            change_info = f"{sign} {change_value} ({change_rate}%)"
                        elif change_value:
                            change_info = f"{sign} {change_value}"
                    
                    # 추가 정보 추출
                    info_dict = {}
                    info_table = detail_result.select_one('table.no_info')
                    if info_table:
                        rows = info_table.select('tr')
                        for row in rows:
                            ths = row.select('th')
                            tds = row.select('td')
                            for i, th in enumerate(ths):
                                if i < len(tds):
                                    label = th.get_text(strip=True)
                                    value = tds[i].get_text(strip=True)
                                    if '거래량' in label:
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
                        if '거래량' in info_dict:
                            send_msg += f"📊 거래량: {info_dict['거래량']}\n"
                        if '시총' in info_dict:
                            send_msg += f"💎 시총: {info_dict['시총']}\n"
                    send_msg += f"\n⏰ {datetime.now().strftime('%m/%d %H:%M')} 기준"
                    send_msg += f"\n📈 네이버 증권"
                    
                    debug_logger.log_debug(f"주식 조회 성공: {stock_name}")
                    return send_msg
        
        return f"❌ '{keyword}' 종목을 찾을 수 없습니다.\n\n💡 정확한 종목명이나 종목코드를 입력해주세요.\n예) /주식 삼성전자, /주식 005930"
        
    except Exception as e:
        log(f"주식 조회 오류: {e}")
        return f"❌ 주식 정보 조회 중 오류가 발생했습니다.\n\n💡 다시 시도해주세요."


def coin(room: str, sender: str, msg: str):
    """코인 시세 조회"""
    url = 'https://m.stock.naver.com/front-api/crypto/v1/domesticPrice?domesticType=UPBIT&page=1&size=20'
    result = request(url, method="get", result="json")
    
    coin_list = result['result']['data']
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_msg = f"💰 암호화폐 시세 TOP 20\n📅 {current_time} 기준\n{'='*25}"
    
    for coin in coin_list:
        name = coin['currencyName']
        price = coin['closePrice']
        change_rate = coin['fluctuateRate']
        
        # 상승/하락 표시
        if float(change_rate) > 0:
            emoji = "📈"
            sign = "+"
        elif float(change_rate) < 0:
            emoji = "📉"
            sign = ""
        else:
            emoji = "➡️"
            sign = ""
        
        send_msg += f"\n{emoji} {name}: {price:,.0f}원 ({sign}{change_rate}%)"
    
    return send_msg


def exchange(room: str, sender: str, msg: str):
    """환율 정보"""
    try:
        url = 'https://finance.naver.com/marketindex/'
        result = request(url, method="get", result="bs")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"💱 환율 정보\n📅 {current_time} 기준\n{'='*25}"
        
        # 주요 통화 정보 추출
        exchange_list = result.select('ul.data_lst li')
        
        currency_info = {
            'USD': ('달러', '🇺🇸'),
            'JPY': ('엔', '🇯🇵'),
            'EUR': ('유로', '🇪🇺'),
            'CNY': ('위안', '🇨🇳')
        }
        
        for item in exchange_list[:4]:  # 상위 4개 통화
            currency_elem = item.select_one('.blind')
            value_elem = item.select_one('.value')
            change_elem = item.select_one('.change')
            
            if currency_elem and value_elem:
                currency_text = currency_elem.text.strip()
                
                # 통화 식별
                for key, (name, flag) in currency_info.items():
                    if name in currency_text:
                        value = value_elem.text.strip()
                        
                        # 변동 정보
                        if change_elem:
                            change_text = change_elem.text.strip()
                            if '상승' in change_text or '▲' in change_text:
                                trend = "📈"
                            elif '하락' in change_text or '▼' in change_text:
                                trend = "📉"
                            else:
                                trend = "➡️"
                        else:
                            trend = "➡️"
                        
                        # JPY는 100엔 기준
                        if key == 'JPY':
                            send_msg += f"\n{trend} {flag} {name}(100): {value}원"
                        else:
                            send_msg += f"\n{trend} {flag} {name}: {value}원"
                        break
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"환율 정보 오류: {str(e)}")
        return "💱 환율 정보를 불러오는 중 오류가 발생했습니다."


def gold(room: str, sender: str, msg: str):
    """금값 조회"""
    try:
        url = 'https://finance.naver.com/marketindex/goldDetail.naver'
        result = request(url, method="get", result="bs")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"🥇 금 시세\n📅 {current_time} 기준\n{'='*25}"
        
        # 국내 금 시세
        domestic_gold = result.select_one('#goldDomestic')
        if domestic_gold:
            price_elem = domestic_gold.select_one('.no_today .no')
            change_elem = domestic_gold.select_one('.no_exday')
            
            if price_elem:
                price = price_elem.text.strip()
                
                # 변동 정보
                if change_elem:
                    change_spans = change_elem.select('span')
                    if len(change_spans) >= 2:
                        change_value = change_spans[0].text.strip()
                        change_rate = change_spans[1].text.strip()
                        
                        if '상승' in str(change_elem) or 'up' in str(change_elem.get('class', [])):
                            trend = "📈"
                            sign = "▲"
                        elif '하락' in str(change_elem) or 'down' in str(change_elem.get('class', [])):
                            trend = "📉"
                            sign = "▼"
                        else:
                            trend = "➡️"
                            sign = "-"
                        
                        send_msg += f"\n{trend} 국내 금(1g): {price}원"
                        send_msg += f"\n   전일대비: {sign} {change_value} ({change_rate})"
        
        # 국제 금 시세
        international_gold = result.select_one('#goldInternational')
        if international_gold:
            price_elem = international_gold.select_one('.no_today .no')
            
            if price_elem:
                price = price_elem.text.strip()
                send_msg += f"\n\n💰 국제 금(1온스): ${price}"
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"금값 조회 오류: {str(e)}")
        return "🥇 금 시세를 불러오는 중 오류가 발생했습니다."


def stock_upper(room: str, sender: str, msg: str):
    """상한가 종목"""
    try:
        url = 'https://finance.naver.com/sise/upper.naver'
        result = request(url, method="get", result="bs")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"🚀 상한가 종목\n📅 {current_time} 기준\n{'='*25}"
        
        # 상한가 종목 테이블에서 데이터 추출
        table = result.select_one('table.type_2')
        if table:
            rows = table.select('tr')
            count = 0
            
            for row in rows:
                if count >= 10:  # 상위 10개만
                    break
                    
                cols = row.select('td')
                if len(cols) >= 4:
                    # 종목명과 현재가 추출
                    name_elem = cols[1].select_one('a')
                    price_elem = cols[2]
                    
                    if name_elem and price_elem:
                        name = name_elem.text.strip()
                        price = price_elem.text.strip()
                        
                        if name and price and price != '0':
                            count += 1
                            send_msg += f"\n{count}. {name}: {price}원"
        
        if count == 0:
            send_msg += "\n\n현재 상한가 종목이 없습니다."
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"상한가 조회 오류: {str(e)}")
        return "🚀 상한가 종목을 불러오는 중 오류가 발생했습니다."


def stock_lower(room: str, sender: str, msg: str):
    """하한가 종목"""
    try:
        url = 'https://finance.naver.com/sise/lower.naver'
        result = request(url, method="get", result="bs")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"📉 하한가 종목\n📅 {current_time} 기준\n{'='*25}"
        
        # 하한가 종목 테이블에서 데이터 추출
        table = result.select_one('table.type_2')
        if table:
            rows = table.select('tr')
            count = 0
            
            for row in rows:
                if count >= 10:  # 상위 10개만
                    break
                    
                cols = row.select('td')
                if len(cols) >= 4:
                    # 종목명과 현재가 추출
                    name_elem = cols[1].select_one('a')
                    price_elem = cols[2]
                    
                    if name_elem and price_elem:
                        name = name_elem.text.strip()
                        price = price_elem.text.strip()
                        
                        if name and price and price != '0':
                            count += 1
                            send_msg += f"\n{count}. {name}: {price}원"
        
        if count == 0:
            send_msg += "\n\n현재 하한가 종목이 없습니다."
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"하한가 조회 오류: {str(e)}")
        return "📉 하한가 종목을 불러오는 중 오류가 발생했습니다."