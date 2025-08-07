#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 핸들러 모듈
AI 관련 명령어 처리 (GPT, Gemini, Claude, Perplexity)
"""

import requests
import traceback
import google.generativeai as genai
from datetime import datetime
from utils.api_manager import APIManager
from utils.text_utils import clean_for_kakao
from chat_history_manager import chat_history


def get_ai_answer(room, sender, msg):
    """AI 질문 처리 함수 - Gemini로 통합 (히스토리 기능 포함)"""
    import random
    
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
        print(f"[AI] 에러 상세: {traceback.format_exc()}")
        return "일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요."


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
        
        # 프롬프트 구성
        if needs_search and use_search:
            # 검색이 필요한 경우 명시적으로 요청
            full_prompt = f"""
{system}

먼저 Google Search를 통해 최신 정보를 검색한 후 답변해주세요.
특히 다음 정보가 필요합니다:
- 실시간 정보 (날씨, 뉴스, 주가 등)
- 최신 데이터와 통계
- 정확한 사실 확인

질문: {question}

답변할 때:
1. 검색된 최신 정보를 바탕으로 답변
2. 구체적인 수치나 데이터 포함
3. 신뢰할 수 있는 정보만 제공
4. 불확실한 경우 명시
"""
        else:
            full_prompt = f"{system}\n\n{question}"
        
        # AI 응답 생성
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            return response.text.strip()
        
        # 응답이 없으면 재시도
        if retry_count < 2:
            print(f"Gemini 재시도 {retry_count + 1}/2")
            APIManager.rotate_gemini_key()  # 다음 키로 회전
            return gemini15_flash(system, question, retry_count + 1, use_search)
        
        return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"Gemini API 오류: {error_msg}")
        
        # API 키 문제인 경우 자동 회전 후 재시도
        if "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg:
            if retry_count < 3:
                print(f"Gemini API 키 오류, 다음 키로 재시도 {retry_count + 1}/3")
                APIManager.rotate_gemini_key()  # 다음 키로 강제 회전
                return gemini15_flash(system, question, retry_count + 1, use_search)
        
        # quota 에러시 검색 없이 재시도
        if "quota" in error_msg.lower() and use_search and retry_count == 0:
            print("Google Search quota 초과, 검색 없이 재시도")
            return gemini15_flash(system, question, retry_count + 1, False)
        
        # 다른 키로 재시도
        if retry_count < 2:
            APIManager.rotate_gemini_key()
            return gemini15_flash(system, question, retry_count + 1, use_search)
        
        return None


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
            # 3. 마크다운 제거
            content = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', content)  # **bold** 또는 *italic*
            content = re.sub(r'`([^`]+)`', r'\1', content)  # `code`
            # 4. 연속된 공백만 제거 (줄바꿈은 보존!)
            lines = content.split('\n')
            lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in lines if line.strip()]
            content = '\n'.join(lines)
            # 5. 앞뒤 공백 제거
            content = content.strip()
            
            # 6. 마침표 추가 (없으면)
            if content and not content[-1] in '.!?':
                content += '.'
            
            print(f"정제된 Perplexity 응답: {content}")
            return content
        
        return None
    
    except requests.exceptions.Timeout:
        print(f"Perplexity API 타임아웃 (5초)")
        return None
    except Exception as e:
        print(f"Perplexity API 오류: {e}")
        return None


def claude3_haiku(system, question):
    """Claude 3 Haiku API 호출 (비활성화 상태)"""
    # 현재 사용하지 않음
    return None


def gpt4o_mini(system, question):
    """GPT-4o Mini API 호출 (비활성화 상태)"""
    # 현재 사용하지 않음
    return None


def get_ai_greeting():
    """AI 인사말 생성"""
    greetings = [
        "안녕하세요! 무엇을 도와드릴까요? 😊",
        "반갑습니다! 어떤 도움이 필요하신가요? 🌟",
        "안녕하세요~ 오늘은 어떤 일로 찾아주셨나요? 💫",
        "환영합니다! 무엇이든 물어보세요! 🎯"
    ]
    import random
    return random.choice(greetings)


def get_ai_style():
    """AI 스타일 설정"""
    return {
        "temperature": 0.7,
        "max_tokens": 1000,
        "style": "friendly",
        "language": "ko"
    }