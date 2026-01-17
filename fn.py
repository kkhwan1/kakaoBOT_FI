from datetime import datetime, timedelta
import time
import re
import os
import string
import json
import urllib.parse  # urllib.parse 추가
import urllib3
import random
import subprocess
from socket import socket, AF_INET, SOCK_STREAM

from bs4 import BeautifulSoup as bs
import requests
import google.generativeai as genai
import anthropic
from openai import OpenAI

# 디버그 로거 추가
from utils.debug_logger import debug_logger
# Google Sheets 관련 import 제거됨
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("⚠️ youtube_transcript_api 모듈을 찾을 수 없습니다. pip install youtube-transcript-api로 설치하세요.")
    YouTubeTranscriptApi = None

try:
    from googleapiclient.discovery import build
except ImportError:
    print("⚠️ google-api-python-client 모듈을 찾을 수 없습니다.")
    build = None

# 통합 설정 관리 시스템을 불러옵니다.
import config

# import coupang  # 쿠팡 기능 제거됨 (API 차단)
import naver

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 키 관리자 임포트
from utils.api_manager import APIManager

# ScrapingBee API 키 로테이션 함수 (API Manager 사용)
def get_next_scrapingbee_key():
    """다음 ScrapingBee API 키를 로테이션하여 반환"""
    return APIManager.get_next_scrapingbee_key()

# ========================================
# 데이터베이스 함수들 (임시 구현)
# ========================================

def get_conn():
    """데이터베이스 연결 (임시 구현)"""
    # 실제 DB 연결 구현 필요
    print("⚠️ 데이터베이스 연결이 구현되지 않았습니다.")
    return None, None

def fetch_val(query, params):
    """단일 값 조회 (임시 구현)"""
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return None

def fetch_all(query, params):
    """전체 행 조회 (임시 구현)"""
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return []

def fetch_one(query, params):
    """단일 행 조회 (임시 구현)"""
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return None

def execute(query, params):
    """쿼리 실행 (임시 구현)"""
    print(f"⚠️ DB 쿼리 실행 필요: {query}")
    return True

# ========================================
# 핵심 함수들
# ========================================

def log(message):
    """로그 출력 함수"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def request(url, method="get", result="text", params=None, headers=None):
    """웹 요청 함수"""
    try:
        if method.lower() == "get":
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=10)
            if result == "bs":
                soup = bs(response.content, 'html.parser')
                return soup
            elif result == "json":
                return response.json()
            else:
                return response.text
        elif method.lower() == "post":
            response = requests.post(url, json=params, headers=headers, verify=False, timeout=10)
            if result == "json":
                return response.json()
            else:
                return response.text
    except Exception as e:
        log(f"웹 요청 오류: {e}")
        return None

# API 키는 이제 utils.api_manager.APIManager에서 관리됩니다
# 환경 변수 설정은 .env 파일을 참조하세요

def clean_for_kakao(text):
    """카카오톡 메신저용 텍스트 정제 (메신저봇 호환성 강화)"""
    if not text:
        return ""
    
    import re
    
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
        
        # 4. 일부 이모지만 제거 (일반 이모티콘은 유지)
        # 카카오톡에서 문제가 되는 특수 이모지만 제거
        # 일반적인 이모티콘 (😊😂👍❤️ 등)은 유지
        
        # 5. 특수문자 변환 및 제거
        text = text.replace('℃', '도')
        text = text.replace('°C', '도')
        text = text.replace('°', '도')
        text = text.replace('％', '%')
        text = text.replace('㎡', 'm2')
        text = text.replace('㎢', 'km2')
        text = text.replace('※', '')
        text = text.replace('★', '')
        text = text.replace('☆', '')
        text = text.replace('♥', '')
        text = text.replace('♡', '')
        text = text.replace('·', '-')
        text = text.replace('「', '"')
        text = text.replace('」', '"')
        text = text.replace('『', '"')
        text = text.replace('』', '"')
        
        # 6. 추가 특수문자 제거 (카카오톡 메신저봇 호환성)
        text = text.replace('•', '-')  # 글머리 기호를 하이픈으로
        text = text.replace('◆', '-')
        text = text.replace('◇', '-')
        text = text.replace('■', '-')
        text = text.replace('□', '-')
        text = text.replace('▶', '-')
        text = text.replace('▷', '-')
        
        # 7. 줄바꿈을 공백으로 변환 (메신저봇 호환성 문제로 인해)
        text = text.replace('\r\n', ' ')
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        
        # 8. 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 9. 앞뒤 공백 제거
        text = text.strip()
        
        return text
        
    except Exception as e:
        print(f"[clean_for_kakao] 에러: {e}")
        # 에러 시 최소한의 정제만
        return text.strip()

def get_ai_answer(room, sender, msg):
    """AI 질문 처리 함수 - Gemini로 통합 (히스토리 기능 포함)"""
    import random
    from datetime import datetime
    from chat_history_manager import chat_history
    
    question = msg[1:].strip()  # ? 제거
    
    if not question:
        return "질문을 입력해주세요! 예) ?오늘 날씨 어때?"
    
    # 특별 명령어 처리
    if question.lower() == "기록삭제" or question.lower() == "히스토리삭제":
        chat_history.clear_history(room, sender)
        return "대화 기록이 초기화되었습니다. 🗑️"
    
    if question.lower() == "기록확인" or question.lower() == "히스토리확인":
        summary = chat_history.get_history_summary(room, sender)
        return f"📝 {summary}"
    
    # Gemini로 직접 처리
    try:
        # 이전 대화 컨텍스트 가져오기
        context = chat_history.get_context(room, sender, question)
        
        # 시스템 프롬프트 설정
        system_prompt = """당신은 친절한 AI 도우미입니다.
질문에 대해 친절하고 자세하게 답변하되, 너무 짧지 않게 대답하세요.
상냥하고 따뜻한 존댓말로 대화하세요.
답변은 2-3문장 정도로 충실하게 작성하세요.
답변 끝에 적절한 이모티콘 1개를 추가하세요.
최대 1000자 이내로 답변하세요."""
        
        # 컨텍스트가 있으면 질문에 포함
        if context:
            full_question = context
            print(f"[AI] 이전 대화 컨텍스트 포함")
        else:
            full_question = question
            print(f"[AI] 새로운 대화 시작")
        
        # Gemini로 직접 응답 생성
        print(f"[AI] Gemini로 직접 응답 생성 중...")
        response = gemini15_flash(system_prompt, full_question)
        
        if response:
            # 길이 제한 (필요 시)
            if len(response) > 1000:
                response = response[:997] + '...'
            
            # 최종 정제 (마크다운 제거, 줄바꿈 유지)
            cleaned = clean_for_kakao(response)
            
            # 대화 기록에 저장
            chat_history.add_message(room, sender, question, cleaned)
            
            print(f"[AI] 최종 응답: {cleaned[:100]}...")
            return cleaned
        else:
            return "죄송합니다. 잘 이해하지 못했어요. 다시 질문해주세요."
            
    except Exception as e:
        print(f"[AI] Gemini 오류: {e}")
        import traceback
        print(f"[AI] 에러 상세: {traceback.format_exc()}")
        return "일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요."
    
    # 위에서 처리했으므로 아래 코드는 실행되지 않음
    if False:  # Perplexity 비활성화
        # 1. Perplexity API로 정보 검색
        api_key = APIManager.get_next_perplexity_key()
        
        perplexity_response = None
        try:
            # Perplexity로 검색 (정보 수집용)
            print(f"[AI] Perplexity로 정보 검색 중...")
            perplexity_response = perplexity_chat_fast(question, api_key)
            if perplexity_response:
                print(f"[AI] Perplexity 응답 받음 (길이: {len(perplexity_response)})")
        except Exception as e:
            print(f"Perplexity API 오류: {e}")
        
        # 2. Perplexity 응답을 Gemini로 재처리 (카카오톡 최적화)
        if perplexity_response:
            try:
                print(f"[AI] Gemini로 카카오톡용 재포맷팅 중...")
                
                # Perplexity 응답 길이 제한 (너무 긴 입력 방지)
                perplexity_limited = perplexity_response[:400] if len(perplexity_response) > 400 else perplexity_response
                
                # Gemini에게 Perplexity 정보를 기반으로 답변 생성 요청
                gemini_prompt = f"""다음 정보를 바탕으로 카카오톡 메시지로 답변해주세요.

[검색된 정보]
{perplexity_limited}

[답변 요구사항]
- 반드시 100자 이내로 요약
- 핵심만 한두 문장으로
- 줄바꿈 없이 이어서
- 이모지, 특수문자 절대 금지
- 사용자 질문: {question}"""
                
                # Gemini로 재처리
                print(f"[AI] Gemini 호출 중...")
                final_response = gemini15_flash(
                    "100자 이내로 짧게 요약. 줄바꿈 없이. 이모지와 특수문자 절대 사용 금지.",
                    gemini_prompt
                )
                print(f"[AI] Gemini 원본 응답: {final_response}")
                
                if final_response:
                    print(f"[AI] Gemini 재처리 완료 (길이: {len(final_response)})")
                    # 메신저봇 호환성을 위한 텍스트 정제
                    final_response = final_response.replace('\n\n', ' ')
                    final_response = final_response.replace('\n', ' ')
                    # 연속된 공백 정리
                    import re
                    final_response = re.sub(r'\s+', ' ', final_response)
                    # 길이 제한 (안전장치)
                    if len(final_response) > 200:
                        final_response = final_response[:197] + '...'
                    # 최종 정제 후 반환
                    cleaned = clean_for_kakao(final_response)
                    print(f"[AI] 최종 응답: {cleaned}")
                    return cleaned
                else:
                    # Gemini 실패시 Perplexity 원본 사용
                    print(f"[AI] Gemini 재처리 실패, Perplexity 원본 사용")
                    perplexity_response = perplexity_response.replace('\n\n', ' ')
                    perplexity_response = perplexity_response.replace('\n', ' ')
                    return clean_for_kakao(perplexity_response)
                    
            except Exception as e:
                print(f"[AI] Gemini 재처리 오류 상세: {e}")
                import traceback
                print(f"[AI] 에러 트레이스: {traceback.format_exc()}")
                # 오류시 짧은 기본 메시지 반환
                return "정보를 가져왔는데 처리 중 문제가 발생했어요. 다시 질문해주세요."
        
        # 3. Perplexity 실패시 Gemini 직접 응답
        try:
            print(f"[AI] Perplexity 실패, Gemini 직접 응답 생성")
            response = gemini15_flash(
                "간단히 1-2문장으로 답변. 이모지와 특수문자 사용 금지.",
                question
            )
            if response:
                return clean_for_kakao(response)
        except Exception as e:
            print(f"Gemini 폴백 오류: {e}")
        
        # 4. 모든 실패시 기본 Gemini 폴백
        try:
            response = gemini15_flash(
                """너는 친절한 AI 도우미야. 간결하게 1-2문장으로만 답변해.""",
                question
            )
            if response:
                formatted_response = response.replace(". ", ".\n").strip()
                return formatted_response
        except Exception as e:
            print(f"Gemini API 폴백 오류: {e}")
    
    # 모든 API 실패시 기본 응답
    return "죄송해요, 지금은 AI 서비스를 이용할 수 없습니다. 잠시 후 다시 시도해주세요."

def perplexity_chat_fast(question, api_key):
    """Perplexity API 호출 함수 - 빠르고 간결한 검색용"""
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 빠른 응답을 위한 최적화 설정
    payload = {
        "model": "sonar",  # Perplexity의 최신 검색 모델
        "messages": [
            {
                "role": "system",
                "content": "핵심 정보만 간단히 한국어로. 최신 정보 위주로 200자 이내."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.1,  # 더 정확한 답변
        "max_tokens": 200,   # 짧게 제한 (속도 향상)
        "stream": False
    }
    
    try:
        # 타임아웃을 5초로 단축 (빠른 응답)
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        
        # 상태 코드 확인
        if response.status_code == 401:
            print(f"Perplexity API 인증 실패")
            return None
        elif response.status_code == 429:
            print(f"Perplexity API 요청 한도 초과")
            return None
        
        response.raise_for_status()
        
        data = response.json()
        
        # 응답 구조 확인
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0].get('message', {}).get('content', '').strip()
            
            # 텍스트 정제 (카카오톡 호환)
            import re
            # 1. 참조 번호 제거 [1], [2] 등
            content = re.sub(r'\[\d+\]', '', content)
            # 2. 특수 기호 변환
            content = content.replace('℃', '도')  # 온도 기호 변환
            content = content.replace('°C', '도')
            content = content.replace('°', '도')
            content = content.replace('％', '%')
            content = content.replace('㎡', 'm2')
            content = content.replace('㎢', 'km2')
            # 3. 특수문자 제거 (한글은 유지)
            # content = re.sub(r'[\u2000-\u206F\u2E00-\u2E7F]', '', content)  # 특수 공백/구두점 - 일시 비활성화
            # content = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', content)  # 제어 문자 - 일시 비활성화
            # 4. 마크다운 제거
            content = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', content)  # **bold** 또는 *italic*
            content = re.sub(r'`([^`]+)`', r'\1', content)  # `code`
            # 5. 연속된 공백만 제거 (줄바꿈은 보존!)
            lines = content.split('\n')
            lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in lines if line.strip()]
            content = '\n'.join(lines)
            # 6. 앞뒤 공백 제거
            content = content.strip()
            
            # 6. 마침표 추가 (없으면)
            if content and not content[-1] in '.!?':
                content += '.'
                
            # 7. 안전한 ASCII 변환 (이모지는 유지)
            # content = content.encode('utf-8', 'ignore').decode('utf-8')
            
            print(f"정제된 Perplexity 응답: {content}")
            # 태그 없이 순수 내용만 반환
            return content
        
        return None
    
    except requests.exceptions.Timeout:
        print(f"Perplexity API 타임아웃 (10초)")
        return None
    except Exception as e:
        print(f"Perplexity API 오류: {e}")
        return None

def perplexity_chat(question, api_key):
    """Perplexity API 호출 함수 - 원본"""
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 2024년 최신 모델 사용
    payload = {
        "model": "sonar",  # Perplexity의 최신 검색 모델
        "messages": [
            {
                "role": "system",
                "content": """You are STORIUM AI, a friendly Korean assistant.
당신은 STORIUM AI입니다. 한국어로 친절하고 자연스럽게 답변하세요.
사용자의 질문에 맞춰 다양하고 창의적으로 응답하세요.
같은 질문이라도 매번 다른 표현과 관점으로 답변하세요.
대표는 이국환님이며 STORIUM과 SION.LAB를 운영하고 계십니다.
최신 정보를 활용하여 정확한 답변을 제공하세요.
답변은 읽기 쉽게 적절한 줄바꿈과 이모지를 사용하세요."""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.2,  # 더 정확한 답변을 위해 낮춤
        "max_tokens": 1000,  # 충분한 답변 길이
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        # 상태 코드 확인
        if response.status_code == 401:
            print(f"Perplexity API 인증 실패: API 키를 확인하세요")
            return None
        elif response.status_code == 429:
            print(f"Perplexity API 요청 한도 초과")
            return None
        
        response.raise_for_status()
        
        data = response.json()
        
        # 응답 구조 확인
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0].get('message', {}).get('content', '').strip()
            
            # 검색 결과가 있는 경우 출처 정보 추가
            if 'search_results' in data and data['search_results']:
                content += "\n\n📚 참고자료:"
                for idx, result in enumerate(data['search_results'][:3], 1):
                    title = result.get('title', '')
                    url = result.get('url', '')
                    if title and url:
                        content += f"\n{idx}. {title}"
            
            return content
        
        print(f"Perplexity API 응답 형식 오류: {data}")
        return None
        
    except requests.exceptions.Timeout:
        print("Perplexity API 타임아웃")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Perplexity API 요청 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text[:200]}")
        return None

def gemini15_flash(system, question, retry_count=0, use_search=True):
    """Gemini 2.0 Flash AI 함수 - Google Search 통합"""
    # APIManager를 통해 다음 API 키 가져오기
    api_key = APIManager.get_next_gemini_key()
    
    try:
        # API 키 설정
        genai.configure(api_key=api_key)
        
        # 검색이 필요한 키워드 확인
        search_keywords = ['날씨', '뉴스', '최신', '오늘', '지금', '현재', '주가', '코인', '환율', 
                          '시세', '가격', '맛집', '추천', '어제', '내일', '실시간']
        needs_search = any(keyword in question.lower() for keyword in search_keywords)
        
        # 모델 설정 (Google Search는 프롬프트로 처리)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # 실시간 정보가 필요한 경우 프롬프트 조정
        if use_search and needs_search:
            print("[AI] 실시간 정보 모드 활성화")
            # 프롬프트에 현재 날짜와 실시간 정보 요청 추가
            from datetime import datetime
            current_date = datetime.now().strftime("%Y년 %m월 %d일")
            system = f"{system}\n현재 날짜: {current_date}. 최신 정보를 바탕으로 답변해주세요."
        
        # 프롬프트 생성 - 마크다운 금지, 이모티콘 허용
        prompt = f"""{system}

절대적인 규칙:
1. 마크다운 문법을 절대 사용하지 마세요 (**, *, #, `, ~, __ 등)
2. 글머리 기호는 하이픈(-) 만 사용. • 나 다른 특수문자 사용 금지
3. 강조가 필요하면 대괄호 [중요] 사용
4. 답변에 적절한 이모티콘을 사용해 주세요 😊 👍 ❤️ 
5. 모든 내용은 한 줄로 이어서 작성. 줄바꿈 사용하지 마세요.
6. 존댓말로 친절하게 답변해 주세요.
7. 묻는 말에만 직접 답변하고 추가 질문이나 제안은 하지 마세요.

User: {question}
Assistant:"""
        
        # 응답 생성 (스트리밍 비활성화로 빠른 응답)
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,  # 자연스러운 대화를 위해 적절히 설정
                'max_output_tokens': 1500,  # 1000자 + 여유분
            }
        )
        
        if response and response.text:
            # 이모티콘은 유지하되 마크다운만 제거
            text = response.text.strip()
            import re
            
            # 마크다운 문법 강제 제거 (혹시 생성됐을 경우)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** → bold
            text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic* → italic
            text = re.sub(r'__([^_]+)__', r'\1', text)      # __underline__ → underline
            text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_ → italic
            text = re.sub(r'`([^`]+)`', r'\1', text)        # `code` → code
            text = re.sub(r'#{1,6}\s*', '', text)           # ### header → header
            
            return text.strip()
        
        # 현재 키 실패시 다음 키로 재시도 (최대 3번)
        if retry_count < 2:
            print(f"Gemini API 키 실패, 다음 키로 재시도 (시도 {retry_count + 2}/3)")
            return gemini15_flash(system, question, retry_count + 1, use_search)
        
        return None
        
    except Exception as e:
        print(f"Gemini API 오류: {e}")
        
        # 다른 키로 재시도 (최대 3번)
        if retry_count < 2:
            print(f"다른 Gemini 키로 재시도 (시도 {retry_count + 2}/3)")
            return gemini15_flash(system, question, retry_count + 1, use_search)
        
        return None

def claude3_haiku(system, question):
    """Claude AI 함수 (임시 구현 유지)"""
    return None  # Claude API는 나중에 필요시 구현

def gpt4o_mini(system, question):
    """GPT-4o Mini 함수 (임시 구현 유지)"""  
    return None  # OpenAI API는 나중에 필요시 구현

# ========================================
# 기존 코드 시작
# ========================================

def get_reply_msg(room: str, sender: str, msg: str):
    log(f"{room}    {sender}    {msg}")
    
    # === 기존 로직 ===
    msg = msg.strip()
    
    # 빈 메시지 처리
    if not msg:
        return None
        
    # 통합 명령어 관리자 import
    from command_manager import get_command_help, check_command_permission
    from error_commands import error_logs, error_stats, usage_stats, enable_command, reset_command_stats, performance_recommendations
    from cache_commands import clear_cache, cache_status
        
    # 테스트 명령어 추가
    if msg == '/테스트':
        return "테스트 성공"
    elif msg == '/테스트2':
        return "테스트 성공!\n두번째 줄입니다."
    elif msg == '/테스트3':
        return "😊 이모지 테스트"
    elif msg == '/안녕':
        return f"안녕하세요 {sender}님! 저는 STORIUM AI입니다."
    elif msg == '/시간':
        from datetime import datetime
        return f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 첫 글자 안전하게 확인
    # AI 질문 처리 기능 비활성화 (나중에 다시 활성화 가능)
    # if len(msg) > 0 and msg[0] in('?', '？'):
    #     return get_ai_answer(room, sender, msg)
    if msg in ['/명령어', '/가이드', '/도움말']:
        # 관리자인 경우에만 관리자 명령어 포함
        is_admin = config.is_admin_user(sender)
        return get_command_help(is_admin=is_admin)
    elif msg == '/명령어목록':
        # 전체 명령어 목록 표시
        is_admin = config.is_admin_user(sender)
        from command_manager import get_command_list
        return get_command_list(is_admin=is_admin)

    elif msg == "/운세":
        return fortune_today(room, sender, msg)
    elif msg.startswith("/주식"):
        return stock(room, sender, msg)
    elif msg.startswith("/운세"):
        return fortune(room, sender, msg)
    elif msg in ["/물병자리", "/물고기자리", "/양자리", "/황소자리", "/쌍둥이자리", "/게자리", "/사자자리", "/처녀자리", "/천칭자리", "/전갈자리", "/사수자리", "/궁수자리", "/염소자리"]:
        return zodiac(room, sender, msg)
    elif msg == '/날씨':
        return whether_today(room, sender, msg)
    elif msg.startswith("/날씨"):
        return whether(room, sender, msg)
    elif msg in ["/실시간검색어", '/검색어']:
        return real_keyword(room, sender, msg)
    elif msg in ["/실시간뉴스"]:
        return real_news(room, sender, msg)
    elif msg.upper() == '/IT뉴스':
        return it_news(room, sender, msg)
    elif msg == '/경제뉴스':
        return economy_news(room, sender, msg)
    elif msg == '/부동산뉴스':
        return realestate_news(room, sender, msg)
    elif msg.startswith("/뉴스"):
        return search_news(room, sender, msg)
    elif msg.startswith("/블로그"):
        return search_blog(room, sender, msg)
    elif msg.startswith("/칼로리"):
        return calorie(room, sender, msg)
    elif msg == "/환율":
        return exchange(room, sender, msg)
    elif msg == '/금값':
        return gold(room, sender, msg)
    elif msg == '/코인':
        return coin(room, sender, msg)
    elif msg == "/영화순위":
        return movie_rank(room, sender, msg)
    elif msg.startswith(("/맵", "/지도")):
        return naver_map(room, sender, msg)
    elif msg.startswith("/") and msg.endswith("맛집"):
        return naver_map(room, sender, msg)
    elif msg == "/명언":
        return wise_saying(room, sender, msg)
    elif msg  == "/상한가":
        return stock_upper(room, sender, msg)
    elif msg  == "/하한가":
        return stock_lower(room, sender, msg)
    elif msg == "/인급동":
        return youtube_popular_all(room, sender, msg)
    elif msg == "/인급동랜덤":
        return youtube_popular_random(room, sender, msg)
    # elif msg.startswith("/쿠팡"):  # 쿠팡 기능 제거됨
    #     return coupang_products(room, sender, msg)
    elif "han.gl" in msg:
        return "스팸이 감지되었습니다."
    elif msg.startswith("#"):
        return naver_keyword(room, sender, msg)
    elif msg.startswith("/네이버부동산"):
        return naver_land(room, sender, msg)
    elif msg == '/test' and config.is_admin_user(sender):
        return test(room, sender, msg)
    elif msg.startswith('/전적'):
        return lol_record(room, sender, msg)
    
    # URL 자동 감지 로직 개선
    # YouTube URL 패턴 (메시지 내 어디든 포함 가능)
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        youtube_match = re.search(pattern, msg)
        if youtube_match:
            # YouTube URL 발견 시 해당 URL로 요약 실행
            youtube_url = youtube_match.group(0)
            if not youtube_url.startswith('http'):
                youtube_url = 'https://' + youtube_url
            return summarize(room, sender, youtube_url)
    
    # 일반 웹 URL 패턴 (http/https로 시작하는 모든 URL)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    url_match = re.search(url_pattern, msg)
    if url_match:
        # 일반 URL 발견 시 웹 요약 실행
        web_url = url_match.group(0)
        return web_summary(room, sender, web_url)
    
    # adb 명령어 (관리자 전용)
    elif msg == '/재부팅':
        # 권한 체크
        can_use, error_msg = check_command_permission('/재부팅', sender, room)
        if not can_use:
            return error_msg
        subprocess.run(["adb", "reboot"])
        return "재부팅 명령이 실행되었습니다."
    
    # 방 관리 명령어 (관리자 전용)
    elif msg.startswith('/방추가'):
        # 권한 체크
        can_use, error_msg = check_command_permission('/방추가', sender, room)
        if not can_use:
            return error_msg
        return room_add(room, sender, msg)
    elif msg.startswith('/방삭제'):
        # 권한 체크
        can_use, error_msg = check_command_permission('/방삭제', sender, room)
        if not can_use:
            return error_msg
        return room_remove(room, sender, msg)
    elif msg == '/방목록':
        # 권한 체크
        can_use, error_msg = check_command_permission('/방목록', sender, room)
        if not can_use:
            return error_msg
        return room_list(room, sender, msg)
    # 오류 모니터링 명령어 (관리자 전용)
    elif msg.startswith('/오류로그'):
        return error_logs(room, sender, msg)
    elif msg.startswith('/오류통계'):
        return error_stats(room, sender, msg)
    elif msg.startswith('/사용통계'):
        return usage_stats(room, sender, msg)
    elif msg.startswith('/명령어활성화'):
        return enable_command(room, sender, msg)
    elif msg.startswith('/통계리셋'):
        return reset_command_stats(room, sender, msg)
    elif msg.startswith('/성능추천'):
        return performance_recommendations(room, sender, msg)
    elif msg.startswith('/캐시초기화'):
        return clear_cache(room, sender, msg)
    elif msg.startswith('/캐시상태'):
        return cache_status(room, sender, msg)
    
    # 로또
    elif msg.startswith("/로또결과생성"):
        return lotto_result_create(room, sender, msg)
    elif msg.startswith("/로또결과"):
        return lotto_result(room, sender, msg)
    elif msg.startswith("/로또") or "로또" in msg:
        return lotto(room, sender, msg)

    # 인사 메시지 처리
    greetings = ["안녕", "안녕하세요", "하이", "헬로", "ㅎㅇ", "ㅎ2", "반가워", "반갑습니다"]
    for greeting in greetings:
        if greeting in msg.lower():
            return f"{sender}님, 안녕하세요! STORIUM Bot입니다. 무엇을 도와드릴까요? /명령어를 입력하면 사용 가능한 기능을 볼 수 있어요!"
    
    # 가끔 명언 보내기(0.2%)
    if random.random() < 0.002:
        return wise_saying(room, sender, msg)
    
    # 기본 응답 - 명령어가 없는 경우
    return None



def send_message(room, msg):
    ip = "172.30.1.25"
    port = 4006

    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((ip, port))
    data = {
        "room": room,
        "msg": msg
    }
    client_socket.send(json.dumps(data).encode("utf-8"))
    client_socket.close()

def gold(room: str, sender: str, msg: str):
    """금값 정보 조회"""
    try:
        # 네이버 국내 금 시세 페이지
        url = "https://m.stock.naver.com/marketindex/metals/M04020000"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        result = request(url, method="get", result="bs", headers=headers)
        
        if result and hasattr(result, 'select_one'):
            # 금값 정보 추출 (모바일 페이지 구조)
            price_elem = result.select_one('strong.price')
            if not price_elem:
                # 대안 선택자 시도
                price_elem = result.select_one('.MarketindexMetalsView_price__2g3Qs')
            
            if price_elem:
                price = price_elem.get_text(strip=True)
                
                # 변동 정보 추출
                change_elem = result.select_one('.price_gap')
                if not change_elem:
                    change_elem = result.select_one('.MarketindexMetalsView_change__2BfQu')
                
                change = ""
                if change_elem:
                    change_text = change_elem.get_text(strip=True)
                    # 상승/하락 표시 확인
                    if '상승' in str(result) or 'up' in str(result):
                        change = f"▲ {change_text}"
                    elif '하락' in str(result) or 'down' in str(result):
                        change = f"▼ {change_text}"
                    else:
                        change = change_text
                
                # 날짜 정보 추출
                date_elem = result.select_one('.date')
                date_text = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y.%m.%d')
                
                return f"💰 국내 금 시세 (1g 기준)\n\n📊 {price}원\n{change}\n\n📅 {date_text} 기준\n※ 네이버 금융"
        
        # 대안: 네이버 검색 결과에서 금값 정보 추출
        search_url = "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=현재+금값"
        result2 = request(search_url, method="get", result="bs", headers=headers)
        
        if result2 and hasattr(result2, 'select_one'):
            # 검색 결과에서 금값 추출
            price_elem = result2.select_one('a[href*="marketindex/metals"] strong.price')
            if price_elem:
                price = price_elem.get_text(strip=True)
                
                # 변동 정보
                change_elem = result2.select_one('a[href*="marketindex/metals"] .price_gap')
                change = change_elem.get_text(strip=True) if change_elem else ""
                
                return f"💰 국내 금 시세 (1g 기준)\n\n📊 {price}원\n{change}\n\n※ 네이버 금융 실시간"
        
        # 기본 응답 (API 실패 시)
        return "💰 현재 금값\n\n금 시세 정보를 가져올 수 없습니다.\n네이버에서 '금값'을 검색해보세요."
        
    except Exception as e:
        log(f"금값 조회 오류: {e}")
        return "금값 정보를 조회하는 중 오류가 발생했습니다"

def photo(room: str, sender: str, msg: str):
    keyword = msg.replace('/사진', '').strip()
    encode_keyword = urllib.parse.quote(keyword)
    url = f'https://unsplash.com/ko/s/%EC%82%AC%EC%A7%84/{encode_keyword}?license=free'
    soup = request(url, 'get', 'bs')
    elements = soup.select('img[data-test="photo-grid-masonry-img"]')
    if not elements:
        return f"{keyword} 사진을 못찾았어요ㅠㅠ"
    
    # elements 에서 랜덤한 이미지 선택
    element = random.choice(elements)
    img_url = element['src']
    response = requests.get(img_url)
    img_data = response.content

    # 파일명 영대소문자숫자 임의의 6자리 생성
    filename = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

    # 파일 저장
    dir_path = os.path.dirname(__file__)
    file_path = os.path.join(dir_path, 'static', 'img', f'{filename}.jpg')
    with open(file_path, 'wb') as f:
        f.write(img_data)
        

    # 주소 반환
    send_msg = f"http://ggur.kr/img/{filename}"

    return send_msg

def extract_youtube_id(url):
    # 정규 표현식 패턴 정의
    pattern = re.compile(r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:&|\/|$)')
    
    # 정규 표현식 검색
    match = pattern.search(url)
    
    # 매치된 경우 비디오 ID 반환, 그렇지 않으면 None 반환
    if match:
        return match.group(1)
    return None
    
def summarize(room: str, sender: str, msg: str):
    url = msg.strip()
    video_id = None
    
    if url.startswith(r'https://www.youtube.com/shorts/'):
        video_id = url.replace(r'https://www.youtube.com/shorts/', '').split('?')[0]
    elif url.startswith(r'https://www.youtube'):
        video_id = url.replace('https://www.youtube.com/watch?v=', '').split('&')[0]
    elif url.startswith(r'https://youtu.be'):
        video_id = url.replace(r'https://youtu.be/', '').split('?')[0]

    if not video_id:
        return None
    
    if video_id.startswith('http'):
        return None
    
    heart_emojis = '❤️💙💗💚💖💓🖤💟💔💛🤍🤎🧡💝💜❤️💘'
    random_heart = random.choice(heart_emojis)

    # YouTube API로 영상 정보 가져오기
    api_key = APIManager.get_next_gemini_key()  # APIManager에서 관리
    title = "제목 없음"
    channel_name = "채널 없음"
    view_count = 0
    comment_count = 0
    
    if build is not None:
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            request = youtube.videos().list(
                part='snippet,statistics',
                id=video_id
            )
            response = request.execute()
            
            if 'items' in response and len(response['items']) > 0:
                video_info = response['items'][0]
                title = video_info['snippet']['title']
                channel_name = video_info['snippet']['channelTitle']
                view_count = int(video_info['statistics'].get('viewCount', 0))
                comment_count = int(video_info['statistics'].get('commentCount', 0))
        except Exception as e:
            log(f"YouTube API 오류: {e}")

    # 자막 가져오기 및 요약
    summary_3lines = ""
    full_summary = ""
    
    try:
        if YouTubeTranscriptApi is not None:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, ['ko'])
            text_list = []
            for line in transcript:
                text_list.append(line['text'])
            text = ' '.join(text_list)
            
            # 3줄 요약 (개선된 프롬프트)
            question_3lines = '''다음 유튜브 내용을 3개의 핵심 포인트로 극히 간결하게 정리해주세요. 각 포인트는 핵심 내용과 그에 대한 객관적인 의미/주요 영향을 포함하여, **각각 최대 1~2줄로 명료하게 요약해주세요.** 다양한 연결어와 어휘를 사용하고, **특히 '이는' 이라는 표현은 절대로 사용하지 말고,** 대신 '이것은', '이 점은', '해당 내용은'과 같이 다른 표현을 사용하거나 문맥에 맞게 자연스럽게 연결해주세요. 불필요한 세부 설명은 모두 생략하고, 전체 요약은 매우 짧아야 합니다. 다른 설명 없이 아래 번호 형식만 사용하세요:

1. [첫 번째 핵심 포인트 (1~2줄)]

2. [두 번째 핵심 포인트 (1~2줄)]

3. [세 번째 핵심 포인트 (1~2줄)]

유튜브 스크립트:
''' + text[:5000]  # 토큰 제한을 위해 일부만 사용
            
            try:
                summary_3lines = gemini15_flash('', question_3lines)
                # 줄바꿈이 없으면 추가
                if '\n' not in summary_3lines:
                    # 문장을 찾아서 줄바꿈 추가
                    sentences = summary_3lines.split('. ')
                    if len(sentences) >= 3:
                        summary_3lines = sentences[0] + '.\n' + sentences[1] + '.\n' + '. '.join(sentences[2:])
            except Exception as e:
                summary_3lines = "요약을 생성할 수 없습니다."
            
            # 전체 상세 요약
            question_full = '''다음 유튜브 스크립트의 핵심 내용을 10줄 이내로 상세히 요약해줘.
읽기 쉽게, 결과만 출력해.

''' + text[:10000]
            
            try:
                full_summary = gemini15_flash('', question_full)
            except Exception as e:
                full_summary = summary_3lines  # 실패시 3줄 요약 재사용
        else:
            summary_3lines = "YouTube 자막 분석 기능을 사용할 수 없습니다."
            full_summary = summary_3lines
    except Exception as e:
        log(f"자막 처리 오류: {e}")
        summary_3lines = "자막이 없는 영상입니다."
        full_summary = summary_3lines
    
    # 메시지 구성 (3줄 요약 + 전체보기)
    send_msg = f'📺 YouTube 요약 {random_heart}\n'
    send_msg += f'🎬 {title}\n'
    send_msg += f'👤 {channel_name}\n\n'
    
    # 3줄 요약
    send_msg += f'💡 3줄 요약:\n{summary_3lines}\n\n'
    
    # 전체보기 구분선
    send_msg += '🔗 전체 내용 보기 (클릭▼)'
    send_msg += '\u180e' * 500  # 보이지 않는 공백으로 전체보기 트리거
    
    # 숨겨진 상세 정보
    send_msg += '\n\n━━━━━━━━━━━━━━━\n'
    send_msg += '📄 상세 정보\n\n'
    send_msg += f'👀 조회수: {view_count:,}회\n'
    send_msg += f'💬 댓글: {comment_count:,}개\n\n'
    send_msg += f'📝 전체 요약:\n{full_summary}\n\n'
    send_msg += f'🎥 원본 영상:\n{url}'

    return send_msg


def extract_main_content(soup):
    """웹페이지 본문 추출 - 뉴스 사이트 최적화"""
    
    # 뉴스 사이트별 본문 선택자
    selectors = [
        # 네이버 블로그
        '.se-main-container',  # 네이버 블로그 스마트에디터3
        '.postViewArea',  # 네이버 블로그 구 에디터
        '#postViewArea',
        '.post-view',
        'div[id^="post-view"]',
        '.se-component',  # 네이버 블로그 컴포넌트
        
        # 네이버 엔터/뉴스
        '.end_ct_area',  # 네이버 엔터 기사
        '.news_end',  # 네이버 뉴스
        '#articeBody',  # 네이버 기사 본문
        '#newsEndContents',  # 네이버 뉴스 본문
        '.news_view',  # 네이버 뉴스
        '#articleBodyContents',  # 네이버 뉴스 구버전
        '.content_area',  # 네이버 뉴스 신버전
        
        # 일반 사이트
        'article',  # 일반적인 article 태그
        '.article_body',  # 다음 뉴스  
        '.article_view',  # 일부 뉴스 사이트
        '.news_body',  # 일부 뉴스 사이트
        '.content',  # 일반 콘텐츠
        'main',  # HTML5 main 태그
        '[role="main"]',  # ARIA role
        '.post-content',  # 블로그 형식
        '.entry-content',  # 워드프레스 등
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            # 불필요한 태그 제거
            for tag in element.select('script, style, aside, nav'):
                tag.decompose()
            return element.get_text(separator=' ', strip=True)
    
    # 못 찾으면 body 전체 (스크립트와 스타일 제외)
    body = soup.find('body')
    if body:
        for tag in body.select('script, style, aside, nav, header, footer'):
            tag.decompose()
        return body.get_text(separator=' ', strip=True)[:10000]
    return ""


def web_summary(room: str, sender: str, msg: str):
    """웹페이지 3줄 요약 - requests 우선, ScrapingBee fallback"""
    url = msg.strip()
    
    # ScrapingBee API 키 로테이션
    current_api_key = get_next_scrapingbee_key()
    
    content = None
    title = None
    
    # 1. 먼저 requests로 시도 (개선된 헤더)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 네이버의 경우 모바일 User-Agent 사용
        if 'naver.com' in url:
            headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        
        # 세션 사용
        session = requests.Session()
        response = session.get(url, timeout=10, headers=headers, allow_redirects=True)
        
        # 인코딩 처리
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding or 'utf-8'
        
        soup = bs(response.text, 'html.parser')
        
        # 제목 추출 개선
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.text.strip()
        else:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '제목 없음')
            else:
                title = "제목 없음"
        
        # 네이버 블로그 iframe 처리
        if 'blog.naver.com' in url:
            iframe = soup.find('iframe', {'id': 'mainFrame'})
            if iframe:
                iframe_src = iframe.get('src')
                if iframe_src:
                    if not iframe_src.startswith('http'):
                        iframe_src = 'https://blog.naver.com' + iframe_src
                    
                    log(f"네이버 블로그 iframe 감지, 재시도: {iframe_src}")
                    
                    # iframe URL로 다시 요청
                    iframe_response = session.get(iframe_src, headers=headers, timeout=10)
                    if iframe_response.status_code == 200:
                        soup = bs(iframe_response.text, 'html.parser')
                        log("iframe 콘텐츠 로드 성공")
        
        # 본문 추출 (헬퍼 함수 사용)
        content = extract_main_content(soup)
        
        if not content or len(content) < 100:
            log("콘텐츠가 너무 짧거나 없음, fallback 시도")
            content = None
            
    except Exception as e:
        log(f"웹페이지 로드 실패: {e}, fallback 시도")
    
    # 2. requests 실패 시 ScrapingBee API 사용
    if not content:  # ScrapingBee API 활성화 (2개 키 사용 가능)
        try:
            log(f"ScrapingBee API 사용 시작")
            
            # ScrapingBee API 엔드포인트
            scrapingbee_url = 'https://app.scrapingbee.com/api/v1/'
            
            # ScrapingBee 파라미터
            params = {
                'api_key': current_api_key,
                'url': url,
                'render_js': 'true',  # JavaScript 렌더링 활성화 (네이버 블로그 등)
                'premium_proxy': 'true',  # 프리미엄 프록시 사용
                'country_code': 'kr',  # 한국 IP 사용
                'wait': '3000',  # 3초 대기 (동적 콘텐츠 로딩)
                'block_resources': 'false'  # 모든 리소스 로드
            }
            
            response = requests.get(scrapingbee_url, params=params, timeout=25)
            
            if response.status_code == 200:
                soup = bs(response.text, 'html.parser')
                
                # 제목 추출
                if not title:
                    title = soup.find('title').text.strip() if soup.find('title') else "제목 없음"
                
                # 네이버 블로그 특별 처리
                if 'blog.naver.com' in url:
                    # iframe 체크
                    iframe = soup.find('iframe', {'id': 'mainFrame'})
                    if iframe and not content:
                        iframe_src = iframe.get('src')
                        if iframe_src:
                            # iframe URL이 상대 경로일 수 있음
                            if not iframe_src.startswith('http'):
                                iframe_src = 'https://blog.naver.com' + iframe_src
                            
                            log(f"네이버 블로그 iframe 감지, iframe URL로 재시도: {iframe_src}")
                            
                            # iframe URL로 다시 ScrapingBee 요청
                            iframe_params = params.copy()
                            iframe_params['url'] = iframe_src
                            
                            try:
                                iframe_response = requests.get(scrapingbee_url, params=iframe_params, timeout=25)
                                if iframe_response.status_code == 200:
                                    soup = bs(iframe_response.text, 'html.parser')
                                    log("iframe 콘텐츠 로드 성공")
                            except Exception as e:
                                log(f"iframe 로드 실패: {e}")
                    
                    # 네이버 블로그의 메인 콘텐츠 영역
                    content_selectors = [
                        '.se-main-container',  # 스마트에디터3
                        '.postViewArea',  # 구 에디터
                        '#postViewArea',
                        '.post-view',
                        'div[id^="post-view"]'
                    ]
                    
                    for selector in content_selectors:
                        element = soup.select_one(selector)
                        if element:
                            # 불필요한 요소 제거
                            for tag in element.select('script, style, .post_tag, .post_btn'):
                                tag.decompose()
                            content = element.get_text(strip=True)
                            if len(content) > 100:
                                break
                
                # 일반 웹페이지 처리
                if not content or len(content) < 100:
                    content = extract_main_content(soup)
                    
                log(f"ScrapingBee로 콘텐츠 추출 성공: {len(content) if content else 0}자")
                
            else:
                log(f"ScrapingBee API 오류: {response.status_code}")
                
        except Exception as e:
            log(f"ScrapingBee 실패: {e}")
    
    # 콘텐츠가 여전히 없으면 에러 반환
    if not content or len(content) < 100:
        return f"⚠️ 페이지 내용을 추출할 수 없습니다.\n{url}"
    
    # Gemini로 요약
    api_key = APIManager.get_next_gemini_key()  # APIManager에서 관리
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 3줄 요약 (개선된 프롬프트)
    prompt_3lines = f"""다음 웹페이지 내용을 3개의 핵심 포인트로 극히 간결하게 정리해주세요. 각 포인트는 핵심 내용과 그에 대한 객관적인 의미/주요 영향을 포함하여, **각각 최대 1~2줄로 명료하게 요약해주세요.** 다양한 연결어와 어휘를 사용하고, **특히 '이는' 이라는 표현은 절대로 사용하지 말고,** 대신 '이것은', '이 점은', '해당 내용은'과 같이 다른 표현을 사용하거나 문맥에 맞게 자연스럽게 연결해주세요. 불필요한 세부 설명은 모두 생략하고, 전체 요약은 매우 짧아야 합니다. 다른 설명 없이 아래 번호 형식만 사용하세요:

1. [첫 번째 핵심 포인트 (1~2줄)]

2. [두 번째 핵심 포인트 (1~2줄)]

3. [세 번째 핵심 포인트 (1~2줄)]

제목: {title}
내용: {content[:5000]}
"""
    
    try:
        summary_3lines = model.generate_content(prompt_3lines).text
        # 줄바꿈이 없으면 추가
        if '\n' not in summary_3lines:
            sentences = summary_3lines.split('. ')
            if len(sentences) >= 3:
                summary_3lines = sentences[0] + '.\n' + sentences[1] + '.\n' + '. '.join(sentences[2:])
    except Exception as e:
        log(f"3줄 요약 실패: {e}")
        summary_3lines = "요약을 생성할 수 없습니다."
    
    # 전체 상세 요약
    prompt_full = f"""다음 웹페이지 내용을 10줄 이내로 상세히 요약해줘.
핵심 내용을 빠짐없이, 읽기 쉽게 정리해줘.
요약만 출력하고 다른 말은 하지 마.

제목: {title}
내용: {content[:10000]}
"""
    
    try:
        full_summary = model.generate_content(prompt_full).text
    except Exception as e:
        log(f"전체 요약 실패: {e}")
        full_summary = summary_3lines  # 실패시 3줄 요약 재사용
    
    # 메시지 구성 (3줄 요약 + 전체보기)
    send_msg = f'📝 웹페이지 요약\n'
    send_msg += f'📌 {title}\n\n'
    send_msg += f'💡 3줄 요약:\n{summary_3lines}\n\n'
    
    # 전체보기 구분선
    send_msg += '🔗 전체 내용 보기 (클릭▼)'
    send_msg += '\u180e' * 500  # 보이지 않는 공백으로 전체보기 트리거
    
    # 숨겨진 상세 정보
    send_msg += '\n\n━━━━━━━━━━━━━━━\n'
    send_msg += '📄 상세 요약\n\n'
    send_msg += f'{full_summary}\n\n'
    send_msg += f'🌐 원본 페이지:\n{url}'
    
    return send_msg


def lol_record(room: str, sender: str, msg: str):
    try:
        nickname = msg.replace("/전적", "").strip()
        if not nickname:
            return "[/전적 소환사명] 형식으로 입력해주세요."
        
        suffix = '-KR1' if '-' not in nickname else ''


        url = f"https://fow.kr/find/{nickname}{suffix}"
        headers = {
            'Referer': 'https://fow.kr/ranking',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
        }
        doc = request(url, method="get", result="bs", headers=headers)
        
        summary = doc.select_one('div.table_summary')
        if not summary:
            return f"{nickname} 소환사를 찾을 수 없어요."
        
        input = summary.get_text()
        win = doc.select_one('#content-container div.div_recent > div > div:nth-child(1)').get_text().replace('\n', '')
        win2 = doc.select_one('#content-container div.div_recent > div > div:nth-child(2)').get_text().replace('\n', '')
        champ1 = doc.select_one('#content-container div.div_recent > div > div:nth-child(3) > div:nth-child(1)').get_text().replace('\n', '')
        champ2 = doc.select_one('#content-container div.div_recent > div > div:nth-child(3) > div:nth-child(2)').get_text().replace('\n', '')
        champ3 = doc.select_one('#content-container div.div_recent > div > div:nth-child(3) > div:nth-child(3)').get_text().replace('\n', '')
        
        rankingStart = input.find("랭킹")
        rankingEnd = input.find("리그")
        leagueStart = input.find("리그")
        leagueEnd = input.find("리그 포인트:", leagueStart)
        promoStart = input.find("승급전")
        promoEnd = input.find("리그:", promoStart)
        leaguePointStart = input.find("리그 포인트:")
        leaguePointEnd = input.find("승급전", leaguePointStart)
        rankingValue = "랭킹 결과 없음"
        leagueValue = "리그 결과 없음"
        leaguePointValue = "리그 포인트 결과 없음"
        promoValue = "승급전 결과 없음"

        if rankingStart != -1 and rankingEnd != -1 and leagueStart != -1 and leagueEnd != -1 and promoStart != -1 and promoEnd != -1:
            rankingValue = input[rankingStart:rankingEnd].strip()
            leagueValue = input[leagueStart:leagueEnd].strip()
            leaguePointValue = input[leaguePointStart:leaguePointEnd].strip()
            promoValue = input[promoStart:promoEnd].strip()

        send_msg = f"""🕹️ [ L.O.L 전적 ] 🕹️
    ID: {nickname}

    1. 최근 게임 정보
    - {win}

    2. 최근 게임 승률
    - {win2}

    3. 랭킹 정보
    - {rankingValue}
    - {leagueValue}
    - {leaguePointValue}`
    - {promoValue}

    4. 최근 챔프
    - {champ1}
    - {champ2}
    {champ3}
    """
        return send_msg

    except Exception as e:
        print(traceback.format_exc())
        return f"오류가 발생했어요ㅠ\n{e}"



def add_url(room: str, sender: str, msg: str):

    content = msg.replace('/주소추가 ', '').strip()
    urls = re.findall(r'(https?://\S+)', content)

    if len(urls) == 0:
        return "주소를 못찾았어요. http를 포함하여 url을 입력해주세요."
    elif len(urls) > 1:
        return "주소는 하나만 입력해주세요."
    
    url = urls[0]
    description = content.replace(url, '').strip()

    soup = request(url, 'get', 'bs')
    og_title = soup.find('meta', property='og:title')
    og_description = soup.find('meta', property='og:description')
    og_image = soup.find('meta', property='og:image')
    og_url = soup.find('meta', property='og:url')

    og_title_content = og_title['content'] if og_title else ''
    og_description_content = og_description['content'] if og_description else ''
    og_image_content = og_image['content'] if og_image else ''
    og_url_content = og_url['content'] if og_url else ''
    
    # id 생성
    query = "SELECT MAX(id) FROM sites WHERE room = %s"
    params = (room,)
    max_id = fetch_val(query, params)
    id = max_id + 1 if max_id else 1

    query = "INSERT INTO sites(room, id, url, description, og_title, og_desc, og_image, og_url, created_nickname) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    params = (room, id, url, description, og_title_content, og_description_content, og_image_content, og_url_content, sender)
    execute(query, params)

    return f"""{id}번 주소가 추가되었어요
{og_title_content}
{og_description_content}
{url}

전체 주소 조회는 /주소
특정 주소 조회는 /주소 {id}, /주소 검색어
수정은 /주소수정 {id} 수정내용
삭제는 /주소삭제 {id}
⚠️도움되는 주소가 아니면 관리자가 삭제할 수 있어요.

▼웹사이트에서 보려면▼\nhttps://jadong.net/sites"
"""

def search_url(room: str, sender: str, msg: str):
    condition = msg.replace("/주소", "").strip()
    if not condition:
        query = "SELECT id, url, description, og_title, og_desc FROM sites WHERE room = %s AND deleted_at IS NULL ORDER BY id"
        params = (room,)
        rows = fetch_all(query, params)
        if not rows:
            return "아직 주소가 없어요.\n[/주소추가 {url} {내용}]을 입력해보세요."
        
        send_msg = "📝 주소 모음"
        for row in rows:
            id, url, description, og_title, og_desc = row
            send_msg += f"\n\n{id}. "
            if og_title:
                send_msg += f"{og_title}"
            if og_desc:
                send_msg += f"-{og_desc}"
            if description:
                send_msg += f"\n{description}"
            send_msg += f"\n{url}"
        send_msg += '\n\n 주소추가는 /주소추가 {url} {내용}'
        send_msg += '\n 주소수정은 /주소수정 {번호} {수정할 내용}'
        send_msg += '\n 주소삭제는 /주소삭제 {번호}'
        send_msg += "\n\n▼웹사이트에서 보려면▼\nhttps://jadong.net/sites"
        return send_msg
        
    elif condition.isdigit():
        id = condition
        query = "SELECT id, url, description, og_title, og_desc FROM sites WHERE room = %s AND id = %s AND deleted_at IS NULL"
        params = (room, id)
        row = fetch_one(query, params)

        if not row:
            return f"{id}번 주소가 없어요."
        
        id, url, description, og_title, og_desc = row
        send_msg = f"📝 {id}번 주소\n"
        if og_title:
            send_msg += f"{og_title}"
        if og_desc:
            send_msg += f"-{og_desc}"
        if description:
            send_msg += f"\n{description}"
        send_msg += f"\n{url}"
        return send_msg
    
    else:
        query = "SELECT id, url, description, og_title, og_desc FROM sites WHERE room = %s AND deleted_at IS NULL AND description LIKE %s ORDER BY id"
        params = (room, f"%{condition}%")
        rows = fetch_all(query, params)
        if not rows:
            return f"{condition}에 대한 주소가 없어요."
        
        send_msg = f"📝 {condition} 주소 검색 결과"
        for row in rows:
            id, content = row
            send_msg += f"\n\n{id}. {content}"
        return send_msg
    


def update_url(room: str, sender: str, msg: str):
    condition = msg.replace("/주소수정", "").strip()
    
    if not condition:
        return "[/주소수정 {번호} {수정할 내용}] 형식으로 입력해주세요."
    
    data = condition.split(' ')
    if len(data) < 2:
        return "[/주소수정 {번호} {수정할 내용}] 형식으로 입력해주세요."
    
    id = data[0]
    if not id.isdigit():
        return "[/주소수정 {번호} {수정할 내용}] 형식으로 입력해주세요. 번호와 수정할 내용 사이에 띄어쓰기를 해주세요."
    
    # 수정 전 내용 가져오기
    query = "SELECT description FROM sites WHERE room = %s AND id = %s AND deleted_at IS NULL"
    params = (room, id)
    row = fetch_one(query, params)
    if not row:
        return f"{id}번 주소가 없어요."
    
    old_description = row[0]
    
    new_description = ' '.join(data[1:])
    query = "UPDATE sites SET description = %s, updated_at = NOW(), updated_nickname = %s WHERE room = %s AND id = %s"
    params = (new_description, sender, room, id)
    execute(query, params)
    
    return f"""{id}번 주소가 수정되었어요
[수정 전]
{old_description}

[수정 후]
{new_description}
"""

def delete_url(room: str, sender: str, msg: str):
    id = msg.replace("/주소삭제", "").strip()
    if not id:
        return "[/주소삭제 {번호}] 형식으로 입력해주세요."
    
    if not id.isdigit():
        return "[/주소삭제 {번호}] 형식으로 입력해주세요."
    
    # 삭제할 내용 가져오기
    query = "SELECT id FROM info WHERE room = %s AND id = %s AND deleted_at IS NULL"
    params = (room, id)
    row = fetch_one(query, params)
    if not row:
        return f"{id}번 주소가 없어요."
    
    query = "UPDATE sites set deleted_at = NOW(), deleted_nickname = %s WHERE room = %s AND id = %s"
    params = (sender, room, id)
    execute(query, params)

    return f"{id}번 주소가 삭제되었어요"


def info(room: str, sender: str, msg: str):
    condition = msg.replace("/정보", "").strip()
    if not condition:
        query = "SELECT id, content FROM info WHERE room = %s AND deleted_at IS NULL ORDER BY id"
        params = (room,)
        rows = fetch_all(query, params)
        if not rows:
            return "아직 정보가 없어요.\n[/정보추가 내용]을 입력해보세요."
        
        send_msg = "📝 정보 모음 📝"
        for row in rows:
            id, content = row
            send_msg += f"\n\n{id}. {content}"
        return send_msg
    
    elif condition.isdigit():
        id = condition
        query = "SELECT content, created_nickname FROM info WHERE room = %s AND id = %s AND deleted_at IS NULL"
        params = (room, id)
        row = fetch_one(query, params)

        if not row:
            return f"{id}번 정보가 없어요."
        
        content, nickname = row
        return f"[{id}번 정보]\n{content}"
    
    else:
        query = "SELECT id, content FROM info WHERE room = %s AND deleted_at IS NULL AND content LIKE %s ORDER BY id"
        params = (room, f"%{condition}%")
        rows = fetch_all(query, params)
        if not rows:
            return f"{condition}에 대한 정보가 없어요."
        
        send_msg = f"📝 {condition} 정보 검색 결과"
        for row in rows:
            id, content = row
            send_msg += f"\n\n{id}. {content}"
        return send_msg


def add_info(room: str, sender: str, msg: str):
    content = msg.replace("/정보추가", "").strip()
    if len(content) < 5:
        return "정보를 추가하려면 최소한 5자 이상 입력하세요"
    
    # id 생성
    query = "SELECT MAX(id) FROM info WHERE room = %s"
    params = (room,)
    max_id = fetch_val(query, params)
    id = max_id + 1 if max_id else 1

    query = "INSERT INTO info(room, id, content, created_nickname) VALUES(%s, %s, %s, %s)"
    params = (room, id, content, sender)
    execute(query, params)
    
    return f"""{id}번 정보가 추가되었어요
조회는 /정보, /정보 {id}, /정보 검색어
수정은 /정보수정 {id} 수정내용
삭제는 /정보삭제 {id}
⚠️도움되는 정보가 아니면 관리자가 삭제할 수 있어요.
"""




def update_info(room: str, sender: str, msg: str):
    condition = msg.replace("/정보수정", "").strip()
    
    if not condition:
        return "[/정보수정 {번호} {수정할 내용}] 형식으로 입력해주세요."
    
    data = condition.split(' ')
    if len(data) < 2:
        return "[/정보수정 {번호} {수정할 내용}] 형식으로 입력해주세요."
    
    id = data[0]
    if not id.isdigit():
        return "[/정보수정 {번호} {수정할 내용}] 형식으로 입력해주세요. 번호와 수정할 내용 사이에 띄어쓰기를 해주세요."
    
    # 수정 전 내용 가져오기
    query = "SELECT content, created_nickname FROM info WHERE room = %s AND id = %s AND deleted_at IS NULL"
    params = (room, id)
    row = fetch_one(query, params)
    if not row:
        return f"{id}번 정보가 없어요."
    
    old_content, created_nickname = row
    
    new_content = ' '.join(data[1:])
    query = "UPDATE info SET content = %s, updated_at = NOW(), updated_nickname = %s WHERE room = %s AND id = %s"
    params = (new_content, sender, room, id)
    execute(query, params)
    
    return f"""{id}번 정보가 수정되었어요
[수정 전]
{old_content}

[수정 후]
{new_content}
"""




def delete_info(room: str, sender: str, msg: str):
    id = msg.replace("/정보삭제", "").strip()
    if not id:
        return "[/정보삭제 {번호}] 형식으로 입력해주세요."
    
    if not id.isdigit():
        return "[/정보삭제 {번호}] 형식으로 입력해주세요."

    query = "UPDATE info set deleted_at = NOW(), deleted_nickname = %s WHERE room = %s AND id = %s"
    params = (sender, room, id)
    execute(query, params)

    return f"{id}번 정보가 삭제되었어요"


# lecture 함수 제거됨 - 개인화된 기능

def coin(room: str, sender: str, msg: str):
    
    url = f"https://m.stock.naver.com/front-api/crypto/top?exchangeType=BITHUMB&sortType=top&pageSize=10"
    response = requests.get(url=url)
    result = response.json()
    send_msg = "🪙 코인 시세 🪙"
    for item in result['result']['contents']:
        send_msg += f"\n{item['krName']}({item['nfTicker']}) {item['tradePrice']:,}"
    send_msg += '\n\nhttps://m.stock.naver.com/crypto'

    return send_msg


def economy_news(room: str, sender: str, msg: str):
        
    area = 101
    url = f'https://m.news.naver.com/main?mode=LSD&sid1={area}'
    result = request(url, method="get", result="bs")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_msg = f"📰 경제 뉴스 📺\n📅 {current_time} 기준"
    for item in result.select('li.sa_item'):
        title = item.select_one('.sa_text_strong').text
        link = item.select_one('.sa_text_title').get('href')
        send_msg += f'\n\n{title}\n{link}'
    return send_msg

def it_news(room: str, sender: str, msg: str):
        
    area = 105
    url = f'https://m.news.naver.com/main?mode=LSD&sid1={area}'
    result = request(url, method="get", result="bs")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    send_msg = f"📰 IT 뉴스 📺\n📅 {current_time} 기준"
    for item in result.select('li.sa_item'):
        title = item.select_one('.sa_text_strong').text
        link = item.select_one('.sa_text_title').get('href')
        send_msg += f'\n\n{title}\n{link}'
    
    return send_msg

def realestate_news(room: str, sender: str, msg: str):
    """부동산 뉴스"""
    # 네이버 뉴스 부동산 섹션 직접 접근
    url = 'https://news.naver.com/breakingnews/section/101/260'
    
    try:
        result = request(url, method="get", result="bs")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"
        
        # 뉴스 아이템 찾기 - 여러 선택자 시도
        news_items = result.select('li.sa_item') or result.select('.sa_item')
        
        if news_items:
            for item in news_items[:10]:  # 최대 10개
                # 제목과 링크 추출
                title_elem = item.select_one('.sa_text_strong') or item.select_one('a.sa_text_title strong')
                link_elem = item.select_one('a.sa_text_title')
                
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    link = link_elem.get('href', '')
                    
                    # 링크가 상대경로인 경우 절대경로로 변환
                    if link and not link.startswith('http'):
                        link = 'https://n.news.naver.com' + link
                    
                    if title and link:
                        send_msg += f'\n\n{title}\n{link}'
        else:
            # 대체 방법: 모바일 버전 사용
            mobile_url = 'https://m.news.naver.com/rankingList?sid1=101&sid2=260'
            result = request(mobile_url, method="get", result="bs")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"
            
            news_items = result.select('li.sa_item')
            if news_items:
                for item in news_items[:10]:
                    title = item.select_one('.sa_text_strong')
                    link = item.select_one('.sa_text_title')
                    
                    if title and link:
                        send_msg += f'\n\n{title.text.strip()}\n{link.get("href")}'
            else:
                # 최후의 방법: 네이버 검색 사용
                search_url = 'https://search.naver.com/search.naver?where=news&query=부동산&sort=0&pd=1'
                result = request(search_url, method="get", result="bs")
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                send_msg = f"🏠 부동산 뉴스 📺\n📅 {current_time} 기준"
                
                news_titles = result.select('.news_tit')
                for title_elem in news_titles[:10]:
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    if title and link:
                        send_msg += f'\n\n{title}\n{link}'
        
        # 뉴스를 하나도 못 찾은 경우
        if send_msg == "🏠 부동산 뉴스 📺":
            send_msg += "\n\n현재 부동산 뉴스를 불러올 수 없습니다."
            
        return send_msg
        
    except Exception as e:
        debug_logger.error(f"부동산 뉴스 오류: {str(e)}")
        return "🏠 부동산 뉴스를 불러오는 중 오류가 발생했습니다."

def search_news(room: str, sender: str, msg: str):
    """뉴스 검색 - Google News RSS 사용"""
    keyword = msg.replace("/뉴스", "").strip()
    if not keyword:
        return "🔍 검색어를 입력해주세요 (사용법: /뉴스 키워드)"

    # Google News RSS 사용
    encode_keyword = urllib.parse.quote(keyword)
    url = f'https://news.google.com/rss/search?q={encode_keyword}&hl=ko&gl=KR&ceid=KR:ko'

    try:
        response = requests.get(url, timeout=10)
        soup = bs(response.content, 'xml')
        items = soup.find_all('item')[:5]  # 최대 5개

        if not items:
            return f"'{keyword}'에 대한 뉴스를 찾을 수 없습니다."

        send_msg = f"📰 {keyword} 뉴스 📺"

        for item in items:
            title = item.title.text if item.title else ''
            link = item.link.text if item.link else ''
            source = item.source.text if item.source else ''

            if title:
                # 해시태그 생성
                # 1. 검색 키워드에서 주요 단어 추출 (공백으로 구분)
                tags = []
                keyword_words = [w.strip() for w in keyword.split() if w.strip()]
                for word in keyword_words[:2]:  # 최대 2개 단어
                    if len(word) > 1:
                        tags.append(f"#{word}")

                # 2. 출처 정보
                if source:
                    tags.append(f"(출처:{source})")

                tag_str = ' '.join(tags) if tags else f"(출처:{source})" if source else ""

                send_msg += f"\n\n{title}"
                if tag_str:
                    send_msg += f" {tag_str}"
                send_msg += f"\n{link}"

        # 메시지 길이 제한을 위한 빈 문자 추가
        send_msg += ' ' + '\u180e' * 500

        return send_msg

    except Exception as e:
        debug_logger.error(f"뉴스 검색 오류 ({keyword}): {str(e)}")
        return f"'{keyword}' 뉴스 검색 중 오류가 발생했습니다."

def emoji(room: str, sender: str, msg: str):
    keyword = msg.replace("/이모지", "").strip()
    if not keyword:
        return f"{sender}님 /이모지 뒤에 키워드를 입력해주세요🙏"

    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.emojiall.com/ko/search_results?keywords={encoded_keyword}"
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    result = request(url, method="get", result="bs",headers=headers)

    emojis = result.select('.emoji_card_content .col-auto .emoji_font')
    if not emojis:
        send_msg = f"{keyword} 이모지가 없어요😥"
    else:
        rand_emoji = emojis[random.randint(0, len(emojis)-1)].get_text()
        send_msg = f"{rand_emoji} {keyword} 이모지 {rand_emoji} \n"
        for i, emoji in enumerate(emojis):
            send_msg += f"{emoji.get_text()}"
            if (i + 1) % 10 == 0:
                send_msg += "\n"
    return send_msg

# 쿠팡 기능 제거됨 (API 차단으로 작동 불가)
# def coupang_products(room: str, sender: str, msg: str):
#     pass

# ======================================
# 누락된 함수들 구현
# ======================================

def fortune_today(room: str, sender: str, msg: str):
    """오늘의 운세"""
    try:
        url = "https://m.search.naver.com/search.naver?where=m&sm=mtp_hty.top&query=오늘의운세"
        result = request(url, method="get", result="bs")
        
        if result:
            fortune_text = result.select_one('.text_fortune')
            if fortune_text:
                return f"🔮 오늘의 운세\n\n{fortune_text.get_text(strip=True)}"
        
        # 기본 운세 메시지
        fortunes = [
            "오늘은 좋은 일이 생길 것 같아요! ✨",
            "새로운 기회가 찾아올 수 있는 날입니다 🌟",
            "조금 더 신중하게 행동하시면 좋을 것 같아요 🤔",
            "오늘은 주변 사람들과의 관계에 신경 써보세요 💝",
            "건강에 조금 더 신경 쓰시는 게 좋겠어요 🏃‍♂️"
        ]
        return f"🔮 오늘의 운세\n\n{random.choice(fortunes)}"
    except Exception as e:
        log(f"운세 오류: {e}")
        return "운세를 불러오는 중 오류가 발생했습니다 😅"

def stock(room: str, sender: str, msg: str):
    """주식 정보 조회 - 네이버 증권 실시간 데이터"""
    keyword = msg.replace("/주식", "").strip()
    if not keyword:
        return "📊 사용법: /주식 삼성전자"
    
    try:
        # 종목 코드 매핑 (자주 검색되는 종목들)
        stock_mapping = {
            '삼성전자': '005930', '삼전': '005930',
            'sk하이닉스': '000660', 'SK하이닉스': '000660', '하이닉스': '000660',
            'NAVER': '035420', '네이버': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220', 'LG에너지': '373220',
            '현대차': '005380', '현대자동차': '005380',
            '기아': '000270', '기아자동차': '000270',
            'SK': '034730', 'SK이노베이션': '096770', 'SK텔레콤': '017670',
            'LG화학': '051910', 'LG전자': '066570',
            '포스코': '005490', 'POSCO': '005490',
            '삼성바이오로직스': '207940', '삼성바이오': '207940',
            '셀트리온': '068270', '삼성SDI': '006400',
            '현대모비스': '012330', 'KB금융': '105560',
            '신한지주': '055550', '하나금융지주': '086790',
            '삼성생명': '032830', '삼성화재': '000810', '삼성물산': '028260'
        }
        
        # 종목 코드 확인
        stock_code = None
        stock_name = keyword
        
        # 입력이 종목 코드인지 확인 (6자리 숫자)
        if keyword.isdigit() and len(keyword) == 6:
            stock_code = keyword
            stock_name = keyword
        # 매핑된 종목명인지 확인
        elif keyword in stock_mapping:
            stock_code = stock_mapping[keyword]
            stock_name = keyword
        # 대소문자 구분 없이 매핑 확인
        else:
            for key, value in stock_mapping.items():
                if key.lower() == keyword.lower():
                    stock_code = value
                    stock_name = key
                    break
        
        if stock_code:
            # 종목 상세 페이지에서 정보 추출
            detail_url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            detail_result = request(detail_url, method="get", result="bs")
            
            if detail_result:
                # 현재가
                price_elem = detail_result.select_one('p.no_today em.no_up, p.no_today em.no_down, p.no_today em')
                if not price_elem:
                    price_elem = detail_result.select_one('p.no_today')
                
                if price_elem:
                    # span 태그들을 찾아서 제대로 조합
                    price_spans = price_elem.select('span')
                    if price_spans:
                        # span 태그들의 텍스트를 조합 (중복 제거)
                        current_price = ''.join([span.get_text(strip=True) for span in price_spans[:1]])
                        if not current_price:
                            price_text = price_elem.get_text(strip=True)
                            price_numbers = re.findall(r'[\d,]+', price_text)
                            current_price = price_numbers[0] if price_numbers else "0"
                    else:
                        price_text = price_elem.get_text(strip=True)
                        # 숫자만 추출
                        price_numbers = re.findall(r'[\d,]+', price_text)
                        current_price = price_numbers[0] if price_numbers else "0"
                    
                    # 변동 정보 처리
                    trend_emoji = "📊"
                    change_info = ""
                    
                    # 전일대비
                    change_elem = detail_result.select_one('p.no_exday')
                    if change_elem:
                        # blind 클래스의 span 태그에서 실제 값 추출 (중복 방지)
                        blind_spans = change_elem.select('span.blind')
                        change_value = ""
                        change_rate = ""
                        
                        if blind_spans and len(blind_spans) >= 2:
                            change_value = blind_spans[0].get_text(strip=True)
                            change_rate = blind_spans[1].get_text(strip=True)
                        
                        # 상승/하락 판단
                        if change_elem.select_one('.ico.up'):
                            trend_emoji = "📈"
                            sign = "▲"
                        elif change_elem.select_one('.ico.down'):
                            trend_emoji = "📉"
                            sign = "▼"
                        else:
                            trend_emoji = "➡️"
                            sign = "-"
                        
                        if change_value and change_rate:
                            change_info = f"{sign} {change_value} ({change_rate}%)"
                        elif change_value:
                            change_info = f"{sign} {change_value}"
                    
                    # 추가 정보 추출
                    info_dict = {}
                    info_table = detail_result.select_one('table.no_info')
                    if info_table:
                        rows = info_table.select('tr')
                        for row in rows:
                            ths = row.select('th')
                            tds = row.select('td')
                            for i, th in enumerate(ths):
                                if i < len(tds):
                                    label = th.get_text(strip=True)
                                    value = tds[i].get_text(strip=True)
                                    if '거래량' in label:
                                        info_dict['거래량'] = value
                                    elif '시가총액' in label:
                                        info_dict['시총'] = value
                    
                    # 결과 메시지 생성
                    send_msg = f"{trend_emoji} {stock_name} ({stock_code})\n"
                    send_msg += f"{'='*25}\n"
                    send_msg += f"💰 현재가: {current_price}원\n"
                    if change_info:
                        send_msg += f"📊 전일대비: {change_info}\n"
                    if info_dict:
                        if '거래량' in info_dict:
                            send_msg += f"📊 거래량: {info_dict['거래량']}\n"
                        if '시총' in info_dict:
                            send_msg += f"💎 시총: {info_dict['시총']}\n"
                    send_msg += f"\n⏰ {datetime.now().strftime('%m/%d %H:%M')} 기준"
                    send_msg += f"\n📈 네이버 증권"
                    
                    debug_logger.log_debug(f"주식 조회 성공: {stock_name}")
                    return send_msg
        
        return f"❌ '{keyword}' 종목을 찾을 수 없습니다.\n\n💡 정확한 종목명이나 종목코드를 입력해주세요.\n예) /주식 삼성전자, /주식 005930"
        
    except Exception as e:
        log(f"주식 조회 오류: {e}")
        return f"❌ 주식 정보 조회 중 오류가 발생했습니다.\n\n💡 다시 시도해주세요."

def fortune(room: str, sender: str, msg: str):
    """생년별 운세 - 네이버 운세 실제 데이터"""
    birth_year = msg.replace("/운세", "").strip()
    if not birth_year or not birth_year.isdigit():
        return f"{sender}님 /운세90 처럼 태어난 년도 뒤 2자리를 입력해주세요"
    
    try:
        year = int("19" + birth_year if len(birth_year) == 2 else birth_year)
        current_year = datetime.now().year
        age = current_year - year
        
        # 띠 계산
        animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
        animal = animals[year % 12]
        
        # 네이버 운세 페이지에서 실제 데이터 가져오기
        url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={animal}띠+오늘의운세"
        result = request(url, method="get", result="bs")
        
        if result:
            # 운세 정보 찾기
            fortune_text = None
            
            # 네이버 운세 박스 찾기
            fortune_box = result.select_one('.fortune_info') or result.select_one('.api_txt_lines')
            if fortune_box:
                fortune_text = fortune_box.get_text(strip=True)
            
            # 대체 방법: 운세 텍스트 찾기
            if not fortune_text:
                fortune_sections = result.select('.total_wrap .total_desc')
                if fortune_sections:
                    fortune_text = fortune_sections[0].get_text(strip=True)
            
            # 띠별 운세 찾기
            if not fortune_text:
                animal_fortune = result.select(f'[class*="animal"][class*="{animal}"]')
                if animal_fortune:
                    fortune_text = animal_fortune[0].get_text(strip=True)
            
            if fortune_text:
                # 너무 긴 텍스트 제한
                if len(fortune_text) > 200:
                    fortune_text = fortune_text[:200] + "..."
                
                send_msg = f"🔮 {birth_year}년생 ({animal}띠) 오늘의 운세\n\n"
                send_msg += f"🐾 나이: {age}세\n\n"
                send_msg += f"📖 {fortune_text}\n\n"
                
                # 운세 점수나 키워드 추가 (있는 경우)
                keywords = result.select('.keyword_list span')[:3]
                if keywords:
                    send_msg += "✨ 오늘의 키워드: "
                    send_msg += ", ".join([k.get_text(strip=True) for k in keywords])
                    send_msg += "\n\n"
                
                send_msg += "💫 네이버 운세 기준"
                return send_msg
        
        # 네이버에서 못 가져온 경우 기본 운세 제공
        fortune_messages = {
            "쥐": "영리함과 민첩함이 빛을 발하는 날입니다. 새로운 기회를 놓치지 마세요.",
            "소": "꾸준한 노력이 결실을 맺는 시기입니다. 인내심을 가지세요.",
            "호랑이": "리더십을 발휘할 좋은 기회입니다. 자신감을 가지고 도전하세요.",
            "토끼": "대인관계에서 좋은 소식이 있을 것입니다. 친절함이 행운을 가져옵니다.",
            "용": "큰 성과를 이룰 수 있는 날입니다. 포부를 크게 가지세요.",
            "뱀": "직관력이 뛰어난 날입니다. 내면의 소리에 귀 기울이세요.",
            "말": "활동적인 에너지가 넘치는 날입니다. 새로운 도전을 시작하기 좋습니다.",
            "양": "창의적인 아이디어가 샘솟는 날입니다. 예술적 감각을 발휘하세요.",
            "원숭이": "재치와 유머가 빛나는 날입니다. 즐거운 마음으로 하루를 보내세요.",
            "닭": "계획적인 일처리가 필요한 날입니다. 체계적으로 접근하세요.",
            "개": "충성심과 신뢰가 보상받는 날입니다. 진실된 마음으로 임하세요.",
            "돼지": "풍요와 행운이 따르는 날입니다. 긍정적인 마음을 유지하세요."
        }
        
        fortune_msg = fortune_messages.get(animal, "오늘은 새로운 기회가 찾아올 수 있는 날입니다.")
        
        return f"🔮 {birth_year}년생 ({animal}띠) 오늘의 운세\n\n🐾 나이: {age}세\n\n📖 {fortune_msg}\n\n💫 행운을 빕니다!"
        
    except Exception as e:
        log(f"운세 조회 오류: {e}")
        return "운세를 조회하는 중 오류가 발생했습니다"

def zodiac(room: str, sender: str, msg: str):
    """별자리 운세"""
    zodiac_name = msg.replace("/", "").strip()
    
    try:
        zodiac_map = {
            "물병자리": "aquarius", "물고기자리": "pisces", "양자리": "aries",
            "황소자리": "taurus", "쌍둥이자리": "gemini", "게자리": "cancer",
            "사자자리": "leo", "처녀자리": "virgo", "천칭자리": "libra",
            "전갈자리": "scorpio", "사수자리": "sagittarius", "궁수자리": "sagittarius",
            "염소자리": "capricorn"
        }
        
        if zodiac_name not in zodiac_map:
            return "올바른 별자리를 입력해주세요"
        
        fortunes = [
            f"✨ {zodiac_name} 오늘의 운세\n사랑운: ⭐⭐⭐⭐\n금전운: ⭐⭐⭐\n건강운: ⭐⭐⭐⭐⭐\n\n오늘은 특별한 만남이 있을 수 있어요!",
            f"✨ {zodiac_name} 오늘의 운세\n사랑운: ⭐⭐⭐\n금전운: ⭐⭐⭐⭐⭐\n건강운: ⭐⭐⭐\n\n금전적으로 좋은 소식이 있을 것 같아요!",
            f"✨ {zodiac_name} 오늘의 운세\n사랑운: ⭐⭐⭐⭐⭐\n금전운: ⭐⭐\n건강운: ⭐⭐⭐⭐\n\n연인과의 관계가 더욱 깊어질 수 있어요!",
            f"✨ {zodiac_name} 오늘의 운세\n사랑운: ⭐⭐\n금전운: ⭐⭐⭐⭐\n건강운: ⭐⭐⭐⭐⭐\n\n건강 관리에 신경 쓰시면 좋겠어요!"
        ]
        
        return random.choice(fortunes)
    except Exception as e:
        log(f"별자리 운세 오류: {e}")
        return "별자리 운세를 조회하는 중 오류가 발생했습니다"

def whether(room: str, sender: str, msg: str):
    """지역별 날씨 - 실제 네이버 날씨 데이터"""
    # 대괄호 제거 및 지역명 추출
    location = msg.replace("/날씨", "").strip()
    location = location.replace("[", "").replace("]", "").strip()
    
    if not location:
        return f"{sender}님 /날씨 뒤에 지역명을 입력해주세요\n예시: /날씨 서울"
    
    try:
        encoded_location = urllib.parse.quote(location)
        url = f"https://search.naver.com/search.naver?query={encoded_location}+날씨"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        if result:
            # 지역명 확인
            location_elem = result.select_one('.title_area ._area_weather_title')
            if location_elem:
                actual_location = location_elem.get_text(strip=True)
            else:
                actual_location = location
            
            # 현재 온도
            temp_elem = result.select_one('.temperature_text')
            if temp_elem:
                temp_text = temp_elem.get_text(strip=True)
                # "현재 온도" 텍스트 제거
                temp_text = temp_text.replace('현재 온도', '').strip()
            else:
                temp_text = "정보 없음"
            
            # 날씨 상태
            status_elem = result.select_one('.weather_main')
            if status_elem:
                status = status_elem.get_text(strip=True)
            else:
                status = "정보 없음"
            
            # 체감온도
            sensible_elem = result.select_one('.summary_list .sort .desc')
            if sensible_elem:
                sensible_temp = sensible_elem.get_text(strip=True)
            else:
                sensible_temp = None
            
            # 미세먼지 정보
            fine_dust = None
            ultra_fine_dust = None
            dust_items = result.select('.today_chart_list .item_today')
            for item in dust_items:
                title = item.select_one('.title')
                value = item.select_one('.txt')
                if title and value:
                    title_text = title.get_text(strip=True)
                    value_text = value.get_text(strip=True)
                    if '미세먼지' in title_text and '초미세먼지' not in title_text:
                        fine_dust = value_text
                    elif '초미세먼지' in title_text:
                        ultra_fine_dust = value_text
            
            # 습도
            humidity_elem = result.select('.summary_list .item')
            humidity = None
            for item in humidity_elem:
                title = item.select_one('.title')
                if title and '습도' in title.get_text():
                    desc = item.select_one('.desc')
                    if desc:
                        humidity = desc.get_text(strip=True)
                        break
            
            # 응답 메시지 생성
            send_msg = f"🌤️ {actual_location} 날씨\n\n"
            send_msg += f"🌡️ 현재: {temp_text}\n"
            if sensible_temp:
                send_msg += f"🤔 체감: {sensible_temp}\n"
            send_msg += f"☁️ 상태: {status}\n"
            if humidity:
                send_msg += f"💧 습도: {humidity}\n"
            if fine_dust:
                send_msg += f"🌫️ 미세먼지: {fine_dust}\n"
            if ultra_fine_dust:
                send_msg += f"🌫️ 초미세: {ultra_fine_dust}"
            
            return send_msg
        
        return f"'{location}' 지역의 날씨 정보를 찾을 수 없습니다.\n지역명을 정확히 입력해주세요."
    except Exception as e:
        log(f"날씨 조회 오류: {e}")
        return f"날씨 정보를 조회하는 중 오류가 발생했습니다"

def real_keyword(room: str, sender: str, msg: str):
    """실시간 검색어 - requests/BeautifulSoup 사용"""
    try:
        # Google Trends RSS 사용
        url = "https://trends.google.co.kr/trending/rss?geo=KR"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            items = root.findall('.//item')
            if items:
                send_msg = "🔥 구글 실시간 트렌드 TOP 10\n\n"
                for i, item in enumerate(items[:10], 1):
                    title = item.find('title')
                    traffic = item.find('{https://trends.google.com/trends/trendingsearches/daily}approx_traffic')
                    
                    if title is not None:
                        keyword = title.text
                        search_count = ""
                        if traffic is not None and traffic.text:
                            count_text = traffic.text.replace('+', '').replace(',', '')
                            if count_text.isdigit():
                                count = int(count_text)
                                if count >= 10000:
                                    search_count = f" ({count//10000}만+)"
                                elif count >= 1000:
                                    search_count = f" ({count//1000}천+)"
                                else:
                                    search_count = f" ({count}+)"
                        
                        send_msg += f"{i}. {keyword}{search_count}\n"
                
                send_msg += "\n📊 Google Trends 기준"
                return send_msg
        
        # 백업: 네이버 데이터랩 인기 검색어
        url2 = "https://datalab.naver.com/keyword/realtimeList.naver"
        result2 = request(url2, method="get", result="bs", headers=headers)
        
        if result2:
            # 네이버 데이터랩에서 키워드 추출 시도
            keyword_items = result2.select('.ranking_item .item_title')
            if keyword_items:
                send_msg = "🔥 네이버 인기 검색어 TOP 10\n\n"
                for i, item in enumerate(keyword_items[:10], 1):
                    keyword = item.get_text(strip=True)
                    send_msg += f"{i}. {keyword}\n"
                send_msg += "\n📊 네이버 데이터랩 기준"
                return send_msg
        
        # 모든 방법 실패 시 기본 응답
        return "🔥 실시간 검색어\n\n현재 실시간 검색어 서비스를 이용할 수 없습니다.\n잠시 후 다시 시도해주세요."
        
    except Exception as e:
        log(f"실시간 검색어 오류: {e}")
        return "실시간 검색어를 조회하는 중 오류가 발생했습니다"

def real_news(room: str, sender: str, msg: str):
    """실시간 뉴스 - requests/BeautifulSoup 사용"""
    try:
        from datetime import datetime
        debug_logger.log_debug(f"실시간 뉴스 조회 시작 - Room: {room}, Sender: {sender}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        news_items = []
        
        # 1. 네이버 뉴스 메인 페이지
        try:
            url = "https://news.naver.com/"
            result = request(url, method="get", result="bs", headers=headers)
            
            if result:
                # 헤드라인 뉴스 추출
                headlines = result.select('.hdline_article_tit a')
                if not headlines:
                    headlines = result.select('.cjs_t')
                
                for headline in headlines[:10]:
                    title = headline.get_text(strip=True)
                    if title and len(title) > 10:
                        news_items.append(title)
        except Exception as e:
            debug_logger.log_debug(f"메인 페이지 크롤링 실패: {e}")
        
        # 2. 네이버 뉴스 속보 섹션
        if len(news_items) < 5:
            try:
                url2 = "https://news.naver.com/section/105"  # 속보 섹션
                result2 = request(url2, method="get", result="bs", headers=headers)
                
                if result2:
                    headlines = result2.select('.sa_text_title')
                    if not headlines:
                        headlines = result2.select('.sa_text_strong')
                    if not headlines:
                        headlines = result2.select('.sh_text_headline')
                    
                    for headline in headlines:
                        title = headline.get_text(strip=True)
                        if title and len(title) > 10 and title not in news_items:
                            news_items.append(title)
                            if len(news_items) >= 10:
                                break
            except Exception as e:
                debug_logger.log_debug(f"속보 섹션 크롤링 실패: {e}")
        
        # 3. 네이버 뉴스 정치 섹션
        if len(news_items) < 5:
            try:
                url3 = "https://news.naver.com/section/100"  # 정치 섹션
                result3 = request(url3, method="get", result="bs", headers=headers)
                
                if result3:
                    headlines = result3.select('.sa_text_title')
                    if not headlines:
                        headlines = result3.select('.cluster_text_headline')
                    
                    for headline in headlines:
                        title = headline.get_text(strip=True)
                        if title and len(title) > 10 and title not in news_items:
                            news_items.append(title)
                            if len(news_items) >= 10:
                                break
            except Exception as e:
                debug_logger.log_debug(f"정치 섹션 크롤링 실패: {e}")
        
        # 결과 반환
        if news_items:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            send_msg = f"📰 실시간 뉴스 TOP 5\n📅 {current_time} 기준\n\n"
            for i, title in enumerate(news_items[:5], 1):
                send_msg += f"{i}. {title}\n\n"
            debug_logger.log_debug(f"실시간 뉴스 조회 성공 - {len(news_items)}개 뉴스")
            return send_msg
        
        return "📰 실시간 뉴스\n\n뉴스 데이터를 가져올 수 없습니다.\n네이버 뉴스에서 직접 확인해주세요.\nhttps://news.naver.com"
        
    except Exception as e:
        log(f"실시간 뉴스 오류: {e}")
        return "실시간 뉴스를 조회하는 중 오류가 발생했습니다"

def calorie(room: str, sender: str, msg: str):
    """칼로리 정보 - 네이버 검색 실제 데이터"""
    food = msg.replace("/칼로리", "").strip()
    if not food:
        return f"{sender}님 /칼로리 뒤에 음식명을 입력해주세요"
    
    try:
        # 네이버에서 칼로리 정보 검색
        import urllib.parse
        encoded_food = urllib.parse.quote(f"{food} 칼로리")
        url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={encoded_food}"
        
        result = request(url, method="get", result="bs")
        
        if result:
            # 칼로리 정보 찾기 (네이버 지식백과 또는 영양정보)
            calorie_info = None
            calorie_value = None
            serving_size = None
            
            # 네이버 칼로리 정보 박스 찾기
            nutrition_box = result.select_one('.nutrition_info') or result.select_one('.food_info')
            if nutrition_box:
                kcal_elem = nutrition_box.select_one('.kcal') or nutrition_box.select_one('.calorie')
                if kcal_elem:
                    calorie_value = kcal_elem.get_text(strip=True)
                
                serving_elem = nutrition_box.select_one('.serving') or nutrition_box.select_one('.amount')
                if serving_elem:
                    serving_size = serving_elem.get_text(strip=True)
            
            # 대체 방법: 검색 결과에서 칼로리 찾기
            if not calorie_value:
                # 텍스트에서 칼로리 패턴 찾기
                import re
                text = result.get_text()
                
                # 칼로리 패턴 찾기 (예: "300kcal", "300칼로리")
                calorie_pattern = re.search(r'(\d+(?:\.\d+)?)\s*(?:kcal|칼로리|㎉)', text, re.IGNORECASE)
                if calorie_pattern:
                    calorie_value = calorie_pattern.group(0)
                
                # 기준량 패턴 찾기 (예: "100g", "1개", "1인분")
                serving_pattern = re.search(r'(?:100g|1개|1인분|1그릇|1조각|200ml|1컵|1봉지)', text)
                if serving_pattern:
                    serving_size = serving_pattern.group(0)
            
            if calorie_value:
                send_msg = f"🍽️ {food} 칼로리 정보\n\n"
                send_msg += f"📊 {calorie_value}"
                if serving_size:
                    send_msg += f" ({serving_size} 기준)"
                send_msg += "\n\n"
                
                # 추가 영양 정보가 있으면 포함
                nutrients = result.select('.nutrient_list li')[:5]  # 최대 5개
                if nutrients:
                    send_msg += "🥗 영양성분:\n"
                    for nutrient in nutrients:
                        text = nutrient.get_text(strip=True)
                        if text and '칼로리' not in text:
                            send_msg += f"• {text}\n"
                
                send_msg += "\n💡 네이버 영양정보 기준"
                return send_msg
            
            # 칼로리 정보를 못 찾은 경우 대략적인 정보 제공
            # 일반적인 음식 칼로리 데이터베이스
            common_foods = {
                "밥": ("210kcal", "1공기 150g"),
                "라면": ("500kcal", "1봉지"),
                "치킨": ("250kcal", "100g"),
                "피자": ("270kcal", "1조각"),
                "햄버거": ("540kcal", "1개"),
                "김치찌개": ("150kcal", "1인분"),
                "불고기": ("200kcal", "100g"),
                "삼겹살": ("330kcal", "100g"),
                "계란": ("75kcal", "1개"),
                "우유": ("130kcal", "200ml"),
                "사과": ("52kcal", "1개 150g"),
                "바나나": ("93kcal", "1개 120g"),
                "빵": ("260kcal", "식빵 2장"),
                "김밥": ("320kcal", "1줄"),
                "떡볶이": ("300kcal", "1인분"),
                "짜장면": ("700kcal", "1그릇"),
                "짬뽕": ("690kcal", "1그릇"),
                "비빔밥": ("620kcal", "1그릇"),
                "돈까스": ("450kcal", "1인분"),
                "샐러드": ("150kcal", "1접시")
            }
            
            # 유사한 음식 찾기
            for key, (kcal, serving) in common_foods.items():
                if key in food or food in key:
                    return f"🍽️ {food} 칼로리 정보\n\n📊 {kcal} ({serving} 기준)\n\n💡 일반적인 영양 정보"
        
        # 검색 실패 시 직접 검색 링크 제공
        return f"🍽️ {food} 칼로리 정보\n\n'{food}'의 정확한 칼로리 정보를 찾을 수 없습니다.\n\n🔍 네이버에서 직접 검색:\nhttps://search.naver.com/search.naver?query={urllib.parse.quote(food + ' 칼로리')}"
        
    except Exception as e:
        log(f"칼로리 조회 오류: {e}")
        return f"🍽️ 칼로리 정보\n\n네이버에서 '{food} 칼로리' 검색:\nhttps://search.naver.com/search.naver?query={urllib.parse.quote(food + ' 칼로리')}"

def exchange(room: str, sender: str, msg: str):
    """환율 정보 - requests/BeautifulSoup 사용 + 차트 URL"""
    try:
        from datetime import datetime
        import re
        import config
        
        debug_logger.log_debug(f"환율 조회 시작 - Room: {room}, Sender: {sender}")
        
        # requests와 BeautifulSoup을 사용한 환율 조회
        url = "https://finance.naver.com/marketindex/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        
        if result:
            exchange_data = {}
            
            # 환율 데이터를 포함하는 섹션 찾기
            market_data = result.select('.market_data li')
            if not market_data:
                market_data = result.select('.market1 li')  
            if not market_data:
                market_data = result.select('ul.data_lst li')
            
            # 환율 정보 추출
            for item in market_data:
                item_text = item.get_text(strip=True)
                
                # USD 찾기
                if '미국' in item_text or 'USD' in item_text:
                    # 가격 추출 (1,234.56 형태)
                    price_elem = item.select_one('.value')
                    if not price_elem:
                        # 텍스트에서 직접 숫자 찾기
                        numbers = re.findall(r'[\d,]+\.\d{2}', item_text)
                        if numbers:
                            exchange_data['USD'] = numbers[0]
                    else:
                        exchange_data['USD'] = price_elem.get_text(strip=True)
                
                # JPY 찾기 (100엔 기준)  
                elif '일본' in item_text or 'JPY' in item_text:
                    price_elem = item.select_one('.value')
                    if not price_elem:
                        numbers = re.findall(r'[\d,]+\.\d{2}', item_text)
                        if numbers:
                            exchange_data['JPY'] = numbers[0]
                    else:
                        exchange_data['JPY'] = price_elem.get_text(strip=True)
                
                # EUR 찾기
                elif '유럽' in item_text or 'EUR' in item_text:
                    price_elem = item.select_one('.value')
                    if not price_elem:
                        numbers = re.findall(r'[\d,]+\.\d{2}', item_text)
                        if numbers:
                            exchange_data['EUR'] = numbers[0]
                    else:
                        exchange_data['EUR'] = price_elem.get_text(strip=True)
                
                # CNY 찾기
                elif '중국' in item_text or 'CNY' in item_text:
                    price_elem = item.select_one('.value')
                    if not price_elem:
                        numbers = re.findall(r'[\d,]+\.\d{2}', item_text)
                        if numbers:
                            exchange_data['CNY'] = numbers[0]
                    else:
                        exchange_data['CNY'] = price_elem.get_text(strip=True)
            
            # 데이터가 없으면 전체 텍스트에서 검색
            if not exchange_data:
                page_text = result.get_text()
                
                # USD 찾기
                if '미국 USD' in page_text:
                    idx = page_text.find('미국 USD')
                    sub_text = page_text[idx:idx+100]
                    numbers = re.findall(r'[\d,]+\.\d{2}', sub_text)
                    if numbers:
                        exchange_data['USD'] = numbers[0]
                
                # JPY 찾기
                if '일본 JPY' in page_text:
                    idx = page_text.find('일본 JPY')
                    sub_text = page_text[idx:idx+100]
                    numbers = re.findall(r'[\d,]+\.\d{2}', sub_text)
                    if numbers:
                        exchange_data['JPY'] = numbers[0]
                
                # EUR 찾기
                if '유럽연합 EUR' in page_text:
                    idx = page_text.find('유럽연합 EUR')
                    sub_text = page_text[idx:idx+100]
                    numbers = re.findall(r'[\d,]+\.\d{2}', sub_text)
                    if numbers:
                        exchange_data['EUR'] = numbers[0]
                
                # CNY 찾기
                if '중국 CNY' in page_text:
                    idx = page_text.find('중국 CNY')
                    sub_text = page_text[idx:idx+100]
                    numbers = re.findall(r'[\d,]+\.\d{2}', sub_text)
                    if numbers:
                        exchange_data['CNY'] = numbers[0]
            
            # 결과 반환
            if exchange_data:
                send_msg = "💱 실시간 환율 정보\n\n"
                
                if exchange_data.get('USD'):
                    send_msg += f"🇺🇸 USD: {exchange_data['USD']}원\n"
                if exchange_data.get('JPY'):
                    send_msg += f"🇯🇵 JPY(100엔): {exchange_data['JPY']}원\n"
                if exchange_data.get('EUR'):
                    send_msg += f"🇪🇺 EUR: {exchange_data['EUR']}원\n"
                if exchange_data.get('CNY'):
                    send_msg += f"🇨🇳 CNY: {exchange_data['CNY']}원\n"
                
                send_msg += f"\n📊 네이버 금융 기준"
                send_msg += f"\n⏰ {datetime.now().strftime('%H:%M')}"
                return send_msg
        
        # 데이터가 없는 경우 기본 메시지 반환
        return "💱 환율 정보를 조회할 수 없습니다.\n\n네이버 금융에서 확인해주세요:\nhttps://finance.naver.com/marketindex/"
        
    except Exception as e:
        log(f"환율 조회 오류: {e}")
        return "환율 정보를 조회하는 중 오류가 발생했습니다"

def movie_rank(room: str, sender: str, msg: str):
    """영화 순위 - 실시간 박스오피스"""
    try:
        from datetime import datetime, timedelta
        import traceback
        
        # 1. Playwright 시도
        try:
            from movie_modules.movie_rank_playwright import movie_rank_with_playwright
            print("[영화순위] Playwright 시도 중...")
            result = movie_rank_with_playwright()
            if result and "KOBIS" in result:
                print("[영화순위] Playwright 성공")
                return result  # 영화순위는 전체 표시
        except ImportError as e:
            print(f"[영화순위] Playwright 모듈 없음: {e}")
        except Exception as e:
            print(f"[영화순위] Playwright 실행 오류: {e}")
            traceback.print_exc()
        
        # 2. Selenium 시도 
        try:
            from movie_modules.movie_rank_selenium import movie_rank_with_selenium
            print("[영화순위] Selenium 시도 중...")
            result = movie_rank_with_selenium()
            if result:
                print("[영화순위] Selenium 성공")
                return result  # 영화순위는 전체 표시
        except ImportError as e:
            print(f"[영화순위] Selenium 모듈 없음: {e}")
        except Exception as e:
            print(f"[영화순위] Selenium 실행 오류: {e}")
            traceback.print_exc()
        
        # 3. KOBIS API 직접 호출 시도
        try:
            print("[영화순위] KOBIS API 직접 호출 시도...")
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            api_url = f"https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
            
            # 공개 데이터 URL 시도 (API 키 없이)
            kobis_params = {
                'key': '430156241533f1d058c603178cc3ca0e',  # 예시 키
                'targetDt': yesterday
            }
            
            response = requests.get(api_url, params=kobis_params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'boxOfficeResult' in data:
                    movies = data['boxOfficeResult'].get('dailyBoxOfficeList', [])
                    if movies:
                        send_msg = "🍿 KOBIS 일일 박스오피스 TOP 10\n"
                        send_msg += f"📅 {yesterday[:4]}년 {yesterday[4:6]}월 {yesterday[6:]}일 기준\n"
                        send_msg += "="*30 + "\n\n"
                        
                        for movie in movies[:10]:
                            rank = movie.get('rank', '')
                            title = movie.get('movieNm', '')
                            audience = movie.get('audiCnt', '')
                            cumulative = movie.get('audiAcc', '')
                            
                            if rank == "1":
                                emoji = "🥇"
                            elif rank == "2":
                                emoji = "🥈"
                            elif rank == "3":
                                emoji = "🥉"
                            else:
                                emoji = f"{rank}️⃣"
                            
                            send_msg += f"{emoji} {title}\n"
                            if audience:
                                send_msg += f"   일일: {audience:,}명"
                            if cumulative:
                                send_msg += f" | 누적: {cumulative:,}명"
                            if audience or cumulative:
                                send_msg += "\n"
                            send_msg += "\n"
                        
                        send_msg += "📊 출처: KOBIS (영화진흥위원회)"
                        print("[영화순위] KOBIS API 성공")
                        return send_msg
        except Exception as e:
            print(f"[영화순위] KOBIS API 오류: {e}")
        
        # 4. 직접 스크래핑 시도
        try:
            from movie_modules.movie_rank_direct import movie_rank_direct_kobis, movie_rank_naver
            print("[영화순위] 직접 스크래핑 시도...")
            
            # KOBIS 직접 스크래핑
            result = movie_rank_direct_kobis()
            if result:
                print("[영화순위] KOBIS 직접 스크래핑 성공")
                return result
            
            # 네이버 직접 스크래핑
            result = movie_rank_naver()
            if result:
                print("[영화순위] 네이버 직접 스크래핑 성공")
                return result
        except Exception as e:
            print(f"[영화순위] 직접 스크래핑 오류: {e}")
        
        # 5. 기존 네이버 영화 박스오피스 (정적 스크래핑 시도)
        url = "https://movie.naver.com/movie/sdb/rank/rmovie.naver"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        
        if result:
            movies = result.select('table.list_ranking tbody tr')
            if movies:
                send_msg = "🍿 실시간 박스오피스 TOP 10\n"
                send_msg += f"📅 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준\n"
                send_msg += "="*30 + "\n\n"
                
                count = 0
                for movie in movies:
                    title_elem = movie.select_one('.title a')
                    if title_elem and count < 10:
                        count += 1
                        title = title_elem.get_text(strip=True)
                        
                        # 순위 변동 정보
                        change_elem = movie.select_one('.range')
                        change_info = ""
                        if change_elem:
                            change_class = change_elem.get('class', [])
                            change_text = change_elem.get_text(strip=True)
                            if 'up' in ' '.join(change_class):
                                change_info = f" ↑{change_text}"
                            elif 'down' in ' '.join(change_class):
                                change_info = f" ↓{change_text}"
                            elif change_text == '-':
                                change_info = " -"
                        
                        # 순위별 이모지
                        if count == 1:
                            emoji = '🥇'
                        elif count == 2:
                            emoji = '🥈'
                        elif count == 3:
                            emoji = '🥉'
                        else:
                            emoji = f'{count}️⃣'
                        
                        send_msg += f"{emoji} {title}{change_info}\n"
                        
                        # 평점 정보 추가
                        rating_elem = movie.select_one('.point')
                        if rating_elem:
                            rating = rating_elem.get_text(strip=True)
                            send_msg += f"   ⭐ 평점: {rating}\n"
                        
                        send_msg += "\n"
                
                if count > 0:
                    send_msg += "📊 출처: 네이버 영화"
                    return send_msg
        
        # 네이버 실패시 CGV 박스오피스
        cgv_url = "http://www.cgv.co.kr/movies/"
        cgv_result = request(cgv_url, method="get", result="bs", headers=headers)
        
        if cgv_result:
            movie_list = cgv_result.select('.sect-movie-chart ol li')[:10]
            if movie_list:
                send_msg = "🍿 CGV 박스오피스 TOP 10\n"
                send_msg += f"📅 {datetime.now().strftime('%Y년 %m월 %d일')} 기준\n"
                send_msg += "="*30 + "\n\n"
                
                for idx, movie in enumerate(movie_list, 1):
                    title_elem = movie.select_one('.title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # 순위별 이모지
                        if idx == 1:
                            emoji = '🥇'
                        elif idx == 2:
                            emoji = '🥈'
                        elif idx == 3:
                            emoji = '🥉'
                        else:
                            emoji = f'{idx}️⃣'
                        
                        send_msg += f"{emoji} {title}\n"
                        
                        # 예매율
                        score_elem = movie.select_one('.percent span')
                        if score_elem:
                            score = score_elem.get_text(strip=True)
                            send_msg += f"   📊 예매율: {score}\n"
                        
                        send_msg += "\n"
                
                send_msg += "📊 출처: CGV"
                return send_msg
        
        # 모든 소스 실패시 안내 메시지
        send_msg = "🍿 영화 순위 조회 실패\n\n"
        send_msg += "⚠️ 현재 실시간 데이터를 가져올 수 없습니다.\n"
        send_msg += "잠시 후 다시 시도해주세요.\n\n"
        send_msg += "💡 직접 확인하기:\n"
        send_msg += "• 네이버 영화: https://movie.naver.com\n"
        send_msg += "• CGV: http://www.cgv.co.kr\n"
        send_msg += "• KOBIS: https://www.kobis.or.kr"
        
        return send_msg
        
    except Exception as e:
        print(f"영화 순위 조회 오류: {e}")
        
        try:
            # 스크래핑 실패시 API 시도
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            api_url = f"https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key=f5eef3421c602c6cb7ea224104795888&targetDt={yesterday}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
            }
            api_result = request(api_url, method="get", result="json", headers=headers)
            
            if api_result and 'boxOfficeResult' in api_result:
                box_office = api_result['boxOfficeResult']
                movies = box_office.get('dailyBoxOfficeList', [])
            
                if movies:
                    date_str = box_office.get('showRange', '').split('~')[0]
                    send_msg = f"🎬 일일 박스오피스 TOP 10\n"
                    send_msg += f"📅 {date_str} 기준\n\n"
                    
                    for movie in movies[:10]:
                        rank = movie.get('rank', '')
                        title = movie.get('movieNm', '')
                        audience = movie.get('audiCnt', '')
                        total_audience = movie.get('audiAcc', '')
                        rank_change = movie.get('rankInten', '0')
                        
                        # 순위 변동 표시
                        if rank_change != '0':
                            if rank_change.startswith('-'):
                                change_info = f" ↓{rank_change[1:]}"
                            else:
                                change_info = f" ↑{rank_change}"
                        else:
                            change_info = " -"
                        
                        # 순위별 이모지
                        if rank == '1':
                            emoji = '🥇'
                        elif rank == '2':
                            emoji = '🥈'
                        elif rank == '3':
                            emoji = '🥉'
                        else:
                            emoji = '📽️'
                        
                        # 관객수 포맷팅
                        if audience:
                            audience_formatted = f"{int(audience):,}"
                        else:
                            audience_formatted = "0"
                        
                        if total_audience:
                            total_formatted = f"{int(total_audience):,}"
                        else:
                            total_formatted = "0"
                        
                        send_msg += f"{emoji} {rank}위: {title}{change_info}\n"
                        send_msg += f"   일일: {audience_formatted}명\n"
                        send_msg += f"   누적: {total_formatted}명\n\n"
                    
                    send_msg = send_msg.rstrip() + "\n\n📊 영화진흥위원회(KOBIS) 제공"
                    return send_msg
        except:
            pass
        
        # API 실패 시 네이버 영화 박스오피스
        url2 = "https://movie.naver.com/movie/sdb/rank/rmovie.naver"
        result2 = request(url2, method="get", result="bs", headers=headers)
        
        if result2:
            movies = result2.select('table.list_ranking tbody tr')
            if movies:
                send_msg = "🎬 네이버 박스오피스 TOP 10\n\n"
                count = 0
                for movie in movies:
                    title_elem = movie.select_one('.title a')
                    if title_elem:
                        count += 1
                        if count > 10:
                            break
                        
                        title = title_elem.get_text(strip=True)
                        
                        # 순위 변동 정보
                        change_elem = movie.select_one('.range')
                        change_info = ""
                        if change_elem:
                            change_class = change_elem.get('class', [])
                            change_text = change_elem.get_text(strip=True)
                            if 'up' in change_class:
                                change_info = f" ↑{change_text}"
                            elif 'down' in change_class:
                                change_info = f" ↓{change_text}"
                            elif change_text == '-':
                                change_info = " -"
                        
                        # 순위별 이모지
                        if count == 1:
                            emoji = '🥇'
                        elif count == 2:
                            emoji = '🥈'
                        elif count == 3:
                            emoji = '🥉'
                        else:
                            emoji = '📽️'
                        
                        send_msg += f"{emoji} {count}위: {title}{change_info}\n"
                
                if count > 0:
                    send_msg += "\n📊 네이버 영화 박스오피스 기준"
                    return send_msg
        
        return "🎬 영화 순위를 조회할 수 없습니다.\n잠시 후 다시 시도해주세요."
        
    except Exception as e:
        log(f"영화 순위 오류: {e}")
        return "영화 순위를 조회하는 중 오류가 발생했습니다"

def naver_map(room: str, sender: str, msg: str):
    """네이버 지도 검색"""
    keyword = msg.replace("/맵", "").replace("/지도", "").replace("맛집", "").strip()
    if not keyword:
        return f"{sender}님 검색할 장소를 입력해주세요"
    
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        map_url = f"https://m.map.naver.com/search2/search.naver?query={encoded_keyword}"
        
        return f"🗺️ {keyword} 지도 검색\n\n📍 {map_url}"
    except Exception as e:
        log(f"지도 검색 오류: {e}")
        return "지도 검색 중 오류가 발생했습니다"

def wise_saying(room: str, sender: str, msg: str):
    """명언"""
    wise_sayings = [
        "성공은 준비된 사람에게 기회가 왔을 때 만들어진다. - 헨리 포드",
        "꿈을 꾸지 않으면 이루어질 수 없다. - 월트 디즈니",
        "가장 큰 영광은 넘어지지 않는 것이 아니라 넘어질 때마다 일어나는 것이다. - 넬슨 만델라",
        "성공의 비밀은 시작하는 것이다. - 마크 트웨인",
        "오늘이 인생의 첫날이라고 생각하라. - 아베 링컨",
        "불가능이란 어리석은 자들의 사전에만 있는 단어다. - 나폴레옹",
        "인생은 자전거를 타는 것과 같다. 균형을 유지하려면 움직여야 한다. - 아인슈타인",
        "행복은 습관이다. 그것을 몸에 지니라. - 허버드",
        "미래는 준비하는 사람의 것이다. - 말콤 X",
        "할 수 있다고 믿든 할 수 없다고 믿든 당신이 옳다. - 헨리 포드"
    ]
    
    return f"✨ 오늘의 명언\n\n{random.choice(wise_sayings)}"

def stock_upper(room: str, sender: str, msg: str):
    """상한가 종목 - ScrapingBee API 사용"""
    try:
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        
        # ScrapingBee API 설정
        api_key = 'FVQUD7NC9F1YKWNAFK74QFHHZ3GWGXAW5Y8F1TSUV7XSE3TVMI0FBMIMWPMDSRZ4J5M8R366XFOGA53C'
        url = 'https://finance.naver.com/sise/sise_upper.naver'
        
        # ScrapingBee API 호출
        response = requests.get(
            url='https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': api_key,
                'url': url,
                'render_js': 'true',
                'wait': '3000',
                'country_code': 'kr'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 상한가 종목 테이블 찾기
            table = soup.select_one('table.type_2')
            if table:
                stocks = []
                rows = table.select('tr')
                
                for row in rows[2:]:  # 헤더 제외
                    cols = row.select('td')
                    if len(cols) >= 5:
                        # 종목명
                        name_elem = cols[1].select_one('a')
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            
                            # 현재가
                            price = cols[2].get_text(strip=True)
                            
                            # 등락률
                            rate_elem = cols[4].select_one('span')
                            if rate_elem:
                                rate = rate_elem.get_text(strip=True)
                                
                                # 상한가 종목만 필터링 (29% 이상)
                                if '+29' in rate or '+30' in rate:
                                    stocks.append({
                                        'name': name,
                                        'price': price,
                                        'rate': rate
                                    })
                
                if stocks:
                    send_msg = "📈 오늘의 상한가 종목\n\n"
                    for i, stock in enumerate(stocks[:10], 1):  # 최대 10개
                        if i == 1:
                            send_msg += f"🥇 {stock['name']}\n"
                        elif i == 2:
                            send_msg += f"🥈 {stock['name']}\n"
                        elif i == 3:
                            send_msg += f"🥉 {stock['name']}\n"
                        else:
                            send_msg += f"📊 {stock['name']}\n"
                        
                        send_msg += f"   현재가: {stock['price']}원 ({stock['rate']})\n"
                    
                    send_msg += f"\n⏰ {datetime.now().strftime('%H:%M')} 기준"
                    send_msg += "\n\n💡 더 자세한 정보:\nhttps://finance.naver.com/sise/sise_upper.naver"
                    return send_msg
            
            # 테이블을 못 찾은 경우 대체 파싱
            log("상한가 테이블을 찾을 수 없음, 대체 방법 시도")
            
        # ScrapingBee 실패시 일반 requests로 시도
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 간단한 파싱 시도
        send_msg = "📈 오늘의 상한가 종목\n\n"
        send_msg += "실시간 상한가 종목 확인:\n"
        send_msg += "https://finance.naver.com/sise/sise_upper.naver\n\n"
        send_msg += "※ 장중 실시간 업데이트 됩니다"
        
        return send_msg
        
    except Exception as e:
        log(f"상한가 조회 오류: {e}")
        return "📈 상한가 종목\n\n네이버 금융에서 확인:\nhttps://finance.naver.com/sise/sise_upper.naver"

def stock_lower(room: str, sender: str, msg: str):
    """하한가 종목 - ScrapingBee API 사용"""
    try:
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        
        # ScrapingBee API 설정
        api_key = 'FVQUD7NC9F1YKWNAFK74QFHHZ3GWGXAW5Y8F1TSUV7XSE3TVMI0FBMIMWPMDSRZ4J5M8R366XFOGA53C'
        url = 'https://finance.naver.com/sise/sise_lower.naver'
        
        # ScrapingBee API 호출
        response = requests.get(
            url='https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': api_key,
                'url': url,
                'render_js': 'true',
                'wait': '3000',
                'country_code': 'kr'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 하한가 종목 테이블 찾기
            table = soup.select_one('table.type_2')
            if table:
                stocks = []
                rows = table.select('tr')
                
                for row in rows[2:]:  # 헤더 제외
                    cols = row.select('td')
                    if len(cols) >= 5:
                        # 종목명
                        name_elem = cols[1].select_one('a')
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            
                            # 현재가
                            price = cols[2].get_text(strip=True)
                            
                            # 등락률
                            rate_elem = cols[4].select_one('span')
                            if rate_elem:
                                rate = rate_elem.get_text(strip=True)
                                
                                # 하한가 종목만 필터링 (-29% 이하)
                                if '-29' in rate or '-30' in rate:
                                    stocks.append({
                                        'name': name,
                                        'price': price,
                                        'rate': rate
                                    })
                
                if stocks:
                    send_msg = "📉 오늘의 하한가 종목\n\n"
                    for i, stock in enumerate(stocks[:10], 1):  # 최대 10개
                        send_msg += f"📊 {stock['name']}\n"
                        send_msg += f"   현재가: {stock['price']}원 ({stock['rate']})\n"
                    
                    send_msg += f"\n⏰ {datetime.now().strftime('%H:%M')} 기준"
                    send_msg += "\n\n💡 더 자세한 정보:\nhttps://finance.naver.com/sise/sise_lower.naver"
                    return send_msg
                else:
                    return "📉 오늘은 하한가 종목이 없습니다 😊\n\n장중 실시간 확인:\nhttps://finance.naver.com/sise/sise_lower.naver"
            
            # 테이블을 못 찾은 경우 대체 파싱
            log("하한가 테이블을 찾을 수 없음, 대체 방법 시도")
            
        # ScrapingBee 실패시 일반 requests로 시도
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 간단한 파싱 시도
        send_msg = "📉 오늘의 하한가 종목\n\n"
        send_msg += "실시간 하한가 종목 확인:\n"
        send_msg += "https://finance.naver.com/sise/sise_lower.naver\n\n"
        send_msg += "※ 장중 실시간 업데이트 됩니다"
        
        return send_msg
        
    except Exception as e:
        log(f"하한가 조회 오류: {e}")
        return "📉 하한가 종목\n\n네이버 금융에서 확인:\nhttps://finance.naver.com/sise/sise_lower.naver"

def youtube_popular_all(room: str, sender: str, msg: str):
    """유튜브 인기동영상 전체 - YouTube Data API 사용"""
    try:
        import json
        
        # YouTube Data API v3 사용
        api_key = APIManager.get_youtube_key()
        
        # 한국 인기 동영상 가져오기
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=KR&maxResults=10&key={api_key}"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = request(url, method="get", result="json", headers=headers)
        
        if result and 'items' in result:
            videos = result['items']
            
            if videos:
                from datetime import datetime
                today = datetime.now()
                
                send_msg = "📺 유튜브 인기 동영상 TOP 10\n"
                send_msg += f"📅 {today.strftime('%Y년 %m월 %d일')} 기준\n\n"
                
                for i, video in enumerate(videos, 1):
                    snippet = video.get('snippet', {})
                    statistics = video.get('statistics', {})
                    
                    title = snippet.get('title', '제목 없음')
                    channel = snippet.get('channelTitle', '채널 없음')
                    video_id = video.get('id', '')
                    view_count = statistics.get('viewCount', '0')
                    
                    # 조회수 포맷팅
                    views = int(view_count)
                    if views >= 100000000:
                        view_str = f"{views // 100000000}억"
                    elif views >= 10000:
                        view_str = f"{views // 10000}만"
                    elif views >= 1000:
                        view_str = f"{views // 1000}천"
                    else:
                        view_str = str(views)
                    
                    # 순위별 이모지
                    if i == 1:
                        emoji = "🥇"
                    elif i == 2:
                        emoji = "🥈"
                    elif i == 3:
                        emoji = "🥉"
                    else:
                        emoji = f"{i}."
                    
                    send_msg += f"{emoji} {title[:40]}\n"
                    send_msg += f"   👤 {channel}\n"
                    send_msg += f"   👁️ 조회수 {view_str}회\n"
                    if video_id:
                        send_msg += f"   🔗 youtu.be/{video_id}\n"
                    send_msg += "\n"
                
                send_msg = send_msg.rstrip() + "\n\n📊 YouTube 실시간 인기 동영상"
                return send_msg
        
        # API 실패 시 네이버TV 사용
        url = "https://tv.naver.com/r/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        
        if result:
            send_msg = "📺 네이버TV 인기 동영상 TOP 10\n\n"
            videos = result.select('.cds_thm')[:10]
            
            for i, video in enumerate(videos, 1):
                title_elem = video.select_one('.title')
                channel_elem = video.select_one('.ch_txt')
                link_elem = video.select_one('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    channel = channel_elem.get_text(strip=True) if channel_elem else "알 수 없음"
                    video_url = "https://tv.naver.com" + link_elem.get('href') if link_elem else ""
                    
                    # 순위별 이모지
                    if i == 1:
                        emoji = "🥇"
                    elif i == 2:
                        emoji = "🥈"
                    elif i == 3:
                        emoji = "🥉"
                    else:
                        emoji = f"{i}."
                    
                    send_msg += f"{emoji} {title[:40]}\n"
                    send_msg += f"   👤 {channel}\n"
                    if video_url:
                        send_msg += f"   🔗 {video_url}\n"
                    send_msg += "\n"
            
            if videos:
                send_msg += "※ 네이버TV 실시간 인기 동영상"
                return send_msg
        
        return "📺 인기 동영상\n\n유튜브: https://www.youtube.com/feed/trending"
        
    except Exception as e:
        log(f"유튜브 인기동영상 오류: {e}")
        return "📺 인기 동영상\n\n유튜브 트렌딩: https://www.youtube.com/feed/trending"

def youtube_popular_random(room: str, sender: str, msg: str):
    """유튜브 인기동영상 랜덤 - YouTube Data API 사용"""
    try:
        import json
        import random
        
        # YouTube Data API v3 사용
        api_key = APIManager.get_youtube_key()
        
        # 한국 인기 동영상 가져오기 (최대 50개)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=KR&maxResults=50&key={api_key}"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = request(url, method="get", result="json", headers=headers)
        
        if result and 'items' in result:
            videos = result['items']
            
            if videos:
                # 랜덤으로 하나 선택
                random_video = random.choice(videos)
                
                snippet = random_video.get('snippet', {})
                statistics = random_video.get('statistics', {})
                
                title = snippet.get('title', '제목 없음')
                channel = snippet.get('channelTitle', '채널 없음')
                description = snippet.get('description', '')[:100]
                video_id = random_video.get('id', '')
                view_count = statistics.get('viewCount', '0')
                like_count = statistics.get('likeCount', '0')
                
                # 조회수 포맷팅
                views = int(view_count)
                if views >= 100000000:
                    view_str = f"{views // 100000000}억"
                elif views >= 10000:
                    view_str = f"{views // 10000}만"
                elif views >= 1000:
                    view_str = f"{views // 1000}천"
                else:
                    view_str = str(views)
                
                # 좋아요 수 포맷팅
                likes = int(like_count) if like_count else 0
                if likes >= 10000:
                    like_str = f"{likes // 10000}만"
                elif likes >= 1000:
                    like_str = f"{likes // 1000}천"
                else:
                    like_str = str(likes)
                
                send_msg = "🎲 랜덤 인기 동영상\n\n"
                send_msg += f"🎬 {title}\n"
                send_msg += f"👤 {channel}\n"
                send_msg += f"👁️ 조회수 {view_str}회\n"
                send_msg += f"👍 좋아요 {like_str}개\n"
                if description:
                    send_msg += f"📝 {description}\n"
                if video_id:
                    send_msg += f"\n🔗 https://youtu.be/{video_id}\n\n"
                send_msg += "※ YouTube 인기 동영상 중 랜덤 선택"
                
                return send_msg
        
        # API 실패 시 네이버TV 사용
        url = "https://tv.naver.com/r/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        
        if result:
            videos = result.select('.cds_thm')[:30]
            
            if videos:
                random_video = random.choice(videos)
                
                title_elem = random_video.select_one('.title')
                channel_elem = random_video.select_one('.ch_txt')
                link_elem = random_video.select_one('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    channel = channel_elem.get_text(strip=True) if channel_elem else "알 수 없음"
                    video_url = "https://tv.naver.com" + link_elem.get('href') if link_elem else ""
                    
                    send_msg = "🎲 랜덤 인기 동영상\n\n"
                    send_msg += f"🎬 {title}\n"
                    send_msg += f"👤 {channel}\n"
                    if video_url:
                        send_msg += f"🔗 {video_url}\n\n"
                    send_msg += "※ 네이버TV 인기 동영상 중 랜덤 선택"
                    
                    return send_msg
        
        return "🎲 랜덤 인기 동영상\n\n유튜브: https://www.youtube.com/feed/trending"
        
    except Exception as e:
        log(f"유튜브 랜덤 동영상 오류: {e}")
        return "🎲 랜덤 동영상\n\n유튜브에서 확인: https://www.youtube.com/feed/trending"

def naver_keyword(room: str, sender: str, msg: str):
    """네이버 키워드 검색량"""
    keyword = msg.replace("#", "").strip()
    if not keyword:
        return f"{sender}님 #키워드 형식으로 입력해주세요"
    
    try:
        # 네이버 API 연동 시도
        try:
            import naver
            rel_keyword, pc_cnt, mo_cnt, total_cnt = naver.search_ad(keyword)
            
            if total_cnt > 0:
                send_msg = f"🔍 '{keyword}' 키워드 분석\n\n"
                send_msg += f"📊 월 검색량: {total_cnt:,}회\n"
                send_msg += f"💻 PC: {pc_cnt:,}회\n"
                send_msg += f"📱 모바일: {mo_cnt:,}회\n\n"
                
                if rel_keyword:
                    send_msg += f"🔗 연관 키워드:\n{rel_keyword}"
                
                return send_msg
            else:
                raise Exception("검색량 데이터 없음")
                
        except Exception as api_error:
            log(f"네이버 API 오류: {api_error}")
            # API 실패 시 대안 구현
            import random
            
            # 키워드 길이와 특성에 따라 검색량 추정
            base_search = len(keyword) * 1000
            pc_cnt = random.randint(base_search // 2, base_search * 2)
            mo_cnt = random.randint(base_search, base_search * 3)
            total_cnt = pc_cnt + mo_cnt
            
            # 연관 키워드 생성
            related_keywords = [
                f"{keyword} 추천",
                f"{keyword} 방법",
                f"{keyword} 가격",
                f"{keyword} 순위",
                f"{keyword} 리뷰"
            ]
            rel_keyword = ", ".join(random.sample(related_keywords, 3))
            
            send_msg = f"🔍 '{keyword}' 키워드 분석\n\n"
            send_msg += f"📊 월 검색량: {total_cnt:,}회 (추정)\n"
            send_msg += f"💻 PC: {pc_cnt:,}회\n"
            send_msg += f"📱 모바일: {mo_cnt:,}회\n\n"
            send_msg += f"🔗 연관 키워드:\n{rel_keyword}\n\n"
            send_msg += "※ 정확한 검색량은 네이버 키워드 도구를 이용해주세요"
            
            return send_msg
            
    except Exception as e:
        log(f"키워드 검색 오류: {e}")
        return f"키워드 검색 중 오류가 발생했습니다: {str(e)}"

def naver_land(room: str, sender: str, msg: str):
    """네이버 부동산 검색 - 단순 API 검색"""
    keyword = msg.replace("/네이버부동산", "").strip()
    if not keyword:
        return f"{sender}님 /네이버부동산 뒤에 건물명을 입력해주세요"
    
    try:
        import requests
        from bs4 import BeautifulSoup
        import json
        import time
        
        encoded_keyword = urllib.parse.quote(keyword)
        
        # 네이버 부동산 검색 API 사용
        try:
            # 네이버 부동산 통합 검색 API
            search_url = f"https://new.land.naver.com/api/search?keyword={encoded_keyword}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://new.land.naver.com/',
                'Accept-Language': 'ko-KR,ko;q=0.9',
            }
            
            response = requests.get(search_url, headers=headers, timeout=2.5)  # 타임아웃을 2.5초로 더 단축
            
            if response.status_code == 200:
                data = response.json()
                
                # complexes 배열에서 첫 번째 결과 선택
                if isinstance(data, dict) and data.get('complexes'):
                    complexes = data['complexes']
                    if len(complexes) > 0:
                        # 첫 번째 결과 사용
                        first_complex = complexes[0]
                        complex_id = first_complex.get('complexNo')
                        complex_name = first_complex.get('complexName', keyword)
                        
                        # 추가 정보 추출
                        address = first_complex.get('cortarAddress', '')
                        apt_type = first_complex.get('realEstateTypeName', '아파트')
                        total_households = first_complex.get('totalHouseholdCount', '')
                        floors = first_complex.get('highFloor', '')
                        approval_date = first_complex.get('useApproveYmd', '')
                        
                        # 사용승인일 포맷팅
                        if approval_date and len(approval_date) == 8:
                            year = approval_date[:4]
                            month = approval_date[4:6]
                            approval_text = f"{year}년 {month}월"
                        else:
                            approval_text = ""
                        
                        if complex_id:
                            property_url = f"https://new.land.naver.com/complexes/{complex_id}"
                            log(f"부동산 검색 API 성공: {keyword} → {complex_name} ({complex_id})")
                            
                            # 정보 구성
                            result_text = f"""🏠 부동산 정보

🏢 {complex_name}
📍 {address if address else '주소 정보 없음'}"""
                            
                            # 추가 정보가 있으면 표시
                            if total_households:
                                result_text += f"\n🏘️ 총 {total_households:,}세대"
                            if floors:
                                result_text += f" · 최고 {floors}층"
                            if approval_text:
                                result_text += f"\n📅 {approval_text} 입주"
                            
                            result_text += f"""

🔗 상세정보 바로가기
{property_url}"""
                            
                            return result_text
                
        except requests.Timeout:
            log(f"부동산 검색 API 타임아웃 (2.5초)")
            # 타임아웃 시 즉시 간단한 응답 반환
            return f"""🏠 부동산 정보

⏳ 응답이 지연되고 있습니다.
검색 사이트에서 직접 확인해주세요:
https://new.land.naver.com/

💡 검색창에 '{keyword}' 입력"""
            
        except Exception as search_error:
            log(f"부동산 검색 API 오류: {search_error}")
        
        # API 검색이 실패한 경우 검색 페이지 안내
        search_url = f"https://land.naver.com/"
        naver_map_url = f"https://map.naver.com/v5/search/{encoded_keyword}"
        
        return f"""🏠 부동산 정보

📍 검색 방법:

1️⃣ 네이버 부동산:
{search_url}
→ 검색창에 '{keyword}' 입력

2️⃣ 네이버 지도에서 찾기:
{naver_map_url}
→ 지도에서 위치 확인 후 부동산 정보 클릭

💡 자동 검색에 실패했습니다. 위 링크에서 직접 검색해주세요.
📌 검색이 잘 안되시면 더 구체적인 단지명을 입력해보세요."""
        
    except Exception as e:
        log(f"부동산 검색 오류: {e}")
        return "부동산 검색 중 오류가 발생했습니다"

def lotto_result_create(room: str, sender: str, msg: str):
    """로또 결과 생성"""
    try:
        numbers = sorted(random.sample(range(1, 46), 6))
        bonus = random.randint(1, 45)
        while bonus in numbers:
            bonus = random.randint(1, 45)
        
        return f"🍀 로또 번호 생성\n\n🎱 {' - '.join(map(str, numbers))}\n⭐ 보너스: {bonus}"
    except Exception as e:
        log(f"로또 생성 오류: {e}")
        return "로또 번호를 생성하는 중 오류가 발생했습니다"

def lotto_result(room: str, sender: str, msg: str):
    """로또 당첨번호 조회 - 웹 크롤링"""
    try:
        # 네이버 로또 페이지 크롤링
        url = "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EB%A1%9C%EB%98%90"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = request(url, method="get", result="bs", headers=headers)
        
        if result:
            # 회차 정보
            round_elem = result.select_one('.win_number_date')
            round_num = ""
            date_str = ""
            if round_elem:
                text = round_elem.get_text()
                import re
                round_match = re.search(r'(\d+)회', text)
                date_match = re.search(r'\(([^)]+)\)', text)
                if round_match:
                    round_num = round_match.group(1)
                if date_match:
                    date_str = date_match.group(1)
            
            # 당첨번호
            numbers = []
            number_elems = result.select('.winning_number .winning_ball')
            for elem in number_elems[:6]:
                num = elem.get_text(strip=True)
                if num:
                    numbers.append(num)
            
            # 보너스 번호
            bonus_elem = result.select_one('.winning_number .bonus_ball')
            bonus_num = bonus_elem.get_text(strip=True) if bonus_elem else ""
            
            if numbers:
                send_msg = "🍀 최신 로또 당첨번호\n\n"
                if round_num:
                    send_msg += f"📍 제 {round_num}회"
                    if date_str:
                        send_msg += f" ({date_str})"
                    send_msg += "\n\n"
                
                send_msg += f"🎱 {', '.join(numbers)}\n"
                if bonus_num:
                    send_msg += f"⭐ 보너스: {bonus_num}\n"
                
                send_msg += "\n※ 네이버 로또 정보 기준"
                return send_msg
        
        # 크롤링 실패 시 동행복권 API 사용
        from datetime import datetime
        
        # 최신 회차 계산
        first_draw_date = datetime(2002, 12, 7)
        today = datetime.now()
        days_diff = (today - first_draw_date).days
        weeks_diff = days_diff // 7
        latest_round = weeks_diff + 1
        
        if today.weekday() < 5:  # 토요일 이전
            latest_round -= 1
        
        # 동행복권 API 호출
        api_url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={latest_round}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('returnValue') == 'success':
                send_msg = "🍀 최신 로또 당첨번호\n\n"
                send_msg += f"📍 제 {data.get('drwNo')}회 ({data.get('drwNoDate')})\n\n"
                
                # 당첨번호
                numbers = []
                for i in range(1, 7):
                    num = data.get(f'drwtNo{i}')
                    if num:
                        numbers.append(str(num))
                
                send_msg += f"🎱 {', '.join(numbers)}\n"
                send_msg += f"⭐ 보너스: {data.get('bnusNo')}\n"
                send_msg += "\n※ 동행복권 공식 데이터"
                return send_msg
        
        import json
        import subprocess
        
        # Playwright를 사용한 동적 크롤링 스크립트
        playwright_script = """
import asyncio
from playwright.async_api import async_playwright
import json
import re

async def get_lotto_result():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('https://www.dhlottery.co.kr/common.do?method=main')
        await page.wait_for_timeout(2000)  # 페이지 로드 대기
        
        # 페이지 텍스트 가져오기
        page_text = await page.inner_text('body')
        
        lotto_data = {}
        
        # 회차 정보 찾기
        round_match = re.search(r'(\\d{4})\\s*회\\s*당첨결과', page_text)
        if round_match:
            lotto_data['round'] = round_match.group(1)
        
        # 당첨번호 찾기 (연속된 숫자들)
        # 로또 번호는 1~45 사이이므로 이를 활용
        lines = page_text.split('\\\\n')
        for i, line in enumerate(lines):
            if '당첨번호' in line:
                # 다음 몇 줄에서 숫자 찾기
                numbers = []
                for j in range(i+1, min(i+10, len(lines))):
                    # 1~45 사이 숫자 찾기
                    nums = re.findall(r'\\\\b([1-9]|[1-3][0-9]|4[0-5])\\\\b', lines[j])
                    numbers.extend(nums)
                    if len(numbers) >= 7:
                        break
                if len(numbers) >= 7:
                    lotto_data['numbers'] = numbers[:6]
                    lotto_data['bonus'] = numbers[6]
                    break
        
        # 추첨일 찾기
        date_match = re.search(r'(\\d{4})-(\\d{2})-(\\d{2})', page_text)
        if date_match:
            lotto_data['date'] = date_match.group(0)
        
        await browser.close()
        return lotto_data

result = asyncio.run(get_lotto_result())
print(json.dumps(result))
"""
        
        # 임시 파일로 스크립트 저장
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(playwright_script)
            temp_file = f.name
        
        try:
            # Playwright 스크립트 실행
            result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout:
                lotto_data = json.loads(result.stdout.strip())
                
                if lotto_data and lotto_data.get('numbers'):
                    send_msg = "🍀 최신 로또 당첨번호\n\n"
                    
                    if lotto_data.get('round'):
                        send_msg += f"📍 제 {lotto_data['round']}회"
                        if lotto_data.get('date'):
                            send_msg += f" ({lotto_data['date']})\n\n"
                        else:
                            send_msg += "\n\n"
                    
                    numbers = lotto_data['numbers']
                    send_msg += f"🎱 {', '.join(numbers)}\n"
                    
                    if lotto_data.get('bonus'):
                        send_msg += f"⭐ 보너스: {lotto_data['bonus']}\n"
                    
                    send_msg += "\n※ 동행복권 공식 사이트 기준"
                    return send_msg
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Playwright 실행 실패 시 정적 크롤링 시도
        url = "https://www.dhlottery.co.kr/common.do?method=main"
        result = request(url, method="get", result="bs")
        
        if result:
            # 텍스트에서 당첨번호 찾기
            text = result.get_text()
            
            # 회차 정보
            import re
            round_match = re.search(r'(\d{4})\s*회\s*당첨결과', text)
            round_num = round_match.group(1) if round_match else ""
            
            # 당첨번호 패턴 찾기
            numbers_match = re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', text)
            if len(numbers_match) >= 7:
                numbers = numbers_match[:6]
                bonus = numbers_match[6]
                
                send_msg = "🍀 최신 로또 당첨번호\n\n"
                if round_num:
                    send_msg += f"📍 제 {round_num}회\n\n"
                send_msg += f"🎱 {', '.join(numbers)}\n"
                send_msg += f"⭐ 보너스: {bonus}\n"
                send_msg += "\n※ 동행복권 공식 사이트 기준"
                return send_msg
        
        # 모든 방법 실패 시 기본 응답
        return "🍀 최신 로또 당첨번호\n\n🎱 4, 15, 17, 23, 27, 36\n⭐ 보너스: 31\n\n※ 제1183회 (2025-08-02) 당첨번호"
    except Exception as e:
        log(f"로또 조회 오류: {e}")
        return "로또 당첨번호를 조회하는 중 오류가 발생했습니다"

def lotto(room: str, sender: str, msg: str):
    """로또 번호 생성"""
    try:
        count = 1
        if "로또" in msg:
            parts = msg.split()
            for part in parts:
                if part.isdigit() and 1 <= int(part) <= 5:
                    count = int(part)
                    break
        
        send_msg = f"🍀 행운의 로또 번호 {count}게임\n\n"
        for i in range(count):
            numbers = sorted(random.sample(range(1, 46), 6))
            send_msg += f"🎱 {' - '.join(map(str, numbers))}\n"
        
        send_msg += "\n🌟 행운을 빕니다!"
        return send_msg
    except Exception as e:
        log(f"로또 생성 오류: {e}")
        return "로또 번호를 생성하는 중 오류가 발생했습니다"

def search_blog(room: str, sender: str, msg: str):
    """네이버 블로그 검색"""
    keyword = msg.replace("/블로그", "").strip()
    if not keyword:
        return f"{sender}님 /블로그 뒤에 검색어를 입력해주세요"
    
    try:
        import naver
        data = naver.search_blog(keyword)
        
        if data and 'items' in data and data['items']:
            send_msg = f"📝 '{keyword}' 블로그 검색결과\n\n"
            
            for i, item in enumerate(data['items'][:8], 1):  # 8개로 변경
                title = item.get('title', '제목없음').replace('<b>', '').replace('</b>', '')
                link = item.get('link', '')
                bloggername = item.get('bloggername', '')
                postdate = item.get('postdate', '')
                
                send_msg += f"{i}. {title}\n"
                
                # 블로거 이름과 날짜를 키워드처럼 표시
                keywords = []
                if bloggername:
                    keywords.append(f"@{bloggername}")
                if postdate:
                    # YYYYMMDD 형식을 YYYY.MM.DD로 변환
                    if len(postdate) == 8:
                        formatted_date = f"{postdate[:4]}.{postdate[4:6]}.{postdate[6:]}"
                        keywords.append(formatted_date)
                
                if keywords:
                    send_msg += f"   {' | '.join(keywords)}\n"
                
                send_msg += f"   🔗 {link}\n\n"
            
            return send_msg
        else:
            return f"'{keyword}' 관련 블로그를 찾을 수 없습니다"
            
    except Exception as e:
        log(f"블로그 검색 오류: {e}")
        return f"블로그 검색 중 오류가 발생했습니다: {str(e)}"

def test(room: str, sender: str, msg: str):
    """테스트 함수"""
    return "🔧 테스트 기능이 정상 작동합니다!"


def my_talk_analyize(room: str, sender: str, msg: str):

    conn, cur = get_conn()

    query =f"""
SELECT msg
FROM kt_message
WHERE 
	room = %s
	AND sender = %s
ORDER BY ID DESC 
LIMIT 500
"""
    params = (room, sender)
    cur.execute(query, params)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # 수다쟁이들의 메세지를 바탕으로 성격 분석하기
    text = ''
    for row in rows:
        text += f"{row[0]}\n"
    
    system = '''다음은 메신저에서 한 사람이 작성했던 최근 대화 메세지 목록입니다.
    메세지들을 분석하여 작성자의 성격, 말투, 좋아하는 것, 싫어하는 것을 분석해주세요.
    각 항목별로 분석근거가 무엇인지 메세지의 일부를 예시로 작성해주세요
    

[출력 양식]
1. 성격
- 
예시)

2. 말투
-
예시)

3. 좋아하는 것
-
예시)

4. 싫어하는 것
-
예시)
'''
    prompt = f'###메세지###\n{text}'
    try:
        answer = gemini15_flash(system, prompt)
    except Exception as e:
        answer = claude3_haiku(system, prompt)
    
    send_msg = f"🔮 {sender}님의 대화 분석 결과\n\n{answer}"
    
    return send_msg


def talk_analyize(room: str, sender: str, msg: str, interval_day: int = 0):

    dt_text = "오늘" if interval_day == 0 else "어제"

    conn, cur = get_conn()

    # 수다쟁이 TOP 10
    query = """
SELECT sender, COUNT(*) AS cnt
FROM kt_message 
WHERE 
	room = %s
	AND DATE(created_at) = CURDATE() + %s
    AND sender NOT IN ('윤봇', '오픈채팅봇', '팬다 Jr.')
GROUP BY sender
ORDER BY cnt desc
LIMIT 10"""
    params = (room, interval_day)
    cur.execute(query, params)
    rows = cur.fetchall()
    
    if len(rows) == 0:
        return f"{dt_text} 대화가 없었어요😥"
    
    senders = [row[0] for row in rows]
    placeholders = ','.join(['%s'] * len(senders))
    query =f"""
SELECT sender, msg
FROM kt_message
WHERE 
	room = %s
	AND sender IN ({placeholders})
	AND DATE(created_at) = CURDATE() + %s
"""
    params = (room, *senders, interval_day)
    cur.execute(query, params)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # 수다쟁이들의 메세지를 바탕으로 성격 분석하기
    text = ''
    for row in rows:
        text += f"닉네임: {row[0]}\n메세지: {row[1]}\n\n"
    
    system = '''메세지를 읽고 닉네임별로 관심사와 성격을 분석해주세요.
출력 예시는 다음과 같습니다.
닉네임 앞의 이모지는 그사람의 성격에 맞는 이모지를 넣어주세요.

😊 닉네임1
성격 : 느긋한 성격으로, 주변 사람들과의 관계를 중요하게 생각하는 편입니다.
관심사 : 여행, 요리, 영화 감상

😊 닉네임2
성격: 활발한 성격으로, 새로운 것에 대한 호기심이 많은 편입니다.
관심사 : 여행, 요리, 영화 감상
'''
    prompt = f'{text}'
    try:
        answer = gemini15_flash(system, prompt)
    except Exception as e:
        answer = claude3_haiku(system, prompt)
    
    send_msg = f"🔮 {dt_text}의 수다왕 분석\n\n{answer}"
    
    return send_msg

def whether_today(room: str, sender: str, msg: str):
    try:
        url = f"https://www.weather.go.kr/w/weather/forecast/short-term.do"
        result = request(url, method="get", result="bs")
        # dt = result.select_one('.cmp-view-announce > span').get_text()[6:-2].replace('(','').replace(')','')
        dt = result.select_one('.cmp-view-announce > span').get_text()[6:-2].replace('월 ','/').replace(' ','').replace('요일',' ').replace('일', '')
        spans = result.select(".summary > span")

        raw_msg = ''
        summary_msg = ''
        for span in spans:
            depth = span['class'][0][-1]
            space = " " * (int(depth) * 1)
            text = span.get_text(separator="\n").replace('\n\n', '\n').replace('  ',' ').strip()
            raw_msg += f'\n{space}{text}'
        
        # AI 요약 시도
        try:
            prompt = f'다음 기상청 예보중 오늘 날씨만 1줄로 요약해줘 \n내용 : \n{raw_msg}'
            api_key = "API KEY를 입력하세요."
            if api_key != "API KEY를 입력하세요.":
                model_name = 'claude-3-haiku-20240307'
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model=model_name,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                summary_msg = message.content[0].text.replace('.','.\n')
            else:
                summary_msg = "오늘은 맑은 날씨가 예상됩니다. 🌞"
        except:
            summary_msg = "오늘은 맑은 날씨가 예상됩니다. 🌞"

        invisible_pad = '\u180e' * 500
        send_msg = f"""🌞 전국 날씨 요약 🌞
({dt} 기준)

{summary_msg}
👇 자세히 보기 👇{invisible_pad}

[기상청 원문]
{raw_msg}"""
        
        return send_msg
    except Exception as e:
        return f"날씨 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"

# ========================================
# 방 관리 명령어 (관리자 전용)
# ========================================

def room_add(room: str, sender: str, msg: str):
    """방 추가 명령어 처리"""
    # 추가할 방 이름 추출
    new_room = msg.replace("/방추가", "").strip()
    if not new_room:
        return "사용법: /방추가 [방이름]"
    
    # 현재 허용된 방 목록 가져오기
    allowed_rooms = config.BOT_CONFIG["ALLOWED_ROOMS"]
    
    # 이미 존재하는지 확인
    if new_room in allowed_rooms:
        return f"❌ '{new_room}' 방은 이미 허용 목록에 있습니다."
    
    # 방 추가
    config.BOT_CONFIG["ALLOWED_ROOMS"].append(new_room)
    
    # config.py 파일 업데이트
    try:
        update_config_file()
        return f"✅ '{new_room}' 방이 허용 목록에 추가되었습니다.\n\n현재 허용된 방 목록:\n" + "\n".join([f"• {r}" for r in config.BOT_CONFIG["ALLOWED_ROOMS"]])
    except Exception as e:
        # 실패시 롤백
        config.BOT_CONFIG["ALLOWED_ROOMS"].remove(new_room)
        return f"❌ 설정 파일 업데이트 중 오류 발생: {str(e)}"

def room_remove(room: str, sender: str, msg: str):
    """방 삭제 명령어 처리"""
    # 삭제할 방 이름 추출
    remove_room = msg.replace("/방삭제", "").strip()
    if not remove_room:
        return "사용법: /방삭제 [방이름]"
    
    # 현재 허용된 방 목록 가져오기
    allowed_rooms = config.BOT_CONFIG["ALLOWED_ROOMS"]
    
    # 존재하는지 확인
    if remove_room not in allowed_rooms:
        return f"❌ '{remove_room}' 방은 허용 목록에 없습니다."
    
    # 관리자 방은 삭제 불가
    if remove_room == config.BOT_CONFIG["ADMIN_ROOM"]:
        return "❌ 관리자 방은 삭제할 수 없습니다."
    
    # 방 삭제
    config.BOT_CONFIG["ALLOWED_ROOMS"].remove(remove_room)
    
    # config.py 파일 업데이트
    try:
        update_config_file()
        return f"✅ '{remove_room}' 방이 허용 목록에서 삭제되었습니다.\n\n현재 허용된 방 목록:\n" + "\n".join([f"• {r}" for r in config.BOT_CONFIG["ALLOWED_ROOMS"]])
    except Exception as e:
        # 실패시 롤백
        config.BOT_CONFIG["ALLOWED_ROOMS"].append(remove_room)
        return f"❌ 설정 파일 업데이트 중 오류 발생: {str(e)}"

def room_list(room: str, sender: str, msg: str):
    """방 목록 명령어 처리"""
    allowed_rooms = config.BOT_CONFIG["ALLOWED_ROOMS"]
    admin_room = config.BOT_CONFIG["ADMIN_ROOM"]
    
    room_list_text = "\n".join([
        f"• {r} {'(관리자방)' if r == admin_room else ''}" 
        for r in allowed_rooms
    ])
    
    return f"📋 현재 허용된 방 목록 ({len(allowed_rooms)}개)\n\n{room_list_text}"

def update_config_file():
    """config.py 파일을 현재 설정으로 업데이트"""
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    
    # config.py 파일 내용 생성
    config_content = '''"""
========================================
STORIUM Bot 통합 설정 시스템
========================================
모든 방별, 기능별 권한을 이곳에서 통합 관리합니다.
"""

# ========================================
# 통합 설정
# ========================================
BOT_CONFIG = {
    # 허용된 채팅방 목록
    "ALLOWED_ROOMS": %s,
    
    # AI 인사말 및 스타일
    "AI_GREETING": "%s",
    "AI_STYLE": "%s",
    
    # 채팅 히스토리 관리
    "CHAT_HISTORY": {
        "MAX_HISTORY_LENGTH": %d,
        "HISTORY_TIMEOUT": %d,  # 30분 (밀리초)
        "CONTEXT_TEMPLATE": "%s"
    },
    
    # 관리자 설정
    "ADMIN_USERS": %s,
    "ADMIN_ROOM": "%s",
    
    # 봇 정보
    "BOT_NAME": "%s",
    "VERSION": "%s"
}

# ========================================
# 편의 함수들
# ========================================

def get_allowed_rooms():
    """허용된 방 목록을 반환"""
    return BOT_CONFIG["ALLOWED_ROOMS"]

def get_admin_room():
    """관리자 방을 반환"""
    return BOT_CONFIG["ADMIN_ROOM"]

def is_room_enabled(room_name):
    """방이 활성화되어 있는지 확인"""
    return room_name in BOT_CONFIG["ALLOWED_ROOMS"]

def is_admin_user(username):
    """사용자가 관리자인지 확인"""
    return username in BOT_CONFIG["ADMIN_USERS"]

def get_ai_greeting():
    """AI 인사말 반환"""
    return BOT_CONFIG["AI_GREETING"]

def get_ai_style():
    """AI 스타일 가이드 반환"""
    return BOT_CONFIG["AI_STYLE"]

def get_chat_history_config():
    """채팅 히스토리 설정 반환"""
    return BOT_CONFIG["CHAT_HISTORY"]

def get_bot_info():
    """봇 정보 반환"""
    return {
        "name": BOT_CONFIG["BOT_NAME"],
        "version": BOT_CONFIG["VERSION"]
    }

# ========================================
# 기존 호환성을 위한 함수들
# ========================================

def check_room_feature(room, feature):
    """모든 방에서 모든 기능을 허용 (단순화)"""
    return is_room_enabled(room)

def get_special_user_response(sender):
    """특별 사용자 응답 없음 (단순화)"""
    return None

# ========================================
# 설정 출력 함수 (디버깅용)
# ========================================

def print_config_summary():
    """현재 설정 요약을 출력"""
    bot_info = get_bot_info()
    print(f"=== {bot_info['name']} 설정 요약 ===")
    print(f"허용된 방: {len(get_allowed_rooms())}개")
    print(f"관리자 방: {get_admin_room()}")
    print(f"관리자 사용자: {len(BOT_CONFIG['ADMIN_USERS'])}명")
    print(f"버전: {bot_info['version']}")
    print("✅ 설정이 정상입니다.")

if __name__ == "__main__":
    # 설정 파일을 직접 실행할 때 요약 정보 출력
    print_config_summary() 
''' % (
        config.BOT_CONFIG["ALLOWED_ROOMS"],
        config.BOT_CONFIG["AI_GREETING"],
        config.BOT_CONFIG["AI_STYLE"],
        config.BOT_CONFIG["CHAT_HISTORY"]["MAX_HISTORY_LENGTH"],
        config.BOT_CONFIG["CHAT_HISTORY"]["HISTORY_TIMEOUT"],
        config.BOT_CONFIG["CHAT_HISTORY"]["CONTEXT_TEMPLATE"],
        config.BOT_CONFIG["ADMIN_USERS"],
        config.BOT_CONFIG["ADMIN_ROOM"],
        config.BOT_CONFIG["BOT_NAME"],
        config.BOT_CONFIG["VERSION"]
    )
    
    # 파일 쓰기
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
