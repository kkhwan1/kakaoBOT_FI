"""
텍스트 유틸리티 모듈
텍스트 처리 및 정제 관련 함수들
"""

import re
from datetime import datetime


def log(message: str):
    """로그 출력 함수
    
    Args:
        message: 출력할 로그 메시지
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def clean_for_kakao(text: str) -> str:
    """카카오톡 메신저용 텍스트 정제 (메신저봇 호환성 강화)
    
    Args:
        text: 정제할 텍스트
        
    Returns:
        str: 정제된 텍스트
    """
    if not text:
        return ""
    
    try:
        # 1. 마크다운 문법 제거 (** * __ _ ` # ~ 등)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** → bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic* → italic  
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __underline__ → underline
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_ → italic
        text = re.sub(r'`([^`]+)`', r'\1', text)        # `code` → code
        text = re.sub(r'#{1,6}\s*', '', text)           # ### header → header
        text = re.sub(r'~([^~]+)~', r'\1', text)        # ~strike~ → strike
        
        # 마크다운 리스트 문법 정리
        text = re.sub(r'^\s*[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)  # * item → • item
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)       # 1. item → item
        
        # 2. 참조 번호 제거 [1], [2] 등
        text = re.sub(r'\[\d+\]', '', text)
        
        # 3. URL 제거
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'www\.[^\s]+', '', text)
        
        # 4. HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 5. 연속된 공백과 줄바꿈 정리
        text = re.sub(r'\n{3,}', '\n\n', text)  # 3개 이상 연속 줄바꿈 → 2개로
        text = re.sub(r' {2,}', ' ', text)      # 연속 공백 → 1개로
        
        # 6. 앞뒤 공백 제거
        text = text.strip()
        
        # 7. 길이 제한 (카카오톡 메시지 최대 길이)
        MAX_LENGTH = 5000
        if len(text) > MAX_LENGTH:
            text = text[:MAX_LENGTH-20] + "...\n(내용이 너무 길어 생략됨)"
        
        return text
        
    except Exception as e:
        print(f"텍스트 정제 오류: {e}")
        return text[:5000] if text else ""