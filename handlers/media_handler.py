#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
미디어 핸들러 모듈
YouTube, 영화, 사진 등 미디어 관련 명령어 처리
"""

import re
import random
from datetime import datetime
from utils.text_utils import clean_for_kakao
from utils.debug_logger import debug_logger

# request 함수 import
try:
    from fn import request, gemini15_flash
except ImportError:
    import requests
    from bs4 import BeautifulSoup
    
    def request(url, method="get", result="text", params=None, headers=None):
        """HTTP 요청 헬퍼 함수"""
        try:
            if method.lower() == "get":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, params=params, headers=headers, timeout=10)
            
            if result == "json":
                return response.json()
            elif result == "bs":
                return BeautifulSoup(response.text, 'html.parser')
            else:
                return response.text
        except Exception as e:
            print(f"Request error: {e}")
            return None

    def gemini15_flash(system, question, retry_count=0, use_search=True):
        """Gemini 폴백 - fn.py 사용 불가시"""
        return None


def youtube_popular_all(room: str, sender: str, msg: str):
    """유튜브 인기 급상승 동영상 전체"""
    url = 'https://www.youtube.com/feed/trending'
    headers = {'Accept-Language': 'ko-KR,ko;q=0.9'}
    
    try:
        result = request(url, method="get", result="text", headers=headers)
        if not result:
            return "YouTube 인기 동영상을 불러올 수 없습니다."
        
        # 간단한 정규식으로 비디오 정보 추출
        video_pattern = r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"'
        videos = re.findall(video_pattern, result)[:10]  # 상위 10개
        
        if not videos:
            return "인기 동영상을 찾을 수 없습니다."
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"🔥 YouTube 인기 급상승\n📅 {current_time} 기준\n{'='*25}"
        
        for idx, (video_id, title) in enumerate(videos, 1):
            # HTML 엔티티 디코딩
            title = title.replace('\\u0026', '&').replace('\\u003c', '<').replace('\\u003e', '>')
            title = title[:50] + '...' if len(title) > 50 else title
            link = f"https://youtu.be/{video_id}"
            send_msg += f"\n\n{idx}. {title}\n{link}"
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"YouTube 인기 동영상 오류: {str(e)}")
        return "YouTube 인기 동영상을 불러오는 중 오류가 발생했습니다."


def youtube_popular_random(room: str, sender: str, msg: str):
    """유튜브 인기 급상승 동영상 랜덤 1개"""
    url = 'https://www.youtube.com/feed/trending'
    headers = {'Accept-Language': 'ko-KR,ko;q=0.9'}
    
    try:
        result = request(url, method="get", result="text", headers=headers)
        if not result:
            return "YouTube 인기 동영상을 불러올 수 없습니다."
        
        # 간단한 정규식으로 비디오 정보 추출
        video_pattern = r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"'
        videos = re.findall(video_pattern, result)[:20]  # 상위 20개 중에서 선택
        
        if not videos:
            return "인기 동영상을 찾을 수 없습니다."
        
        # 랜덤 선택
        video_id, title = random.choice(videos)
        
        # HTML 엔티티 디코딩
        title = title.replace('\\u0026', '&').replace('\\u003c', '<').replace('\\u003e', '>')
        link = f"https://youtu.be/{video_id}"
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"🎲 YouTube 랜덤 인기 동영상\n📅 {current_time} 기준\n{'='*25}\n\n"
        send_msg += f"🎬 {title}\n{link}"
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"YouTube 랜덤 동영상 오류: {str(e)}")
        return "YouTube 인기 동영상을 불러오는 중 오류가 발생했습니다."


def summarize(room: str, sender: str, msg: str):
    """YouTube 동영상 요약"""
    try:
        # YouTube URL 추출
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([\w-]+)',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([\w-]+)'
        ]
        
        video_id = None
        for pattern in youtube_patterns:
            match = re.search(pattern, msg)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            return "YouTube URL을 찾을 수 없습니다."
        
        # YouTube API를 통한 정보 가져오기 (간단 버전)
        from utils.api_manager import APIManager
        youtube_key = APIManager.get_youtube_key()
        
        if youtube_key:
            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={youtube_key}&part=snippet"
            result = request(api_url, method="get", result="json")
            
            if result and 'items' in result and result['items']:
                video_info = result['items'][0]['snippet']
                title = video_info.get('title', '제목 없음')
                description = video_info.get('description', '')[:200]
                
                # Gemini로 요약 요청
                summary_prompt = f"""
다음 YouTube 동영상을 간단히 요약해주세요.
제목: {title}
설명: {description}

100자 이내로 핵심만 요약하세요.
"""
                
                summary = gemini15_flash("간단히 요약", summary_prompt)
                if summary:
                    return f"📹 {title}\n\n📝 요약:\n{clean_for_kakao(summary)}"
        
        return f"YouTube 동영상 정보를 가져올 수 없습니다.\nhttps://youtu.be/{video_id}"
        
    except Exception as e:
        debug_logger.error(f"YouTube 요약 오류: {str(e)}")
        return "동영상 요약 중 오류가 발생했습니다."


def photo(room: str, sender: str, msg: str):
    """사진 검색 (Unsplash API)"""
    keyword = msg.replace("/사진", "").strip()
    if not keyword:
        return "🖼️ 사용법: /사진 [검색어]"
    
    try:
        # Unsplash API (무료 버전)
        url = f"https://source.unsplash.com/featured/?{keyword}"
        
        send_msg = f"🖼️ '{keyword}' 사진\n"
        send_msg += f"📸 {url}\n"
        send_msg += f"\n💡 Unsplash 제공"
        
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"사진 검색 오류: {str(e)}")
        return "사진을 불러오는 중 오류가 발생했습니다."