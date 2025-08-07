#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
게임 핸들러 모듈
로또, 운세, LOL 전적 등 게임/엔터테인먼트 관련 명령어 처리
"""

import re
import random
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


def lotto(room: str, sender: str, msg: str):
    """로또 번호 생성"""
    try:
        count = 1
        if "로또" in msg:
            parts = msg.split()
            for part in parts:
                if part.isdigit() and 1 <= int(part) <= 5:
                    count = int(part)
                    break
        
        send_msg = f"🍀 행운의 로또 번호 {count}게임\n\n"
        for i in range(count):
            numbers = sorted(random.sample(range(1, 46), 6))
            send_msg += f"🎱 {' - '.join(map(str, numbers))}\n"
        
        send_msg += "\n🌟 행운을 빕니다!"
        return send_msg
    except Exception as e:
        log(f"로또 생성 오류: {e}")
        return "로또 번호를 생성하는 중 오류가 발생했습니다"


def lotto_result(room: str, sender: str, msg: str):
    """로또 당첨번호 조회 - 웹 크롤링"""
    try:
        # 네이버 로또 페이지 크롤링
        url = "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EB%A1%9C%EB%98%90"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        
        if result:
            # 회차 정보
            round_elem = result.select_one('.win_number_date')
            round_num = ""
            date_str = ""
            if round_elem:
                text = round_elem.get_text()
                round_match = re.search(r'(\d+)회', text)
                date_match = re.search(r'\(([^)]+)\)', text)
                if round_match:
                    round_num = round_match.group(1)
                if date_match:
                    date_str = date_match.group(1)
            
            # 당첨번호
            win_numbers = []
            number_elems = result.select('.win_number_box .win_ball')
            for elem in number_elems[:6]:
                num_text = elem.get_text(strip=True)
                if num_text.isdigit():
                    win_numbers.append(num_text)
            
            # 보너스 번호
            bonus_elem = result.select_one('.win_number_box .bonus_ball')
            bonus = bonus_elem.get_text(strip=True) if bonus_elem else ""
            
            if win_numbers:
                send_msg = f"🎰 로또 6/45 당첨번호\n"
                if round_num:
                    send_msg += f"📅 제 {round_num}회"
                if date_str:
                    send_msg += f" ({date_str})"
                send_msg += "\n" + "="*25 + "\n\n"
                send_msg += f"🎱 당첨번호: {' - '.join(win_numbers)}\n"
                if bonus:
                    send_msg += f"⭐ 보너스: {bonus}\n"
                
                # 1등 당첨금액 정보
                prize_elem = result.select_one('.win_prize_money')
                if prize_elem:
                    prize_text = prize_elem.get_text(strip=True)
                    send_msg += f"\n💰 1등 당첨금: {prize_text}"
                
                return send_msg
        
        # 크롤링 실패 시 기본 메시지
        return "🎰 로또 당첨번호를 조회할 수 없습니다.\n잠시 후 다시 시도해주세요."
        
    except Exception as e:
        log(f"로또 결과 조회 오류: {e}")
        return "로또 당첨번호를 조회하는 중 오류가 발생했습니다"


def lotto_result_create(room: str, sender: str, msg: str):
    """로또 결과 생성"""
    try:
        numbers = sorted(random.sample(range(1, 46), 6))
        bonus = random.randint(1, 45)
        while bonus in numbers:
            bonus = random.randint(1, 45)
        
        return f"🍀 로또 번호 생성\n\n🎱 {' - '.join(map(str, numbers))}\n⭐ 보너스: {bonus}"
    except Exception as e:
        log(f"로또 생성 오류: {e}")
        return "로또 번호를 생성하는 중 오류가 발생했습니다"


def fortune_today(room: str, sender: str, msg: str):
    """오늘의 운세"""
    try:
        url = "https://m.search.naver.com/search.naver?where=m&sm=mtp_hty.top&query=오늘의운세"
        result = request(url, method="get", result="bs")
        
        if result:
            fortune_text = result.select_one('.text_fortune')
            if fortune_text:
                return f"🔮 오늘의 운세\n\n{fortune_text.get_text(strip=True)}"
        
        # 기본 운세 메시지
        fortunes = [
            "오늘은 좋은 일이 생길 것 같아요! ✨",
            "새로운 기회가 찾아올 수 있는 날입니다 🌟",
            "조금 더 신중하게 행동하시면 좋을 것 같아요 🤔",
            "오늘은 주변 사람들과의 관계에 신경 써보세요 💝",
            "건강에 조금 더 신경 쓰시는 게 좋겠어요 🏃‍♂️"
        ]
        return f"🔮 오늘의 운세\n\n{random.choice(fortunes)}"
    except Exception as e:
        debug_logger.error(f"운세 조회 오류: {str(e)}")
        return "운세를 조회하는 중 오류가 발생했습니다"


def lol_record(room: str, sender: str, msg: str):
    """LOL 전적 조회"""
    try:
        nickname = msg.replace("/전적", "").strip()
        if not nickname:
            return "[/전적 소환사명] 형식으로 입력해주세요."
        
        suffix = '-KR1' if '-' not in nickname else ''

        url = f"https://fow.kr/find/{nickname}{suffix}"
        headers = {
            'Referer': 'https://fow.kr/ranking',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
        }
        doc = request(url, method="get", result="bs", headers=headers)
        
        summary = doc.select_one('div.table_summary')
        if not summary:
            return f"{nickname} 소환사를 찾을 수 없어요."
        
        input_text = summary.get_text()
        
        # 티어 정보 추출
        tier_elem = doc.select_one('.tier_banner_name')
        tier = tier_elem.get_text(strip=True) if tier_elem else "Unranked"
        
        # LP 및 승률 정보
        lp_elem = doc.select_one('.tier_banner_lp')
        lp = lp_elem.get_text(strip=True) if lp_elem else ""
        
        # 최근 게임 정보
        recent_games = doc.select('.game_row')[:5]  # 최근 5게임
        
        send_msg = f"🎮 {nickname} 님의 전적\n"
        send_msg += f"{'='*25}\n"
        send_msg += f"🏆 티어: {tier}\n"
        if lp:
            send_msg += f"💎 LP: {lp}\n"
        
        if recent_games:
            send_msg += f"\n📊 최근 {len(recent_games)}게임:\n"
            for idx, game in enumerate(recent_games, 1):
                result = "승리" if "win" in str(game.get('class', [])) else "패배"
                champion_elem = game.select_one('.champion_name')
                champion = champion_elem.get_text(strip=True) if champion_elem else "Unknown"
                
                kda_elem = game.select_one('.kda')
                kda = kda_elem.get_text(strip=True) if kda_elem else ""
                
                send_msg += f"{idx}. {champion} - {result}"
                if kda:
                    send_msg += f" ({kda})"
                send_msg += "\n"
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"전적 조회 오류: {str(e)}")
        return f"전적 조회 중 오류가 발생했습니다"