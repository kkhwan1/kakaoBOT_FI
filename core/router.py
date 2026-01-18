"""
라우터 모듈
메시지를 적절한 핸들러로 라우팅하는 기능
"""

import re
import random
from datetime import datetime
import subprocess

import config
from utils.debug_logger import debug_logger


def log(message):
    """로그 출력 함수"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def get_reply_msg(room: str, sender: str, msg: str):
    """메시지를 받아서 적절한 응답을 반환하는 메인 라우터
    
    Args:
        room: 채팅방 이름
        sender: 발신자 이름
        msg: 메시지 내용
        
    Returns:
        str or None: 응답 메시지
    """
    log(f"{room}    {sender}    {msg}")
    
    msg = msg.strip()
    
    # 빈 메시지 처리
    if not msg:
        return None
    
    # 핸들러 모듈들 import (지연 로딩)
    from handlers import (
        # AI 핸들러
        get_ai_answer,
        # 뉴스 핸들러
        economy_news, it_news, realestate_news, world_news,
        # 주식/금융 핸들러
        stock, coin, exchange, gold, stock_upper, stock_lower,
        # 미디어 핸들러
        youtube_popular_all, youtube_popular_random, summarize, movie_rank, photo,
        # 게임 핸들러
        lotto, lotto_result, lotto_result_create, lol_record, fortune_today,
        # 유틸리티 핸들러
        whether, whether_today, calorie, wise_saying, emoji, naver_map,
        search_blog, naver_keyword, real_keyword, naver_land,
        # 관리자 핸들러
        room_add, room_remove, room_list, talk_analyize, my_talk_analyize
    )
    
    from services import (
        web_summary, fortune, zodiac, test
    )
    
    # 통합 명령어 관리자 import
    try:
        from command_manager import get_command_help, check_command_permission, get_command_list
        from error_commands import error_logs, error_stats, usage_stats, enable_command, reset_command_stats, performance_recommendations
        from cache_commands import clear_cache, cache_status
    except ImportError:
        # 명령어 관리자가 없는 경우 기본 함수 정의
        def get_command_help(is_admin=False):
            return "명령어 도움말이 준비 중입니다."
        def check_command_permission(cmd, sender, room):
            return (True, None)
        def get_command_list(is_admin=False):
            return "명령어 목록이 준비 중입니다."
        
    # 테스트 명령어
    if msg == '/테스트':
        return "테스트 성공"
    elif msg == '/테스트2':
        return "테스트 성공!\n두번째 줄입니다."
    elif msg == '/테스트3':
        return "😊 이모지 테스트"
    elif msg == '/안녕':
        return f"안녕하세요 {sender}님! 저는 STORIUM AI입니다."
    elif msg == '/시간':
        return f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 명령어 도움말
    if msg in ['/명령어', '/가이드', '/도움말']:
        is_admin = config.is_admin_user(sender)
        return get_command_help(is_admin=is_admin)
    elif msg == '/명령어목록':
        is_admin = config.is_admin_user(sender)
        return get_command_list(is_admin=is_admin)
    
    # 운세/점술 관련
    elif msg == "/운세":
        return fortune_today(room, sender, msg)
    elif msg.startswith("/운세"):
        return fortune(room, sender, msg)
    elif msg in ["/물병자리", "/물고기자리", "/양자리", "/황소자리", "/쌍둥이자리", 
                  "/게자리", "/사자자리", "/처녀자리", "/천칭자리", "/전갈자리", 
                  "/사수자리", "/궁수자리", "/염소자리"]:
        return zodiac(room, sender, msg)
    
    # 날씨
    elif msg == '/날씨':
        return whether_today(room, sender, msg)
    elif msg.startswith("/날씨"):
        return whether(room, sender, msg)
    
    # 실시간 정보
    elif msg in ["/실시간검색어", '/검색어']:
        return real_keyword(room, sender, msg)

    # 뉴스
    elif msg.upper() == '/IT뉴스':
        return it_news(room, sender, msg)
    elif msg == '/경제뉴스':
        return economy_news(room, sender, msg)
    elif msg == '/부동산뉴스':
        return realestate_news(room, sender, msg)
    elif msg == '/세계뉴스':
        return world_news(room, sender, msg)

    # 검색
    elif msg.startswith("/블로그"):
        return search_blog(room, sender, msg)
    elif msg.startswith("#"):
        return naver_keyword(room, sender, msg)
    
    # 금융/경제
    elif msg.startswith("/주식"):
        return stock(room, sender, msg)
    elif msg == "/환율":
        return exchange(room, sender, msg)
    elif msg == '/금값':
        return gold(room, sender, msg)
    elif msg == '/코인':
        return coin(room, sender, msg)
    elif msg == "/상한가":
        return stock_upper(room, sender, msg)
    elif msg == "/하한가":
        return stock_lower(room, sender, msg)
    
    # 생활 정보
    elif msg.startswith("/칼로리"):
        return calorie(room, sender, msg)
    elif msg == "/영화순위":
        return movie_rank(room, sender, msg)
    elif msg.startswith(("/맵", "/지도")):
        return naver_map(room, sender, msg)
    elif msg.startswith("/") and msg.endswith("맛집"):
        return naver_map(room, sender, msg)
    elif msg == "/명언":
        return wise_saying(room, sender, msg)
    
    # 유튜브
    elif msg == "/인급동":
        return youtube_popular_all(room, sender, msg)
    elif msg == "/인급동랜덤":
        return youtube_popular_random(room, sender, msg)
    
    # 부동산
    elif msg.startswith("/네이버부동산"):
        return naver_land(room, sender, msg)
    
    # 게임
    elif msg.startswith('/전적'):
        return lol_record(room, sender, msg)
    
    # 로또
    elif msg.startswith("/로또결과생성"):
        return lotto_result_create(room, sender, msg)
    elif msg.startswith("/로또결과"):
        return lotto_result(room, sender, msg)
    elif msg.startswith("/로또") or "로또" in msg:
        return lotto(room, sender, msg)
    
    # 스팸 감지
    elif "han.gl" in msg:
        return "스팸이 감지되었습니다."
    
    # URL 자동 감지 로직
    # YouTube URL 패턴
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        youtube_match = re.search(pattern, msg)
        if youtube_match:
            youtube_url = youtube_match.group(0)
            if not youtube_url.startswith('http'):
                youtube_url = 'https://' + youtube_url
            return summarize(room, sender, youtube_url)
    
    # 일반 웹 URL 패턴
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    url_match = re.search(url_pattern, msg)
    if url_match:
        web_url = url_match.group(0)
        return web_summary(room, sender, web_url)
    
    # 관리자 전용 명령어
    if config.is_admin_user(sender):
        # 테스트
        if msg == '/test':
            return test(room, sender, msg)
        
        # 재부팅
        elif msg == '/재부팅':
            can_use, error_msg = check_command_permission('/재부팅', sender, room)
            if not can_use:
                return error_msg
            subprocess.run(["adb", "reboot"])
            return "재부팅 명령이 실행되었습니다."
        
        # 방 관리
        elif msg.startswith('/방추가'):
            can_use, error_msg = check_command_permission('/방추가', sender, room)
            if not can_use:
                return error_msg
            return room_add(room, sender, msg)
        elif msg.startswith('/방삭제'):
            can_use, error_msg = check_command_permission('/방삭제', sender, room)
            if not can_use:
                return error_msg
            return room_remove(room, sender, msg)
        elif msg == '/방목록':
            can_use, error_msg = check_command_permission('/방목록', sender, room)
            if not can_use:
                return error_msg
            return room_list(room, sender, msg)
        
        # 오류 모니터링 (관리자 전용)
        elif msg.startswith('/오류로그'):
            return error_logs(room, sender, msg)
        elif msg.startswith('/오류통계'):
            return error_stats(room, sender, msg)
        elif msg.startswith('/사용통계'):
            return usage_stats(room, sender, msg)
        elif msg.startswith('/명령어활성화'):
            return enable_command(room, sender, msg)
        elif msg.startswith('/통계리셋'):
            return reset_command_stats(room, sender, msg)
        elif msg.startswith('/성능추천'):
            return performance_recommendations(room, sender, msg)
        elif msg.startswith('/캐시초기화'):
            return clear_cache(room, sender, msg)
        elif msg.startswith('/캐시상태'):
            return cache_status(room, sender, msg)
    
    # 인사 메시지 처리
    greetings = ["안녕", "안녕하세요", "하이", "헬로", "ㅎㅇ", "ㅎ2", "반가워", "반갑습니다"]
    for greeting in greetings:
        if greeting in msg.lower():
            return f"{sender}님, 안녕하세요! STORIUM Bot입니다. 무엇을 도와드릴까요? /명령어를 입력하면 사용 가능한 기능을 볼 수 있어요!"
    
    # 가끔 명언 보내기(0.2%)
    if random.random() < 0.002:
        return wise_saying(room, sender, msg)
    
    # 기본 응답 - 명령어가 없는 경우
    return None