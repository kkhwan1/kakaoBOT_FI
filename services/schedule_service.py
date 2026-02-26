#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
스케줄 서비스 모듈
APScheduler를 사용한 명령어 자동 실행 및 관리
"""

import os
import re
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from threading import Lock
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger(__name__)

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'schedules.db')
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'schedules.json')


class ScheduleService:
    """스케줄 관리 서비스"""

    # 패턴별 cron 표현식 매핑
    PATTERN_CRON_MAP = {
        '매일': {'day_of_week': '*'},
        '평일': {'day_of_week': 'mon-fri'},
        '주말': {'day_of_week': 'sat,sun'},
        '매주월': {'day_of_week': 'mon'},
        '매주화': {'day_of_week': 'tue'},
        '매주수': {'day_of_week': 'wed'},
        '매주목': {'day_of_week': 'thu'},
        '매주금': {'day_of_week': 'fri'},
        '매주토': {'day_of_week': 'sat'},
        '매주일': {'day_of_week': 'sun'},
    }

    # 방당 최대 스케줄 수
    MAX_SCHEDULES_PER_ROOM = 20

    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self.pending_messages: List[Dict[str, Any]] = []
        self.lock = Lock()
        self._initialized = False

    def initialize(self):
        """스케줄러 초기화 및 DB에서 스케줄 복원"""
        if self._initialized:
            logger.warning("스케줄러가 이미 초기화되었습니다.")
            return

        try:
            # 데이터베이스 초기화
            self._init_database()

            # APScheduler 초기화
            self.scheduler = BackgroundScheduler(
                jobstores={'default': MemoryJobStore()},
                timezone='Asia/Seoul'
            )
            self.scheduler.start()

            # DB에서 활성 스케줄 복원
            self._restore_schedules_from_db()

            # 설정 파일에서 스케줄 로드
            self._load_schedules_from_config()

            self._initialized = True
            logger.info("✅ 스케줄 서비스 초기화 완료")

        except Exception as e:
            logger.error(f"스케줄러 초기화 실패: {e}")
            raise

    def shutdown(self):
        """스케줄러 종료"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("스케줄러 종료됨")

    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 스케줄 작업 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                pattern TEXT NOT NULL,
                time TEXT NOT NULL,
                command TEXT NOT NULL,
                target_room TEXT NOT NULL,
                creator TEXT NOT NULL,
                source TEXT DEFAULT 'command',
                cron_expression TEXT,
                status TEXT DEFAULT 'active',
                last_run TEXT,
                run_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 대기 메시지 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                message TEXT NOT NULL,
                job_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("스케줄 데이터베이스 초기화 완료")

    def _restore_schedules_from_db(self):
        """DB에서 활성 스케줄 복원"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT job_id, pattern, time, command, target_room, creator
            FROM schedule_jobs
            WHERE status = 'active'
        ''')

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            job_id, pattern, time_str, command, target_room, creator = row
            try:
                self._add_scheduler_job(job_id, pattern, time_str, command, target_room)
                logger.info(f"스케줄 복원: {job_id} - {pattern} {time_str} {command}")
            except Exception as e:
                logger.error(f"스케줄 복원 실패 ({job_id}): {e}")

        logger.info(f"총 {len(rows)}개 스케줄 복원됨")

    def _load_schedules_from_config(self):
        """설정 파일에서 스케줄 로드"""
        if not os.path.exists(CONFIG_PATH):
            # 기본 설정 파일 생성
            default_config = {
                "schedules": []
            }
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info("기본 스케줄 설정 파일 생성됨")
            return

        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)

            schedules = config.get('schedules', [])
            for schedule in schedules:
                if not schedule.get('enabled', True):
                    continue

                job_id = f"config_{schedule.get('id', uuid.uuid4().hex[:8])}"

                # 이미 등록된 스케줄인지 확인
                if self._job_exists_in_db(job_id):
                    continue

                pattern = schedule.get('pattern', '매일')
                time_str = schedule.get('time', '09:00')
                command = schedule.get('command', '')
                room = schedule.get('room', '')

                if command and room:
                    self._save_schedule_to_db(
                        job_id, pattern, time_str, command, room, 'system', 'config'
                    )
                    self._add_scheduler_job(job_id, pattern, time_str, command, room)
                    logger.info(f"설정 파일 스케줄 로드: {job_id}")

            logger.info(f"설정 파일에서 {len(schedules)}개 스케줄 확인")

        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")

    def _job_exists_in_db(self, job_id: str) -> bool:
        """스케줄이 DB에 존재하는지 확인"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM schedule_jobs WHERE job_id = ?', (job_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def _parse_time(self, time_str: str) -> Tuple[int, int]:
        """시간 문자열 파싱 (HH:MM 또는 한국어)"""
        # HH:MM 형식
        match = re.match(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            return int(match.group(1)), int(match.group(2))

        # 한국어 형식 (오전/오후 X시 Y분)
        match = re.match(r'(오전|오후)?(\d{1,2})시(?:(\d{1,2})분)?', time_str)
        if match:
            period = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3)) if match.group(3) else 0

            if period == '오후' and hour < 12:
                hour += 12
            elif period == '오전' and hour == 12:
                hour = 0

            return hour, minute

        raise ValueError(f"유효하지 않은 시간 형식: {time_str}")

    def _parse_pattern(self, pattern: str) -> Dict[str, Any]:
        """패턴 문자열을 cron 표현식 파라미터로 변환"""
        # 기본 패턴
        if pattern in self.PATTERN_CRON_MAP:
            return self.PATTERN_CRON_MAP[pattern]

        # 매월X일 형식
        match = re.match(r'매월(\d{1,2})일', pattern)
        if match:
            day = int(match.group(1))
            if 1 <= day <= 31:
                return {'day': str(day)}

        raise ValueError(f"유효하지 않은 패턴: {pattern}")

    def _add_scheduler_job(self, job_id: str, pattern: str, time_str: str,
                          command: str, target_room: str):
        """APScheduler에 작업 추가"""
        hour, minute = self._parse_time(time_str)
        cron_params = self._parse_pattern(pattern)

        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            **cron_params,
            timezone='Asia/Seoul'
        )

        self.scheduler.add_job(
            func=self._execute_scheduled_command,
            trigger=trigger,
            args=[job_id, target_room, command],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=300  # 5분 유예
        )

    def _execute_scheduled_command(self, job_id: str, room: str, command: str):
        """스케줄된 명령어 실행"""
        try:
            logger.info(f"스케줄 실행: {job_id} - {command} -> {room}")

            # get_reply_msg 함수 import (순환 참조 방지)
            from core.router import get_reply_msg

            # 명령어 실행
            result = get_reply_msg(room, "scheduled", command)

            if result:
                # 대기 메시지에 추가
                with self.lock:
                    message_data = {
                        'room': room,
                        'message': result,
                        'job_id': job_id,
                        'created_at': datetime.now().isoformat()
                    }
                    self.pending_messages.append(message_data)

                    # DB에도 저장 (영속성)
                    self._save_pending_message(room, result, job_id)

                logger.info(f"스케줄 실행 완료: {job_id} - 결과 길이: {len(result)}")

            # 실행 통계 업데이트
            self._update_run_stats(job_id)

        except Exception as e:
            logger.error(f"스케줄 실행 오류 ({job_id}): {e}")

            # 에러 메시지도 전송
            error_msg = f"⚠️ 스케줄 실행 오류\n명령어: {command}\n오류: {str(e)}"
            with self.lock:
                self.pending_messages.append({
                    'room': room,
                    'message': error_msg,
                    'job_id': job_id,
                    'created_at': datetime.now().isoformat()
                })

    def _save_pending_message(self, room: str, message: str, job_id: str):
        """대기 메시지 DB 저장"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pending_messages (room, message, job_id)
            VALUES (?, ?, ?)
        ''', (room, message, job_id))
        conn.commit()
        conn.close()

    def _update_run_stats(self, job_id: str):
        """실행 통계 업데이트"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE schedule_jobs
            SET last_run = ?, run_count = run_count + 1
            WHERE job_id = ?
        ''', (datetime.now().isoformat(), job_id))
        conn.commit()
        conn.close()

    def _save_schedule_to_db(self, job_id: str, pattern: str, time_str: str,
                            command: str, target_room: str, creator: str,
                            source: str = 'command') -> bool:
        """스케줄을 DB에 저장"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # cron 표현식 생성
            hour, minute = self._parse_time(time_str)
            cron_params = self._parse_pattern(pattern)
            cron_expr = f"{minute} {hour} * * {cron_params.get('day_of_week', '*')}"

            cursor.execute('''
                INSERT INTO schedule_jobs
                (job_id, pattern, time, command, target_room, creator, source, cron_expression)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, pattern, time_str, command, target_room, creator, source, cron_expr))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"중복 스케줄 ID: {job_id}")
            return False
        except Exception as e:
            logger.error(f"스케줄 저장 실패: {e}")
            return False

    def add_schedule(self, pattern: str, time_str: str, command: str,
                    target_room: str, creator: str) -> Tuple[bool, str]:
        """새 스케줄 등록"""
        try:
            # 유효성 검사
            self._parse_time(time_str)
            self._parse_pattern(pattern)

            if not command.startswith('/') and not command.startswith('?'):
                return False, "명령어는 / 또는 ?로 시작해야 합니다."

            # 방당 스케줄 수 제한 확인
            schedule_count = self.get_room_schedule_count(target_room)
            if schedule_count >= self.MAX_SCHEDULES_PER_ROOM:
                return False, f"방당 최대 {self.MAX_SCHEDULES_PER_ROOM}개 스케줄만 등록 가능합니다."

            # 중복 확인
            if self._is_duplicate_schedule(pattern, time_str, command, target_room):
                return False, "동일한 스케줄이 이미 등록되어 있습니다."

            # 고유 ID 생성
            job_id = f"sch_{uuid.uuid4().hex[:8]}"

            # DB 저장
            if not self._save_schedule_to_db(job_id, pattern, time_str, command,
                                            target_room, creator):
                return False, "스케줄 저장에 실패했습니다."

            # 스케줄러에 추가
            self._add_scheduler_job(job_id, pattern, time_str, command, target_room)

            logger.info(f"새 스케줄 등록: {job_id} by {creator}")
            return True, f"✅ 스케줄이 등록되었습니다.\nID: {job_id}\n{pattern} {time_str} {command} -> {target_room}"

        except ValueError as e:
            return False, f"⚠️ {str(e)}"
        except Exception as e:
            logger.error(f"스케줄 등록 오류: {e}")
            return False, f"⚠️ 스케줄 등록 중 오류가 발생했습니다."

    def _is_duplicate_schedule(self, pattern: str, time_str: str,
                               command: str, target_room: str) -> bool:
        """중복 스케줄 확인"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM schedule_jobs
            WHERE pattern = ? AND time = ? AND command = ? AND target_room = ? AND status = 'active'
        ''', (pattern, time_str, command, target_room))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_room_schedule_count(self, room: str) -> int:
        """방의 스케줄 수 조회"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM schedule_jobs
            WHERE target_room = ? AND status = 'active'
        ''', (room,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def delete_schedule(self, job_id: str, requester: str) -> Tuple[bool, str]:
        """스케줄 삭제"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # 스케줄 확인
            cursor.execute('''
                SELECT creator, source, command, target_room FROM schedule_jobs
                WHERE job_id = ? AND status = 'active'
            ''', (job_id,))

            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, f"스케줄을 찾을 수 없습니다: {job_id}"

            creator, source, command, target_room = row

            # 설정 파일 스케줄은 관리자만 삭제 가능 (추후 config에서 확인)
            # 일단은 본인이 생성한 스케줄만 삭제 가능하게
            # if source == 'config':
            #     return False, "설정 파일 스케줄은 삭제할 수 없습니다."

            # 상태 변경 (soft delete)
            cursor.execute('''
                UPDATE schedule_jobs
                SET status = 'deleted'
                WHERE job_id = ?
            ''', (job_id,))

            conn.commit()
            conn.close()

            # 스케줄러에서 제거
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass

            logger.info(f"스케줄 삭제: {job_id} by {requester}")
            return True, f"✅ 스케줄이 삭제되었습니다.\nID: {job_id}\n명령어: {command}"

        except Exception as e:
            logger.error(f"스케줄 삭제 오류: {e}")
            return False, f"⚠️ 스케줄 삭제 중 오류가 발생했습니다."

    def get_schedules(self, room: str = None, creator: str = None) -> List[Dict]:
        """스케줄 목록 조회"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = '''
            SELECT job_id, pattern, time, command, target_room, creator,
                   source, status, last_run, run_count, created_at
            FROM schedule_jobs
            WHERE status = 'active'
        '''
        params = []

        if room:
            query += ' AND target_room = ?'
            params.append(room)

        if creator:
            query += ' AND creator = ?'
            params.append(creator)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_pending_messages(self, room: str = None) -> List[Dict]:
        """대기 메시지 조회 및 반환 (polling용)"""
        with self.lock:
            if room:
                messages = [m for m in self.pending_messages if m['room'] == room]
                self.pending_messages = [m for m in self.pending_messages if m['room'] != room]
            else:
                messages = self.pending_messages.copy()
                self.pending_messages.clear()

            # DB에서도 delivered 표시
            if messages:
                self._mark_messages_delivered([m.get('job_id') for m in messages if m.get('job_id')])

            return messages

    def _mark_messages_delivered(self, job_ids: List[str]):
        """메시지 전달 완료 표시"""
        if not job_ids:
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        placeholders = ','.join(['?' for _ in job_ids])
        cursor.execute(f'''
            UPDATE pending_messages
            SET delivered = 1
            WHERE job_id IN ({placeholders}) AND delivered = 0
        ''', job_ids)
        conn.commit()
        conn.close()

    def format_schedule_list(self, schedules: List[Dict]) -> str:
        """스케줄 목록 포맷팅"""
        if not schedules:
            return "📋 등록된 스케줄이 없습니다."

        lines = ["📋 **스케줄 목록**", ""]

        for i, sch in enumerate(schedules, 1):
            status_icon = "✅" if sch['status'] == 'active' else "⏸️"
            source_icon = "📁" if sch['source'] == 'config' else "💬"

            lines.append(f"{status_icon} {i}. [{sch['job_id']}]")
            lines.append(f"   {source_icon} {sch['pattern']} {sch['time']} {sch['command']}")
            lines.append(f"   → {sch['target_room']}")

            if sch['last_run']:
                lines.append(f"   최근 실행: {sch['last_run'][:16]}")

            lines.append(f"   실행 횟수: {sch['run_count']}회")
            lines.append("")

        lines.append(f"총 {len(schedules)}개 스케줄")

        return "\n".join(lines)


# 싱글톤 인스턴스
schedule_service = ScheduleService()
