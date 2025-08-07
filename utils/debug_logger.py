#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
디버그 로거 모듈
"""

import datetime
import os

class DebugLogger:
    def __init__(self):
        self.enabled = True
        self.log_file = None
        
    def log_debug(self, message):
        """디버그 메시지 로깅"""
        if self.enabled:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] DEBUG: {message}"
            print(log_message)
            
            # 파일로도 저장 (선택적)
            if self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(log_message + '\n')
                except:
                    pass
    
    def log_error(self, message):
        """에러 메시지 로깅"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] ERROR: {message}"
        print(log_message)
        
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_message + '\n')
            except:
                pass
    
    def set_enabled(self, enabled):
        """로깅 활성화/비활성화"""
        self.enabled = enabled
    
    def set_log_file(self, file_path):
        """로그 파일 경로 설정"""
        self.log_file = file_path

# 싱글톤 인스턴스
debug_logger = DebugLogger()