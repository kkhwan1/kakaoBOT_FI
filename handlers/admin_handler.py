#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
관리자 핸들러 모듈
방 관리, 대화 분석 등 관리자 명령어 처리
"""

from datetime import datetime
from utils.text_utils import log
from utils.debug_logger import debug_logger
import config

# DB 연결 함수
try:
    from fn import get_conn
except ImportError:
    def get_conn():
        """DB 연결 폴백"""
        import pymysql
        from config import DB_CONFIG
        
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4'
        )
        return conn, conn.cursor()


def room_add(room: str, sender: str, msg: str):
    """방 추가 명령어 처리"""
    # 추가할 방 이름 추출
    new_room = msg.replace("/방추가", "").strip()
    if not new_room:
        return "사용법: /방추가 [방이름]"
    
    # 현재 허용된 방 목록 가져오기
    allowed_rooms = config.BOT_CONFIG["ALLOWED_ROOMS"]
    
    # 이미 존재하는지 확인
    if new_room in allowed_rooms:
        return f"❌ '{new_room}' 방은 이미 허용 목록에 있습니다."
    
    # 방 추가
    config.BOT_CONFIG["ALLOWED_ROOMS"].append(new_room)
    
    # config.py 파일 업데이트
    try:
        update_config_file()
        return f"✅ '{new_room}' 방이 허용 목록에 추가되었습니다.\n\n현재 허용된 방 목록:\n" + "\n".join([f"• {r}" for r in config.BOT_CONFIG["ALLOWED_ROOMS"]])
    except Exception as e:
        log(f"방 추가 오류: {e}")
        return "방 추가 중 오류가 발생했습니다."


def room_remove(room: str, sender: str, msg: str):
    """방 삭제 명령어 처리"""
    # 삭제할 방 이름 추출
    remove_room = msg.replace("/방삭제", "").strip()
    if not remove_room:
        return "사용법: /방삭제 [방이름]"
    
    # 현재 허용된 방 목록 가져오기
    allowed_rooms = config.BOT_CONFIG["ALLOWED_ROOMS"]
    
    # 존재하는지 확인
    if remove_room not in allowed_rooms:
        return f"❌ '{remove_room}' 방은 허용 목록에 없습니다."
    
    # 관리자 방은 삭제 불가
    if remove_room == config.BOT_CONFIG["ADMIN_ROOM"]:
        return "❌ 관리자 방은 삭제할 수 없습니다."
    
    # 방 삭제
    config.BOT_CONFIG["ALLOWED_ROOMS"].remove(remove_room)
    
    # config.py 파일 업데이트
    try:
        update_config_file()
        return f"✅ '{remove_room}' 방이 허용 목록에서 삭제되었습니다.\n\n현재 허용된 방 목록:\n" + "\n".join([f"• {r}" for r in config.BOT_CONFIG["ALLOWED_ROOMS"]])
    except Exception as e:
        log(f"방 삭제 오류: {e}")
        return "방 삭제 중 오류가 발생했습니다."


def room_list(room: str, sender: str, msg: str):
    """방 목록 명령어 처리"""
    allowed_rooms = config.BOT_CONFIG["ALLOWED_ROOMS"]
    admin_room = config.BOT_CONFIG["ADMIN_ROOM"]
    
    room_list_text = "\n".join([
        f"• {r} {'(관리자방)' if r == admin_room else ''}" 
        for r in allowed_rooms
    ])
    
    return f"📋 현재 허용된 방 목록 ({len(allowed_rooms)}개)\n\n{room_list_text}"


def talk_analyize(room: str, sender: str, msg: str, interval_day: int = 0):
    """대화 분석 - 수다쟁이 순위 등"""
    dt_text = "오늘" if interval_day == 0 else "어제"

    try:
        conn, cur = get_conn()

        # 수다쟁이 TOP 10
        query = """
        SELECT sender, COUNT(*) AS cnt
        FROM kt_message 
        WHERE 
            room = %s
            AND DATE(created_at) = CURDATE() + %s
            AND sender NOT IN ('윤봇', '오픈채팅봇', '팬다 Jr.')
        GROUP BY sender
        ORDER BY cnt desc
        LIMIT 10"""
        params = (room, interval_day)
        cur.execute(query, params)
        rows = cur.fetchall()
        
        msg_rank = f"💬 {dt_text}의 수다쟁이 TOP 10\n"
        msg_rank += f"📅 {room}\n"
        msg_rank += "=" * 25 + "\n"
        
        if rows:
            for idx, row in enumerate(rows, 1):
                sender_name = row[0]
                count = row[1]
                
                # 순위별 이모지
                if idx == 1:
                    rank_emoji = "🥇"
                elif idx == 2:
                    rank_emoji = "🥈"
                elif idx == 3:
                    rank_emoji = "🥉"
                else:
                    rank_emoji = f"{idx}."
                
                msg_rank += f"{rank_emoji} {sender_name}: {count}회\n"
        else:
            msg_rank += "아직 대화 기록이 없습니다.\n"
        
        # 총 메시지 수
        query_total = """
        SELECT COUNT(*) 
        FROM kt_message 
        WHERE room = %s 
            AND DATE(created_at) = CURDATE() + %s
            AND sender NOT IN ('윤봇', '오픈채팅봇', '팬다 Jr.')
        """
        cur.execute(query_total, params)
        total_count = cur.fetchone()[0]
        
        msg_rank += f"\n📊 총 메시지: {total_count}개"
        
        conn.close()
        return msg_rank
        
    except Exception as e:
        debug_logger.error(f"대화 분석 오류: {str(e)}")
        return "대화 분석 중 오류가 발생했습니다."


def update_config_file():
    """config.py 파일을 현재 설정으로 업데이트"""
    import os
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
    
    # config.py 파일 내용 생성
    config_content = f'''"""
========================================
카카오톡 봇 설정 파일
========================================
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 봇 기본 설정
BOT_CONFIG = {{
    "BOT_NAME": "윤봇",
    "VERSION": "2.1.0",
    "ADMIN_ROOM": "{config.BOT_CONFIG['ADMIN_ROOM']}",
    "ALLOWED_ROOMS": {config.BOT_CONFIG['ALLOWED_ROOMS']},
    "BOT_ENABLED": True
}}

# 서버 설정
SERVER_CONFIG = {{
    "HOST": "0.0.0.0",
    "PORT": 8002,
    "DEBUG": False
}}

# 데이터베이스 설정
DB_CONFIG = {{
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'kt_bot'),
    'charset': 'utf8mb4'
}}

# 기능 활성화 설정
FEATURES = {{
    "AI_ENABLED": True,
    "STOCK_ENABLED": True,
    "NEWS_ENABLED": True,
    "WEATHER_ENABLED": True,
    "GAME_ENABLED": True,
    "MEDIA_ENABLED": True,
    "UTILITY_ENABLED": True
}}

# 로깅 설정
LOGGING = {{
    "LEVEL": "INFO",
    "FILE": "logs/bot.log",
    "MAX_SIZE": "10MB",
    "BACKUP_COUNT": 5
}}
'''
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        debug_logger.log_debug("Config 파일 업데이트 완료")
    except Exception as e:
        log(f"Config 파일 업데이트 오류: {e}")
        raise