"""
API 키 관리 모듈
환경 변수에서 API 키를 로드하고 관리합니다.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class APIManager:
    """API 키 중앙 관리 클래스"""
    
    # Google Gemini API 키 (3개 로테이션)
    GEMINI_API_KEYS: List[str] = [
        os.getenv('GEMINI_API_KEY_1', ''),
        os.getenv('GEMINI_API_KEY_2', ''),
        os.getenv('GEMINI_API_KEY_3', '')
    ]
    
    # Perplexity API 키 (2개 로테이션)
    PERPLEXITY_API_KEYS: List[str] = [
        os.getenv('PERPLEXITY_API_KEY_1', ''),
        os.getenv('PERPLEXITY_API_KEY_2', '')
    ]
    
    # ScrapingBee API 키 (2개 로테이션)
    SCRAPINGBEE_API_KEYS: List[str] = [
        os.getenv('SCRAPINGBEE_API_KEY_1', ''),
        os.getenv('SCRAPINGBEE_API_KEY_2', '')
    ]
    
    # 단일 API 키들
    CLAUDE_API_KEY: str = os.getenv('CLAUDE_API_KEY', '')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    YOUTUBE_API_KEY: str = os.getenv('YOUTUBE_API_KEY', '')
    
    # 인덱스 관리
    _gemini_index: int = 0
    _perplexity_index: int = 0
    _scrapingbee_index: int = 0
    
    @classmethod
    def get_next_gemini_key(cls) -> str:
        """다음 Gemini API 키를 로테이션하여 반환"""
        if not any(cls.GEMINI_API_KEYS):
            raise ValueError("Gemini API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        key = cls.GEMINI_API_KEYS[cls._gemini_index]
        cls._gemini_index = (cls._gemini_index + 1) % len(cls.GEMINI_API_KEYS)
        return key
    
    @classmethod
    def get_next_perplexity_key(cls) -> str:
        """다음 Perplexity API 키를 로테이션하여 반환"""
        if not any(cls.PERPLEXITY_API_KEYS):
            raise ValueError("Perplexity API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        key = cls.PERPLEXITY_API_KEYS[cls._perplexity_index]
        cls._perplexity_index = (cls._perplexity_index + 1) % len(cls.PERPLEXITY_API_KEYS)
        return key
    
    @classmethod
    def get_next_scrapingbee_key(cls) -> str:
        """다음 ScrapingBee API 키를 로테이션하여 반환"""
        if not any(cls.SCRAPINGBEE_API_KEYS):
            raise ValueError("ScrapingBee API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        key = cls.SCRAPINGBEE_API_KEYS[cls._scrapingbee_index]
        cls._scrapingbee_index = (cls._scrapingbee_index + 1) % len(cls.SCRAPINGBEE_API_KEYS)
        return key
    
    @classmethod
    def get_claude_key(cls) -> str:
        """Claude API 키 반환"""
        if not cls.CLAUDE_API_KEY:
            raise ValueError("Claude API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return cls.CLAUDE_API_KEY
    
    @classmethod
    def get_openai_key(cls) -> str:
        """OpenAI API 키 반환"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return cls.OPENAI_API_KEY
    
    @classmethod
    def get_youtube_key(cls) -> str:
        """YouTube API 키 반환"""
        if not cls.YOUTUBE_API_KEY:
            raise ValueError("YouTube API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return cls.YOUTUBE_API_KEY
    
    @classmethod
    def validate_keys(cls) -> dict:
        """모든 API 키 상태 확인"""
        status = {
            'gemini': sum(1 for key in cls.GEMINI_API_KEYS if key),
            'perplexity': sum(1 for key in cls.PERPLEXITY_API_KEYS if key),
            'scrapingbee': sum(1 for key in cls.SCRAPINGBEE_API_KEYS if key),
            'claude': bool(cls.CLAUDE_API_KEY),
            'openai': bool(cls.OPENAI_API_KEY),
            'youtube': bool(cls.YOUTUBE_API_KEY)
        }
        return status

# 기존 코드 호환성을 위한 전역 변수 (점진적 마이그레이션)
API_KEYS = {
    "GEMINI": APIManager.GEMINI_API_KEYS[0] if APIManager.GEMINI_API_KEYS[0] else "YOUR_GEMINI_API_KEY_HERE",
    "CLAUDE": APIManager.CLAUDE_API_KEY or "YOUR_CLAUDE_API_KEY_HERE",
    "OPENAI": APIManager.OPENAI_API_KEY or "YOUR_OPENAI_API_KEY_HERE",
    "YOUTUBE": APIManager.YOUTUBE_API_KEY or "YOUR_YOUTUBE_API_KEY_HERE"
}