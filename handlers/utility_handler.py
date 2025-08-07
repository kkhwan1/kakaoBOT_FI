#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
유틸리티 핸들러 모듈
날씨, 칼로리, 명언, 이모지, 지도 등 유틸리티 명령어 처리
"""

import random
import urllib.parse
from datetime import datetime
from utils.text_utils import log
from utils.debug_logger import debug_logger

# request 함수 import
try:
    from fn import request
except ImportError:
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


def whether(room: str, sender: str, msg: str):
    """지역별 날씨 - 실제 네이버 날씨 데이터"""
    # 대괄호 제거 및 지역명 추출
    location = msg.replace("/날씨", "").strip()
    location = location.replace("[", "").replace("]", "").strip()
    
    if not location:
        return f"{sender}님 /날씨 뒤에 지역명을 입력해주세요\n예시: /날씨 서울"
    
    try:
        encoded_location = urllib.parse.quote(location)
        url = f"https://search.naver.com/search.naver?query={encoded_location}+날씨"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        if result:
            # 지역명 확인
            location_elem = result.select_one('.title_area ._area_weather_title')
            if location_elem:
                actual_location = location_elem.get_text(strip=True)
            else:
                actual_location = location
            
            # 현재 온도
            temp_elem = result.select_one('.temperature_text')
            if temp_elem:
                temp_text = temp_elem.get_text(strip=True)
                # "현재 온도" 텍스트 제거하고 숫자만 추출
                temp = temp_text.replace('현재 온도', '').replace('°', '').strip()
            else:
                temp = "정보없음"
            
            # 날씨 상태
            weather_elem = result.select_one('.weather.before_slash')
            weather = weather_elem.get_text(strip=True) if weather_elem else "정보없음"
            
            # 체감온도
            feel_elem = result.select('.weather_info .sort dd')
            feel_temp = ""
            humidity = ""
            wind = ""
            
            for elem in feel_elem:
                text = elem.get_text(strip=True)
                if '°' in text and not feel_temp:
                    feel_temp = text
                elif '%' in text:
                    humidity = text
                elif 'm/s' in text:
                    wind = text
            
            # 미세먼지 정보
            dust_info = ""
            dust_elems = result.select('.today_chart_list .item_today')
            for dust in dust_elems:
                title = dust.select_one('.title')
                value = dust.select_one('.txt')
                if title and value:
                    dust_name = title.get_text(strip=True)
                    dust_value = value.get_text(strip=True)
                    dust_info += f"{dust_name}: {dust_value}  "
            
            # 오늘의 최저/최고 기온
            min_max_elem = result.select('.temperature_inner')
            min_temp = ""
            max_temp = ""
            for elem in min_max_elem:
                min_elem = elem.select_one('.lowest')
                max_elem = elem.select_one('.highest')
                if min_elem:
                    min_temp = min_elem.get_text(strip=True).replace('최저기온', '').strip()
                if max_elem:
                    max_temp = max_elem.get_text(strip=True).replace('최고기온', '').strip()
            
            # 결과 메시지 구성
            send_msg = f"🌤️ {actual_location} 날씨\n"
            send_msg += f"{'='*25}\n"
            send_msg += f"🌡️ 현재: {temp}°C ({weather})\n"
            
            if feel_temp:
                send_msg += f"🤔 체감: {feel_temp}\n"
            
            if min_temp or max_temp:
                temp_range = []
                if min_temp:
                    temp_range.append(f"최저 {min_temp}")
                if max_temp:
                    temp_range.append(f"최고 {max_temp}")
                if temp_range:
                    send_msg += f"📊 {' / '.join(temp_range)}\n"
            
            if humidity:
                send_msg += f"💧 습도: {humidity}\n"
            
            if wind:
                send_msg += f"💨 바람: {wind}\n"
            
            if dust_info:
                send_msg += f"\n🌫️ {dust_info}"
            
            send_msg += f"\n\n⏰ {datetime.now().strftime('%m/%d %H:%M')} 기준"
            
            return send_msg
        
        return f"❌ {location}의 날씨 정보를 찾을 수 없습니다."
        
    except Exception as e:
        log(f"날씨 조회 오류: {e}")
        return f"날씨 정보를 가져오는 중 오류가 발생했습니다."


def whether_today(room: str, sender: str, msg: str):
    """오늘의 날씨 예보"""
    try:
        url = f"https://www.weather.go.kr/w/weather/forecast/short-term.do"
        result = request(url, method="get", result="bs")
        
        dt = result.select_one('.cmp-view-announce > span').get_text()[6:-2].replace('월 ','/').replace(' ','').replace('요일',' ').replace('일', '')
        spans = result.select(".summary > span")

        raw_msg = ''
        for span in spans:
            depth = span['class'][0][-1]
            space = " " * (int(depth) * 1)
            text = span.get_text(separator="\n").replace('\n\n', '\n').replace('  ',' ').strip()
            raw_msg += f'\n{space}{text}'
        
        send_msg = f"📅 {dt} 날씨 예보\n{'='*25}{raw_msg}"
        
        return send_msg
        
    except Exception as e:
        log(f"날씨 예보 오류: {e}")
        return "날씨 예보를 가져오는 중 오류가 발생했습니다."


def calorie(room: str, sender: str, msg: str):
    """칼로리 정보 - 네이버 검색 실제 데이터"""
    food = msg.replace("/칼로리", "").strip()
    if not food:
        return f"{sender}님 /칼로리 뒤에 음식명을 입력해주세요"
    
    try:
        # 네이버에서 칼로리 정보 검색
        encoded_food = urllib.parse.quote(f"{food} 칼로리")
        url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={encoded_food}"
        
        result = request(url, method="get", result="bs")
        
        if result:
            # 칼로리 정보 찾기 (네이버 지식백과 또는 영양정보)
            calorie_info = None
            calorie_value = None
            serving_size = None
            
            # 네이버 칼로리 정보 박스 찾기
            nutrition_box = result.select_one('.nutrition_info') or result.select_one('.food_info')
            if nutrition_box:
                kcal_elem = nutrition_box.select_one('.kcal') or nutrition_box.select_one('.calorie')
                if kcal_elem:
                    calorie_value = kcal_elem.get_text(strip=True)
                
                serving_elem = nutrition_box.select_one('.serving') or nutrition_box.select_one('.amount')
                if serving_elem:
                    serving_size = serving_elem.get_text(strip=True)
            
            # 대체 방법: 지식백과나 일반 검색 결과에서 찾기
            if not calorie_value:
                # 검색 결과에서 칼로리 패턴 찾기
                import re
                text_content = result.get_text()
                # "100g당 XXXkcal" 또는 "XXXkcal" 패턴 찾기
                calorie_patterns = [
                    r'(\d+\.?\d*)\s*kcal',
                    r'(\d+\.?\d*)\s*칼로리',
                    r'열량\s*:\s*(\d+\.?\d*)',
                ]
                
                for pattern in calorie_patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        calorie_value = f"{match.group(1)}kcal"
                        break
                
                # 제공량 찾기
                serving_patterns = [
                    r'(\d+g)당',
                    r'1인분\s*\((\d+g)\)',
                    r'(\d+ml)당',
                ]
                
                for pattern in serving_patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        serving_size = match.group(1)
                        break
            
            # 결과 메시지 생성
            if calorie_value:
                send_msg = f"🍽️ {food} 칼로리 정보\n"
                send_msg += f"{'='*25}\n"
                
                if serving_size:
                    send_msg += f"📊 {serving_size}당: {calorie_value}\n"
                else:
                    send_msg += f"📊 칼로리: {calorie_value}\n"
                
                # 운동 칼로리 소모 정보 추가
                try:
                    cal_num = float(re.search(r'(\d+\.?\d*)', calorie_value).group(1))
                    if cal_num > 0:
                        walking_min = int(cal_num / 3.5)  # 걷기: 분당 약 3.5kcal
                        running_min = int(cal_num / 10)   # 달리기: 분당 약 10kcal
                        
                        send_msg += f"\n🏃 운동으로 소모하려면:\n"
                        send_msg += f"• 걷기: 약 {walking_min}분\n"
                        send_msg += f"• 달리기: 약 {running_min}분"
                except:
                    pass
                
                return send_msg
            else:
                # 기본 칼로리 데이터베이스
                calorie_db = {
                    '밥': '210kcal (1공기 150g)',
                    '라면': '500kcal (1봉지)',
                    '김밥': '450kcal (1줄)',
                    '떡볶이': '300kcal (1인분)',
                    '치킨': '1700kcal (1마리)',
                    '피자': '250kcal (1조각)',
                    '햄버거': '500kcal (1개)',
                    '김치찌개': '120kcal (1인분)',
                    '삼겹살': '330kcal (100g)',
                    '아이스크림': '200kcal (1개)',
                }
                
                for food_name, cal_info in calorie_db.items():
                    if food_name in food:
                        return f"🍽️ {food} 칼로리 정보\n{'='*25}\n📊 {cal_info}"
                
                return f"❌ {food}의 칼로리 정보를 찾을 수 없습니다.\n\n💡 다른 음식명으로 검색해보세요."
        
        return f"❌ {food}의 칼로리 정보를 찾을 수 없습니다."
        
    except Exception as e:
        log(f"칼로리 조회 오류: {e}")
        return "칼로리 정보를 가져오는 중 오류가 발생했습니다."


def wise_saying(room: str, sender: str, msg: str):
    """명언"""
    wise_sayings = [
        "성공은 준비된 사람에게 기회가 왔을 때 만들어진다. - 헨리 포드",
        "꿈을 꾸지 않으면 이루어질 수 없다. - 월트 디즈니",
        "가장 큰 영광은 넘어지지 않는 것이 아니라 넘어질 때마다 일어나는 것이다. - 넬슨 만델라",
        "성공의 비밀은 시작하는 것이다. - 마크 트웨인",
        "오늘이 인생의 첫날이라고 생각하라. - 아베 링컨",
        "불가능이란 어리석은 자들의 사전에만 있는 단어다. - 나폴레옹",
        "인생은 자전거를 타는 것과 같다. 균형을 유지하려면 움직여야 한다. - 아인슈타인",
        "행복은 습관이다. 그것을 몸에 지니라. - 허버드",
        "미래는 준비하는 사람의 것이다. - 말콤 X",
        "할 수 있다고 믿든 할 수 없다고 믿든 당신이 옳다. - 헨리 포드"
    ]
    
    return f"✨ 오늘의 명언\n\n{random.choice(wise_sayings)}"


def emoji(room: str, sender: str, msg: str):
    """이모지 검색"""
    keyword = msg.replace("/이모지", "").strip()
    if not keyword:
        return f"{sender}님 /이모지 뒤에 키워드를 입력해주세요🙏"

    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.emojiall.com/ko/search_results?keywords={encoded_keyword}"
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    result = request(url, method="get", result="bs", headers=headers)

    emojis = result.select('.emoji_card_content .col-auto .emoji_font')
    if not emojis:
        send_msg = f"{keyword} 이모지가 없어요😥"
    else:
        rand_emoji = emojis[random.randint(0, len(emojis)-1)].get_text()
        send_msg = f"{rand_emoji} {keyword} 이모지 {rand_emoji} \n"
        for i, emoji in enumerate(emojis):
            send_msg += f"{emoji.get_text()}"
            if (i + 1) % 10 == 0:
                send_msg += "\n"
    return send_msg


def naver_map(room: str, sender: str, msg: str):
    """네이버 지도 검색"""
    keyword = msg.replace("/맵", "").replace("/지도", "").replace("맛집", "").strip()
    if not keyword:
        return f"{sender}님 검색할 장소를 입력해주세요"
    
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        map_url = f"https://m.map.naver.com/search2/search.naver?query={encoded_keyword}"
        
        return f"🗺️ {keyword} 지도 검색\n\n📍 {map_url}"
    except Exception as e:
        log(f"지도 검색 오류: {e}")
        return "지도 검색 중 오류가 발생했습니다"