#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 서비스 모듈
각종 AI API 호출을 통합 관리
"""

import os
import json
from typing import Optional, List, Dict, Any
from utils.api_manager import APIManager
from utils.debug_logger import debug_logger
from utils.text_utils import log, clean_for_kakao
from services.http_service import request, fetch_json


class AIService:
    """
    통합 AI 서비스 클래스
    여러 AI 모델에 대한 통합 인터페이스 제공
    """
    
    def __init__(self):
        self.api_manager = APIManager
        self.chat_history = {}  # 방별 대화 히스토리
        self.max_history = 10  # 최대 히스토리 개수
    
    def get_ai_response(
        self, 
        prompt: str,
        model: str = "gemini",
        room: str = None,
        sender: str = None,
        use_history: bool = False
    ) -> str:
        """
        AI 응답 생성 (통합 인터페이스)
        
        Args:
            prompt: 질문/프롬프트
            model: AI 모델 선택 (gemini/gpt/claude/perplexity)
            room: 채팅방 ID
            sender: 발신자
            use_history: 대화 히스토리 사용 여부
        
        Returns:
            str: AI 응답
        """
        try:
            # 히스토리 컨텍스트 생성
            context = ""
            if use_history and room:
                context = self._get_chat_context(room, sender)
            
            # 모델별 처리
            if model == "gemini":
                return self.gemini_chat(prompt, context)
            elif model == "gpt":
                return self.gpt_chat(prompt, context)
            elif model == "claude":
                return self.claude_chat(prompt, context)
            elif model == "perplexity":
                return self.perplexity_chat(prompt)
            else:
                return "지원하지 않는 AI 모델입니다."
                
        except Exception as e:
            debug_logger.error(f"AI 응답 생성 오류 ({model}): {e}")
            return "AI 응답을 생성하는 중 오류가 발생했습니다."
    
    def gemini_chat(self, prompt: str, context: str = "") -> str:
        """Google Gemini API 호출"""
        try:
            api_key = self.api_manager.get_gemini_key()
            if not api_key:
                return "Gemini API 키가 설정되지 않았습니다."
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
            
            # 컨텍스트 포함 프롬프트 생성
            full_prompt = f"{context}\n{prompt}" if context else prompt
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.9,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                    "stopSequences": []
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            }
            
            result = fetch_json(url, method="post", json_data=payload)
            
            if result and 'candidates' in result:
                response = result['candidates'][0]['content']['parts'][0]['text']
                return clean_for_kakao(response)
            
            return "Gemini 응답을 받을 수 없습니다."
            
        except Exception as e:
            debug_logger.error(f"Gemini API 오류: {e}")
            return "Gemini API 호출 중 오류가 발생했습니다."
    
    def gpt_chat(self, prompt: str, context: str = "") -> str:
        """OpenAI GPT API 호출"""
        try:
            api_key = self.api_manager.get_openai_key()
            if not api_key:
                return "OpenAI API 키가 설정되지 않았습니다."
            
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            result = fetch_json(url, method="post", headers=headers, json_data=payload)
            
            if result and 'choices' in result:
                response = result['choices'][0]['message']['content']
                return clean_for_kakao(response)
            
            return "GPT 응답을 받을 수 없습니다."
            
        except Exception as e:
            debug_logger.error(f"GPT API 오류: {e}")
            return "GPT API 호출 중 오류가 발생했습니다."
    
    def claude_chat(self, prompt: str, context: str = "") -> str:
        """Anthropic Claude API 호출"""
        try:
            api_key = self.api_manager.get_anthropic_key()
            if not api_key:
                return "Claude API 키가 설정되지 않았습니다."
            
            url = "https://api.anthropic.com/v1/messages"
            
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            # 컨텍스트 포함 프롬프트
            full_prompt = f"{context}\n{prompt}" if context else prompt
            
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": full_prompt}
                ]
            }
            
            result = fetch_json(url, method="post", headers=headers, json_data=payload)
            
            if result and 'content' in result:
                response = result['content'][0]['text']
                return clean_for_kakao(response)
            
            return "Claude 응답을 받을 수 없습니다."
            
        except Exception as e:
            debug_logger.error(f"Claude API 오류: {e}")
            return "Claude API 호출 중 오류가 발생했습니다."
    
    def perplexity_chat(self, prompt: str) -> str:
        """Perplexity API 호출 (실시간 검색 포함)"""
        try:
            api_key = self.api_manager.get_perplexity_key()
            if not api_key:
                return "Perplexity API 키가 설정되지 않았습니다."
            
            url = "https://api.perplexity.ai/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides accurate and up-to-date information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            
            result = fetch_json(url, method="post", headers=headers, json_data=payload)
            
            if result and 'choices' in result:
                response = result['choices'][0]['message']['content']
                return clean_for_kakao(response)
            
            return "Perplexity 응답을 받을 수 없습니다."
            
        except Exception as e:
            debug_logger.error(f"Perplexity API 오류: {e}")
            return "Perplexity API 호출 중 오류가 발생했습니다."
    
    def _get_chat_context(self, room: str, sender: str) -> str:
        """대화 컨텍스트 생성"""
        key = f"{room}_{sender}"
        if key not in self.chat_history:
            self.chat_history[key] = []
        
        history = self.chat_history[key][-self.max_history:]
        
        if history:
            context = "이전 대화 내용:\n"
            for h in history:
                context += f"Q: {h['question']}\nA: {h['answer']}\n"
            return context
        
        return ""
    
    def save_chat_history(self, room: str, sender: str, question: str, answer: str):
        """대화 히스토리 저장"""
        key = f"{room}_{sender}"
        if key not in self.chat_history:
            self.chat_history[key] = []
        
        self.chat_history[key].append({
            "question": question,
            "answer": answer
        })
        
        # 최대 개수 유지
        if len(self.chat_history[key]) > self.max_history:
            self.chat_history[key] = self.chat_history[key][-self.max_history:]
    
    def clear_chat_history(self, room: str = None, sender: str = None):
        """대화 히스토리 초기화"""
        if room and sender:
            key = f"{room}_{sender}"
            if key in self.chat_history:
                del self.chat_history[key]
        elif room:
            # 방의 모든 히스토리 삭제
            keys_to_delete = [k for k in self.chat_history if k.startswith(f"{room}_")]
            for key in keys_to_delete:
                del self.chat_history[key]
        else:
            # 전체 히스토리 초기화
            self.chat_history.clear()


# 싱글톤 인스턴스
ai_service = AIService()