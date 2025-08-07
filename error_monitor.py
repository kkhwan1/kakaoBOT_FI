"""
========================================
오류 모니터링 및 알림 시스템
========================================
명령어 실패 추적, 관리자 알림, 오류율 기반 자동 비활성화
"""

import json
import datetime
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import os
import threading
import time

class ErrorMonitor:
    """오류 모니터링 시스템"""
    
    def __init__(self, error_log_file: str = "error_logs.json", 
                 stats_file: str = "command_stats.json"):
        self.error_log_file = error_log_file
        self.stats_file = stats_file
        
        # 오류 로그 (최근 100개만 유지)
        self.error_logs = deque(maxlen=100)
        
        # 명령어별 오류 통계
        self.error_stats = defaultdict(lambda: {
            'total_calls': 0,
            'error_count': 0,
            'last_error': None,
            'error_rate': 0.0,
            'consecutive_errors': 0
        })
        
        # 명령어별 사용 통계
        self.usage_stats = defaultdict(lambda: {
            'count': 0,
            'last_used': None,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        })
        
        # 자동 비활성화된 명령어
        self.disabled_commands = set()
        
        # 오류율 임계값
        self.ERROR_RATE_THRESHOLD = 0.5  # 50% 이상 오류시
        self.CONSECUTIVE_ERROR_THRESHOLD = 5  # 연속 5회 오류시
        
        # 관리자 알림 큐
        self.admin_alerts = deque(maxlen=50)
        
        # 로드 기존 데이터
        self._load_data()
        
        # 자동 저장 스레드
        self._start_auto_save()
    
    def _load_data(self):
        """기존 데이터 로드"""
        # 오류 로그 로드
        if os.path.exists(self.error_log_file):
            try:
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.error_logs = deque(data.get('logs', []), maxlen=100)
                    self.error_stats = defaultdict(lambda: {
                        'total_calls': 0,
                        'error_count': 0,
                        'last_error': None,
                        'error_rate': 0.0,
                        'consecutive_errors': 0
                    }, data.get('stats', {}))
                    self.disabled_commands = set(data.get('disabled', []))
            except:
                pass
        
        # 사용 통계 로드
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.usage_stats = defaultdict(lambda: {
                        'count': 0,
                        'last_used': None,
                        'avg_response_time': 0.0,
                        'total_response_time': 0.0
                    }, data.get('usage', {}))
            except:
                pass
    
    def _save_data(self):
        """데이터 저장"""
        # 오류 로그 저장
        try:
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'logs': list(self.error_logs),
                    'stats': dict(self.error_stats),
                    'disabled': list(self.disabled_commands),
                    'last_updated': datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"오류 로그 저장 실패: {e}")
        
        # 사용 통계 저장
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'usage': dict(self.usage_stats),
                    'last_updated': datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"사용 통계 저장 실패: {e}")
    
    def _start_auto_save(self):
        """자동 저장 스레드 시작"""
        def auto_save():
            while True:
                time.sleep(300)  # 5분마다 저장
                self._save_data()
        
        thread = threading.Thread(target=auto_save, daemon=True)
        thread.start()
    
    def log_command_start(self, command: str, room: str, sender: str) -> float:
        """명령어 시작 기록"""
        start_time = time.time()
        
        # 비활성화된 명령어 체크
        if command in self.disabled_commands:
            return -1  # 비활성화된 명령어
        
        # 통계 업데이트
        self.error_stats[command]['total_calls'] += 1
        self.usage_stats[command]['count'] += 1
        self.usage_stats[command]['last_used'] = datetime.datetime.now().isoformat()
        
        return start_time
    
    def log_command_success(self, command: str, start_time: float):
        """명령어 성공 기록"""
        if start_time < 0:
            return  # 비활성화된 명령어
        
        # 응답 시간 기록
        response_time = time.time() - start_time
        stats = self.usage_stats[command]
        stats['total_response_time'] += response_time
        stats['avg_response_time'] = stats['total_response_time'] / stats['count']
        
        # 연속 오류 카운터 리셋
        self.error_stats[command]['consecutive_errors'] = 0
    
    def log_command_error(self, command: str, room: str, sender: str, 
                         error_msg: str, start_time: float) -> bool:
        """
        명령어 오류 기록
        Returns: True if command should be disabled
        """
        if start_time < 0:
            return False  # 이미 비활성화됨
        
        # 오류 로그 추가
        error_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'command': command,
            'room': room,
            'sender': sender,
            'error': error_msg,
            'response_time': time.time() - start_time if start_time else 0
        }
        self.error_logs.append(error_entry)
        
        # 오류 통계 업데이트
        stats = self.error_stats[command]
        stats['error_count'] += 1
        stats['last_error'] = error_entry
        stats['consecutive_errors'] += 1
        stats['error_rate'] = stats['error_count'] / stats['total_calls']
        
        # 관리자 알림 필요 여부 확인
        should_alert = False
        alert_msg = None
        
        # 연속 오류 체크
        if stats['consecutive_errors'] >= self.CONSECUTIVE_ERROR_THRESHOLD:
            should_alert = True
            alert_msg = f"⚠️ {command} 연속 {stats['consecutive_errors']}회 오류 발생!"
        
        # 오류율 체크
        if stats['total_calls'] >= 10 and stats['error_rate'] >= self.ERROR_RATE_THRESHOLD:
            should_alert = True
            alert_msg = f"🚨 {command} 오류율 {stats['error_rate']*100:.1f}% 초과!"
            
            # 자동 비활성화
            self.disabled_commands.add(command)
            alert_msg += f"\n🔒 명령어가 자동 비활성화되었습니다."
            
            return True  # 비활성화됨
        
        # 관리자 알림 추가
        if should_alert and alert_msg:
            self.admin_alerts.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'message': alert_msg,
                'error': error_entry
            })
        
        return False
    
    def get_error_logs(self, limit: int = 20) -> str:
        """최근 오류 로그 조회"""
        if not self.error_logs:
            return "📋 최근 오류 로그가 없습니다."
        
        msg = f"🔴 최근 오류 로그 (최대 {limit}개)\n\n"
        
        for log in list(self.error_logs)[-limit:]:
            timestamp = log['timestamp'].split('T')[1].split('.')[0]
            msg += f"⏰ {timestamp}\n"
            msg += f"📍 {log['command']} ({log['room']})\n"
            msg += f"👤 {log['sender']}\n"
            msg += f"❌ {log['error'][:100]}\n"
            msg += f"⏱️ {log['response_time']:.2f}초\n\n"
        
        return msg
    
    def get_error_stats(self) -> str:
        """오류 통계 조회"""
        if not self.error_stats:
            return "📊 오류 통계가 없습니다."
        
        msg = "📊 명령어별 오류 통계\n\n"
        
        # 오류율 높은 순으로 정렬
        sorted_stats = sorted(
            self.error_stats.items(),
            key=lambda x: x[1]['error_rate'],
            reverse=True
        )
        
        for cmd, stats in sorted_stats[:10]:
            error_rate = stats['error_rate'] * 100
            status = "🔒 비활성" if cmd in self.disabled_commands else "✅ 활성"
            
            msg += f"【{cmd}】 {status}\n"
            msg += f"  호출: {stats['total_calls']}회\n"
            msg += f"  오류: {stats['error_count']}회 ({error_rate:.1f}%)\n"
            msg += f"  연속오류: {stats['consecutive_errors']}회\n\n"
        
        if self.disabled_commands:
            msg += f"\n🔒 비활성화된 명령어: {', '.join(self.disabled_commands)}"
        
        return msg
    
    def get_usage_stats(self) -> str:
        """사용 통계 조회"""
        if not self.usage_stats:
            return "📊 사용 통계가 없습니다."
        
        msg = "📊 명령어 사용 통계 TOP 10\n\n"
        
        # 사용 횟수 높은 순으로 정렬
        sorted_stats = sorted(
            self.usage_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for i, (cmd, stats) in enumerate(sorted_stats[:10], 1):
            msg += f"{i}. {cmd}: {stats['count']}회\n"
            msg += f"   평균응답: {stats['avg_response_time']:.2f}초\n"
        
        return msg
    
    def get_admin_alerts(self) -> List[Dict]:
        """관리자 알림 조회"""
        alerts = list(self.admin_alerts)
        self.admin_alerts.clear()  # 조회 후 클리어
        return alerts
    
    def enable_command(self, command: str) -> bool:
        """명령어 수동 활성화"""
        if command in self.disabled_commands:
            self.disabled_commands.remove(command)
            # 연속 오류 카운터 리셋
            if command in self.error_stats:
                self.error_stats[command]['consecutive_errors'] = 0
            return True
        return False
    
    def reset_command_stats(self, command: str):
        """명령어 통계 리셋"""
        if command in self.error_stats:
            self.error_stats[command] = {
                'total_calls': 0,
                'error_count': 0,
                'last_error': None,
                'error_rate': 0.0,
                'consecutive_errors': 0
            }
        if command in self.usage_stats:
            self.usage_stats[command] = {
                'count': 0,
                'last_used': None,
                'avg_response_time': 0.0,
                'total_response_time': 0.0
            }
    
    def get_performance_recommendations(self) -> Dict[str, List[str]]:
        """성능 최적화 추천"""
        recommendations = {
            'high_priority_cache': [],  # 자주 사용되는 명령어
            'low_priority_cache': [],   # 거의 사용 안되는 명령어
            'needs_optimization': []    # 응답 시간이 긴 명령어
        }
        
        # 사용 빈도 분석
        if self.usage_stats:
            sorted_by_usage = sorted(
                self.usage_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            total_usage = sum(s[1]['count'] for s in sorted_by_usage)
            
            for cmd, stats in sorted_by_usage:
                usage_ratio = stats['count'] / total_usage if total_usage > 0 else 0
                
                # 상위 20% 명령어는 우선 캐싱
                if usage_ratio > 0.05:
                    recommendations['high_priority_cache'].append(cmd)
                # 하위 20% 명령어는 캐시 시간 단축
                elif usage_ratio < 0.01:
                    recommendations['low_priority_cache'].append(cmd)
                
                # 응답 시간이 5초 이상인 명령어는 최적화 필요
                if stats['avg_response_time'] > 5.0:
                    recommendations['needs_optimization'].append(
                        f"{cmd} (평균 {stats['avg_response_time']:.1f}초)"
                    )
        
        return recommendations

# 전역 에러 모니터 인스턴스
error_monitor = ErrorMonitor()