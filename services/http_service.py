#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP 서비스 모듈
HTTP 요청 처리 및 응답 파싱을 담당
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, Union
from utils.debug_logger import debug_logger
from utils.text_utils import log


def request(
    url: str,
    method: str = "get",
    result: str = "text",
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    data: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    timeout: int = 10
) -> Optional[Union[str, Dict, BeautifulSoup]]:
    """
    통합 HTTP 요청 함수
    
    Args:
        url: 요청 URL
        method: HTTP 메소드 (get/post)
        result: 응답 형식 (text/json/bs)
        params: URL 파라미터
        headers: 요청 헤더
        data: POST 데이터 (form-data)
        json_data: POST JSON 데이터
        timeout: 타임아웃 (초)
    
    Returns:
        result 타입에 따른 응답 데이터
    """
    try:
        # 기본 헤더 설정
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        # 요청 실행
        if method.lower() == "get":
            response = requests.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=timeout
            )
        elif method.lower() == "post":
            if json_data:
                response = requests.post(
                    url,
                    json=json_data,
                    headers=headers,
                    timeout=timeout
                )
            else:
                response = requests.post(
                    url,
                    data=data,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # 응답 상태 확인
        response.raise_for_status()
        
        # 결과 형식에 따른 처리
        if result == "json":
            return response.json()
        elif result == "bs":
            return BeautifulSoup(response.text, 'html.parser')
        else:  # text
            return response.text
            
    except requests.exceptions.Timeout:
        debug_logger.error(f"Request timeout: {url}")
        return None
    except requests.exceptions.ConnectionError:
        debug_logger.error(f"Connection error: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        debug_logger.error(f"HTTP error {e.response.status_code}: {url}")
        return None
    except Exception as e:
        debug_logger.error(f"Request error: {e}")
        return None


def fetch_json(url: str, **kwargs) -> Optional[Dict]:
    """JSON 데이터 요청 헬퍼"""
    return request(url, result="json", **kwargs)


def fetch_html(url: str, **kwargs) -> Optional[BeautifulSoup]:
    """HTML 파싱 요청 헬퍼"""
    return request(url, result="bs", **kwargs)


class HTTPClient:
    """
    세션 기반 HTTP 클라이언트
    쿠키 유지 및 연결 재사용을 위한 클래스
    """
    
    def __init__(self, base_url: str = None, default_headers: Dict = None):
        self.session = requests.Session()
        self.base_url = base_url
        
        # 기본 헤더 설정
        default_headers = default_headers or {}
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            **default_headers
        })
    
    def get(self, path: str, **kwargs) -> requests.Response:
        """GET 요청"""
        url = self._build_url(path)
        return self.session.get(url, **kwargs)
    
    def post(self, path: str, **kwargs) -> requests.Response:
        """POST 요청"""
        url = self._build_url(path)
        return self.session.post(url, **kwargs)
    
    def _build_url(self, path: str) -> str:
        """URL 조합"""
        if self.base_url and not path.startswith('http'):
            return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        return path
    
    def close(self):
        """세션 종료"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()