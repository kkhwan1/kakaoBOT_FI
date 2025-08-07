"""
메시지 핸들러 모듈
메시지 전송 및 처리 관련 기능
"""

import json
import time
from typing import Optional, Dict, Any, List
from socket import socket, AF_INET, SOCK_STREAM
from utils.debug_logger import debug_logger
from config import BOT_CONFIG, is_room_enabled, is_admin_user, get_ai_style


class MessageHandler:
    """
    메시지 처리 및 전송 클래스
    """
    
    def __init__(self, ip: str = "172.30.1.25", port: int = 4006):
        self.ip = ip
        self.port = port
        self.message_queue = []
        self.message_history = {}
        self.rate_limit = 0.5  # 메시지 간 최소 간격 (초)
        self.last_send_time = 0
    
    def send_message(self, room: str, msg: str) -> bool:
        """
        카카오톡 메시지 전송
        
        Args:
            room: 방 이름
            msg: 전송할 메시지
            
        Returns:
            bool: 전송 성공 여부
        """
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_send_time < self.rate_limit:
                time.sleep(self.rate_limit - (current_time - self.last_send_time))
            
            # 소켓 연결 및 전송
            client_socket = socket(AF_INET, SOCK_STREAM)
            client_socket.settimeout(5)  # 5초 타임아웃
            client_socket.connect((self.ip, self.port))
            
            data = {
                "room": room,
                "msg": msg
            }
            
            client_socket.send(json.dumps(data).encode("utf-8"))
            client_socket.close()
            
            self.last_send_time = time.time()
            
            # 히스토리 저장
            self._save_to_history(room, msg, is_bot=True)
            
            debug_logger.info(f"메시지 전송 성공: {room} - {msg[:50]}...")
            return True
            
        except Exception as e:
            debug_logger.error(f"메시지 전송 실패: {e}")
            return False
    
    def send_split_message(self, room: str, msg: str, max_length: int = 500) -> bool:
        """
        긴 메시지를 분할하여 전송
        
        Args:
            room: 방 이름
            msg: 전송할 메시지
            max_length: 최대 메시지 길이
            
        Returns:
            bool: 전송 성공 여부
        """
        try:
            if len(msg) <= max_length:
                return self.send_message(room, msg)
            
            # 메시지 분할
            parts = []
            lines = msg.split('\n')
            current_part = ""
            
            for line in lines:
                if len(current_part) + len(line) + 1 <= max_length:
                    if current_part:
                        current_part += '\n'
                    current_part += line
                else:
                    if current_part:
                        parts.append(current_part)
                    current_part = line
            
            if current_part:
                parts.append(current_part)
            
            # 각 파트 전송
            for i, part in enumerate(parts):
                if i > 0:
                    time.sleep(0.5)  # 파트 간 딜레이
                if not self.send_message(room, part):
                    return False
            
            return True
            
        except Exception as e:
            debug_logger.error(f"분할 메시지 전송 실패: {e}")
            return False
    
    def queue_message(self, room: str, msg: str):
        """
        메시지를 큐에 추가
        
        Args:
            room: 방 이름
            msg: 전송할 메시지
        """
        self.message_queue.append({
            'room': room,
            'msg': msg,
            'timestamp': time.time()
        })
    
    def process_queue(self) -> int:
        """
        큐에 있는 메시지들을 처리
        
        Returns:
            int: 처리된 메시지 수
        """
        processed = 0
        while self.message_queue:
            item = self.message_queue.pop(0)
            if self.send_message(item['room'], item['msg']):
                processed += 1
            else:
                # 실패한 메시지는 다시 큐에 추가
                self.message_queue.insert(0, item)
                break
        
        return processed
    
    def _save_to_history(self, room: str, msg: str, is_bot: bool = False):
        """
        메시지 히스토리 저장
        
        Args:
            room: 방 이름
            msg: 메시지
            is_bot: 봇 메시지 여부
        """
        if room not in self.message_history:
            self.message_history[room] = []
        
        self.message_history[room].append({
            'msg': msg,
            'is_bot': is_bot,
            'timestamp': time.time()
        })
        
        # 최대 100개까지만 유지
        if len(self.message_history[room]) > 100:
            self.message_history[room] = self.message_history[room][-100:]
    
    def get_history(self, room: str, limit: int = 10) -> List[Dict]:
        """
        메시지 히스토리 조회
        
        Args:
            room: 방 이름
            limit: 조회할 메시지 수
            
        Returns:
            List[Dict]: 메시지 히스토리
        """
        if room not in self.message_history:
            return []
        
        return self.message_history[room][-limit:]
    
    def clear_history(self, room: str = None):
        """
        메시지 히스토리 초기화
        
        Args:
            room: 방 이름 (None이면 전체 초기화)
        """
        if room:
            if room in self.message_history:
                del self.message_history[room]
        else:
            self.message_history.clear()


# 싱글톤 인스턴스
message_handler = MessageHandler()

# 기존 함수 호환성을 위한 래퍼
def send_message(room: str, msg: str):
    """카카오톡 메시지 전송 함수 (레거시 호환)
    
    Args:
        room: 방 이름
        msg: 전송할 메시지
    """
    return message_handler.send_message(room, msg)