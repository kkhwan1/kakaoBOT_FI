#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
채팅 히스토리 관리 모듈
메모리 기반으로 대화 내역을 저장하고 관리합니다.
"""

from datetime import datetime, timedelta
from collections import deque
import config

class ChatHistoryManager:
    def __init__(self):
        """채팅 히스토리 매니저 초기화"""
        # 방별 대화 기록 저장소 {room: {sender: deque([messages])}}
        self.histories = {}
        
        # 설정 로드
        self.history_config = config.get_chat_history_config()
        self.max_length = self.history_config.get("MAX_HISTORY_LENGTH", 4)
        self.timeout_ms = self.history_config.get("HISTORY_TIMEOUT", 1800000)  # 30분
        self.context_template = self.history_config.get("CONTEXT_TEMPLATE", "")
    
    def add_message(self, room: str, sender: str, message: str, response: str = None):
        """대화 기록 추가"""
        # 방이 없으면 생성
        if room not in self.histories:
            self.histories[room] = {}
        
        # 사용자가 없으면 생성
        if sender not in self.histories[room]:
            self.histories[room][sender] = deque(maxlen=self.max_length)
        
        # 현재 시간
        current_time = datetime.now()
        
        # 오래된 기록 제거
        self._cleanup_old_messages(room, sender, current_time)
        
        # 새 메시지 추가
        entry = {
            "time": current_time,
            "message": message,
            "response": response
        }
        
        self.histories[room][sender].append(entry)
    
    def get_context(self, room: str, sender: str, current_question: str) -> str:
        """이전 대화 컨텍스트 생성"""
        # 해당 방/사용자의 기록이 없으면 빈 문자열 반환
        if room not in self.histories or sender not in self.histories[room]:
            return ""
        
        current_time = datetime.now()
        
        # 오래된 기록 제거
        self._cleanup_old_messages(room, sender, current_time)
        
        # 대화 기록이 없으면 빈 문자열 반환
        if not self.histories[room][sender]:
            return ""
        
        # 이전 대화 포맷팅
        history_text = ""
        for entry in self.histories[room][sender]:
            if entry["message"]:
                history_text += f"사용자: {entry['message']}\n"
            if entry["response"]:
                history_text += f"AI: {entry['response']}\n"
        
        # 템플릿이 있으면 적용
        if self.context_template and history_text:
            context = self.context_template.replace("{history}", history_text.strip())
            context = context.replace("{question}", current_question)
            return context
        
        return history_text
    
    def _cleanup_old_messages(self, room: str, sender: str, current_time: datetime):
        """오래된 메시지 정리"""
        if room not in self.histories or sender not in self.histories[room]:
            return
        
        # 시간 제한 계산 (밀리초를 초로 변환)
        timeout_seconds = self.timeout_ms / 1000
        cutoff_time = current_time - timedelta(seconds=timeout_seconds)
        
        # 새로운 deque 생성 (시간 내의 메시지만)
        new_messages = deque(maxlen=self.max_length)
        
        for entry in self.histories[room][sender]:
            if entry["time"] > cutoff_time:
                new_messages.append(entry)
        
        self.histories[room][sender] = new_messages
    
    def clear_history(self, room: str = None, sender: str = None):
        """대화 기록 초기화"""
        if room and sender:
            # 특정 사용자의 기록만 삭제
            if room in self.histories and sender in self.histories[room]:
                self.histories[room][sender].clear()
        elif room:
            # 특정 방의 모든 기록 삭제
            if room in self.histories:
                self.histories[room].clear()
        else:
            # 모든 기록 삭제
            self.histories.clear()
    
    def get_history_summary(self, room: str, sender: str) -> str:
        """대화 기록 요약 (디버깅용)"""
        if room not in self.histories or sender not in self.histories[room]:
            return "대화 기록 없음"
        
        count = len(self.histories[room][sender])
        if count == 0:
            return "대화 기록 없음"
        
        last_entry = self.histories[room][sender][-1]
        last_time = last_entry["time"].strftime("%H:%M:%S")
        
        return f"대화 {count}개 저장됨 (마지막: {last_time})"

# 전역 인스턴스 생성
chat_history = ChatHistoryManager()