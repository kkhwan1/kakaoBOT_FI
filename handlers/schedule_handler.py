#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
스케줄 핸들러 모듈
스케줄 관련 명령어 처리
"""

import re
from typing import Tuple
from datetime import datetime


def parse_schedule_command(msg: str) -> Tuple[bool, dict]:
    """
    스케줄 등록 명령어 파싱
    /스케줄 매일 09:00 /뉴스 → 이국환
    /스케줄 평일 08:30 /날씨 서울 → 가족방
    """
    # 기본 패턴: /스케줄 [패턴] [시간] [명령어] → [대상방]
    # 또는: /스케줄 [패턴] [시간] [명령어] (대상방 생략)

    msg = msg.strip()
    if not msg.startswith('/스케줄'):
        return False, {"error": "스케줄 명령어가 아닙니다."}

    # /스케줄 제거
    content = msg[len('/스케줄'):].strip()

    if not content:
        return False, {"error": "사용법: /스케줄 [패턴] [시간] [명령어] → [대상방]"}

    # → 로 대상방 분리
    if '→' in content:
        parts = content.split('→')
        main_part = parts[0].strip()
        target_room = parts[1].strip() if len(parts) > 1 else None
    elif '->' in content:
        parts = content.split('->')
        main_part = parts[0].strip()
        target_room = parts[1].strip() if len(parts) > 1 else None
    else:
        main_part = content
        target_room = None

    # 패턴, 시간, 명령어 파싱
    # 패턴 목록
    patterns = ['매일', '평일', '주말', '매주월', '매주화', '매주수', '매주목',
                '매주금', '매주토', '매주일']

    # 매월X일 패턴 추가
    month_day_match = re.match(r'(매월\d{1,2}일)', main_part)
    if month_day_match:
        pattern = month_day_match.group(1)
        main_part = main_part[len(pattern):].strip()
    else:
        pattern = None
        for p in patterns:
            if main_part.startswith(p):
                pattern = p
                main_part = main_part[len(p):].strip()
                break

    if not pattern:
        return False, {"error": f"유효한 패턴이 필요합니다.\n패턴: {', '.join(patterns)}, 매월X일"}

    # 시간 파싱 (HH:MM 또는 한국어)
    time_match = re.match(r'(\d{1,2}:\d{2}|오전\d{1,2}시(?:\d{1,2}분)?|오후\d{1,2}시(?:\d{1,2}분)?)', main_part)
    if not time_match:
        return False, {"error": "시간 형식이 올바르지 않습니다.\n예: 09:00, 오전9시, 오후2시30분"}

    time_str = time_match.group(1)
    command = main_part[len(time_str):].strip()

    if not command:
        return False, {"error": "실행할 명령어가 필요합니다.\n예: /뉴스, /날씨 서울"}

    if not command.startswith('/') and not command.startswith('?'):
        return False, {"error": "명령어는 / 또는 ?로 시작해야 합니다."}

    return True, {
        "pattern": pattern,
        "time": time_str,
        "command": command,
        "target_room": target_room
    }


def schedule_add(room: str, sender: str, msg: str) -> str:
    """
    스케줄 등록
    /스케줄 매일 09:00 /뉴스 → 이국환
    """
    from services.schedule_service import schedule_service

    # 명령어 파싱
    success, result = parse_schedule_command(msg)

    if not success:
        return f"⚠️ {result.get('error', '파싱 오류')}\n\n사용법:\n/스케줄 매일 09:00 /뉴스 → 이국환\n/스케줄 평일 08:30 /날씨 서울"

    pattern = result['pattern']
    time_str = result['time']
    command = result['command']
    target_room = result.get('target_room') or room  # 대상방 생략시 현재 방

    # 스케줄 등록
    success, message = schedule_service.add_schedule(
        pattern=pattern,
        time_str=time_str,
        command=command,
        target_room=target_room,
        creator=sender
    )

    return message


def schedule_list(room: str, sender: str, msg: str) -> str:
    """
    스케줄 목록 조회
    /스케줄목록
    """
    from services.schedule_service import schedule_service

    # 관리자는 전체 조회, 일반 사용자는 본인 스케줄만
    import config
    if config.is_admin_user(sender):
        schedules = schedule_service.get_schedules()
    else:
        schedules = schedule_service.get_schedules(creator=sender)

    return schedule_service.format_schedule_list(schedules)


def schedule_delete(room: str, sender: str, msg: str) -> str:
    """
    스케줄 삭제
    /스케줄삭제 sch_abc123
    """
    from services.schedule_service import schedule_service

    # job_id 추출
    parts = msg.split()
    if len(parts) < 2:
        return "⚠️ 삭제할 스케줄 ID를 입력하세요.\n사용법: /스케줄삭제 sch_xxx"

    job_id = parts[1].strip()

    # 스케줄 삭제
    success, message = schedule_service.delete_schedule(job_id, sender)

    return message
