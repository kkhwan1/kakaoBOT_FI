#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터베이스 서비스 모듈
DB 연결 및 쿼리 실행을 담당
"""

import pymysql
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager
from config import DB_CONFIG
from utils.debug_logger import debug_logger
from utils.text_utils import log


def get_conn():
    """
    데이터베이스 연결 생성
    
    Returns:
        tuple: (connection, cursor) 객체
    """
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG.get('charset', 'utf8mb4'),
            cursorclass=pymysql.cursors.DictCursor  # 딕셔너리 형태로 결과 반환
        )
        return conn, conn.cursor()
    except Exception as e:
        debug_logger.error(f"DB 연결 실패: {e}")
        raise


@contextmanager
def db_connection():
    """
    컨텍스트 매니저를 사용한 안전한 DB 연결
    
    Usage:
        with db_connection() as (conn, cursor):
            cursor.execute(query, params)
            result = cursor.fetchall()
    """
    conn = None
    try:
        conn, cursor = get_conn()
        yield conn, cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        debug_logger.error(f"DB 작업 중 오류: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: Tuple = None, commit: bool = True) -> int:
    """
    쿼리 실행 (INSERT, UPDATE, DELETE)
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
        commit: 자동 커밋 여부
    
    Returns:
        int: 영향받은 행 수
    """
    with db_connection() as (conn, cursor):
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor.rowcount


def fetch_one(query: str, params: Tuple = None) -> Optional[Dict]:
    """
    단일 행 조회
    
    Args:
        query: SELECT 쿼리
        params: 쿼리 파라미터
    
    Returns:
        Dict: 조회 결과 (딕셔너리)
    """
    with db_connection() as (conn, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()


def fetch_all(query: str, params: Tuple = None, limit: int = None) -> List[Dict]:
    """
    다중 행 조회
    
    Args:
        query: SELECT 쿼리
        params: 쿼리 파라미터
        limit: 최대 행 수
    
    Returns:
        List[Dict]: 조회 결과 리스트
    """
    with db_connection() as (conn, cursor):
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, params)
        return cursor.fetchall()


class DatabaseService:
    """
    데이터베이스 서비스 클래스
    특정 도메인의 DB 작업을 캡슐화
    """
    
    def __init__(self, table_name: str = None):
        self.table_name = table_name
    
    def save_message(self, room: str, sender: str, msg: str, reply: str = None):
        """메시지 저장"""
        query = """
        INSERT INTO kt_message (room, sender, msg, reply, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """
        params = (room, sender, msg, reply)
        return execute_query(query, params)
    
    def get_chat_history(self, room: str, sender: str, limit: int = 10) -> List[Dict]:
        """채팅 히스토리 조회"""
        query = """
        SELECT msg, reply, created_at
        FROM kt_message
        WHERE room = %s AND sender = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        params = (room, sender, limit)
        return fetch_all(query, params)
    
    def get_talk_statistics(self, room: str, date_offset: int = 0) -> List[Dict]:
        """대화 통계 조회"""
        query = """
        SELECT sender, COUNT(*) AS cnt
        FROM kt_message 
        WHERE 
            room = %s
            AND DATE(created_at) = CURDATE() + %s
            AND sender NOT IN ('윤봇', '오픈채팅봇', '팬다 Jr.')
        GROUP BY sender
        ORDER BY cnt DESC
        LIMIT 10
        """
        params = (room, date_offset)
        return fetch_all(query, params)
    
    def get_room_list(self) -> List[str]:
        """활성 방 목록 조회"""
        query = """
        SELECT DISTINCT room
        FROM kt_message
        WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY room
        """
        results = fetch_all(query)
        return [row['room'] for row in results]
    
    def cleanup_old_messages(self, days: int = 30) -> int:
        """오래된 메시지 정리"""
        query = """
        DELETE FROM kt_message
        WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        return execute_query(query, (days,))


# 싱글톤 인스턴스
db_service = DatabaseService()