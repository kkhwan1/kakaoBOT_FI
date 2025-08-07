#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
개선된 메인 서버 - 안정성과 타임아웃 처리 강화
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import Response
import uvicorn
import traceback
import json
import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import functools
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG로 변경하여 더 자세한 로그 확인
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="KakaoBot API (Improved)",
    version="2.0",
    description="안정성이 개선된 카카오톡 봇 API"
)

# 스레드 풀 (브라우저 작업용)
executor = ThreadPoolExecutor(max_workers=3)

# 설정
import config
import command_manager
from error_monitor import error_monitor

# 새로운 모듈 구조 사용
try:
    from core.router import get_reply_msg
    logger.info("✅ 새로운 모듈 구조 (core.router) 사용")
except ImportError:
    logger.warning("⚠️ core.router를 찾을 수 없음, fn.py에서 import")
    from fn import get_reply_msg

# 응답 캐시 (중복 요청 방지)
response_cache = {}

# 캐시 통계 추가
cache_stats = {
    'hits': 0,
    'misses': 0,
    'total_requests': 0,
    'hit_rate': 0.0
}

# 캐시 타임아웃 설정 (초 단위)
CACHE_TIMEOUTS = {
    # 자주 변하지 않는 데이터 - 장시간 캐시
    '/영화순위': 86400,      # 24시간 (하루 1회 업데이트)
    '/로또결과': 86400,      # 24시간 (주 1회 추첨)
    '/명언': 3600,           # 1시간
    '/명령어': 3600,         # 1시간
    '/도움말': 3600,         # 1시간
    '/가이드': 3600,         # 1시간
    
    # 중간 빈도 업데이트 - 중간 캐시
    '/환율': 300,            # 5분
    '/금값': 300,            # 5분
    '/코인': 180,            # 3분
    '/상한가': 300,          # 5분
    '/하한가': 300,          # 5분
    '/인급동': 1800,         # 30분
    
    # 실시간 데이터 - 짧은 캐시
    '/주식': 60,             # 1분
    '/날씨': 600,            # 10분
    '/실시간검색어': 600,    # 10분
    '/실시간뉴스': 300,      # 5분
    
    # AI 및 동적 응답 - 캐시 안함
    '?': 0,                  # AI 대화는 캐시 안함
    
    # 기본값
    'default': 30            # 30초
}

# 캐시 크기 제한 (메모리 관리)
MAX_CACHE_SIZE = 100  # 최대 100개 항목만 캐시

# 명령어별 에러 메시지
ERROR_MESSAGES = {
    '/영화순위': '🎬 영화 정보를 가져오는 중 지연이 발생했습니다.\n잠시 후 다시 시도해주세요.',
    '/전적': '🎮 LOL 전적 조회가 지연되고 있습니다.\nOP.GG 서버 상태를 확인중입니다.',
    '/주식': '📈 주식 시장 데이터 조회가 지연되고 있습니다.\n장 마감 시간일 수 있습니다.',
    '/블로그': '📝 블로그 검색이 지연되고 있습니다.\n검색어를 단순화해보세요.',
    '/네이버부동산': '🏠 부동산 정보 조회가 지연되고 있습니다.\n단지명을 정확히 입력해주세요.',
    '/실시간검색어': '🔍 실시간 검색어 조회가 지연되고 있습니다.',
    '/인급동': '📺 유튜브 인기 동영상 조회가 지연되고 있습니다.',
    '?': '🤖 AI 응답 생성이 지연되고 있습니다.\n질문을 단순화해보세요.',
    'default': '⏱️ 응답 시간이 초과되었습니다.\n잠시 후 다시 시도해주세요.'
}

# API 타임아웃 설정 (초 단위)
API_TIMEOUTS = {
    # Selenium 사용 명령어 - 긴 타임아웃
    '/영화순위': 15.0,          # 영화진흥위원회 API + 크롤링
    '/전적': 10.0,              # LOL 전적 조회 (복잡한 크롤링)
    '/블로그': 8.0,             # 네이버 블로그 검색
    '/네이버부동산': 10.0,       # 부동산 정보 크롤링
    
    # 중간 복잡도 - 중간 타임아웃
    '/실시간검색어': 6.0,        # 네이버 실시간 검색어
    '/실시간뉴스': 6.0,         # 네이버 뉴스 크롤링
    '/인급동': 8.0,             # 유튜브 API 호출
    '/상한가': 6.0,             # 주식 상한가 조회
    '/하한가': 6.0,             # 주식 하한가 조회
    '/금값': 5.0,               # 금 시세 조회
    '/코인': 5.0,               # 코인 시세 조회
    
    # 빠른 응답 - 짧은 타임아웃
    '/주식': 4.0,               # 단일 종목 조회
    '/환율': 3.0,               # 환율 정보
    '/날씨': 4.0,               # 날씨 API
    '/운세': 3.0,               # 운세 정보
    '/로또': 2.0,               # 로또 번호 생성
    '/명령어': 1.0,             # 로컬 명령어 목록
    '/도움말': 1.0,             # 로컬 도움말
    '/안녕': 1.0,               # 간단한 인사
    
    # AI 대화 - 비활성화 상태
    '?': 8.0,                   # AI 대화 (현재 비활성화)
    
    # 기본값
    'default': 4.0              # 기본 타임아웃
}

# ========================================
# 캐시 관리 함수들 (중복 제거)
# ========================================

def get_command_cache_timeout(msg: str) -> int:
    """명령어별 캐시 타임아웃 결정 (중복 제거)"""
    for cmd, timeout in CACHE_TIMEOUTS.items():
        if msg.startswith(cmd):
            return timeout
    return CACHE_TIMEOUTS.get('default', 30)

def get_command_api_timeout(msg: str) -> float:
    """명령어별 API 타임아웃 결정"""
    for cmd, timeout in API_TIMEOUTS.items():
        if msg.startswith(cmd):
            return timeout
    return API_TIMEOUTS.get('default', 4.0)

def update_cache_stats(is_hit: bool):
    """캐시 통계 업데이트"""
    cache_stats['total_requests'] += 1
    if is_hit:
        cache_stats['hits'] += 1
    else:
        cache_stats['misses'] += 1
    
    if cache_stats['total_requests'] > 0:
        cache_stats['hit_rate'] = cache_stats['hits'] / cache_stats['total_requests']

def get_timeout_message(msg: str, timeout: float) -> str:
    """명령어별 타임아웃 메시지 생성"""
    for cmd, error_msg in ERROR_MESSAGES.items():
        if msg.startswith(cmd):
            return f"{error_msg}\n\n(제한시간: {timeout}초)"
    return ERROR_MESSAGES['default'] + f"\n\n(제한시간: {timeout}초)"

def save_to_cache(cache_key: str, data: str, timestamp: datetime.datetime):
    """캐시 저장 및 크기 관리"""
    response_cache[cache_key] = (data, timestamp)
    
    # 캐시 크기 제한
    if len(response_cache) > MAX_CACHE_SIZE:
        # LRU(Least Recently Used) 방식으로 제거
        oldest_key = min(response_cache.keys(), 
                        key=lambda k: response_cache[k][1])
        del response_cache[oldest_key]
        logger.debug(f"캐시 크기 제한 - 가장 오래된 항목 제거: {oldest_key[:30]}")

def try_fallback_cache(room: str, sender: str, msg: str) -> str:
    """타임아웃 시 이전 캐시 데이터 활용"""
    # 유사한 캐시 키 검색
    for key in response_cache.keys():
        if f"{room}:{sender}:" in key and msg in key:
            old_data, old_time = response_cache[key]
            age_minutes = (datetime.datetime.now() - old_time).total_seconds() / 60
            logger.info(f"폴백 캐시 사용 ({age_minutes:.1f}분 전 데이터)")
            return f"⏱️ 최신 정보 조회 실패 ({age_minutes:.1f}분 전 데이터)\n\n{old_data}"
    return None

async def cleanup_expired_cache():
    """백그라운드 캐시 정리 작업"""
    while True:
        await asyncio.sleep(300)  # 5분마다 실행
        
        now = datetime.datetime.now()
        expired_keys = []
        
        for key, (_, cached_time) in response_cache.items():
            msg_part = key.split(':')[-1] if ':' in key else ''
            cache_timeout = get_command_cache_timeout(msg_part)
            
            if cache_timeout > 0 and (now - cached_time).total_seconds() > cache_timeout:
                expired_keys.append(key)
        
        for key in expired_keys:
            del response_cache[key]
        
        if expired_keys:
            logger.info(f"백그라운드 캐시 정리: {len(expired_keys)}개 항목 제거")

def clean_message_for_kakao(msg: str) -> str:
    """카카오톡 전송을 위한 메시지 정리"""
    if not msg:
        return ""
    
    # 1. 길이 제한 (카카오톡 제한)
    # 영화순위는 전체 표시
    # AI 응답은 1000자로 제한
    if "KOBIS" not in msg:  # 영화순위가 아닌 경우
        max_length = 1000
        if len(msg) > max_length:
            msg = msg[:max_length-3] + "..."  # 잘린 경우 ... 추가
    # 영화순위는 5000자까지 허용
    else:
        max_length = 5000
        if len(msg) > max_length:
            msg = msg[:max_length] + "..."
    
    # 2. 문제가 될 수 있는 특수문자 정리
    # 일부 이모지는 메신저 봇에서 문제 발생 가능
    replacements = {
        '🥇': '[1위]',
        '🥈': '[2위]', 
        '🥉': '[3위]',
        '4️⃣': '4.',
        '5️⃣': '5.',
        '6️⃣': '6.',
        '7️⃣': '7.',
        '8️⃣': '8.',
        '9️⃣': '9.',
        '🔟': '10.',
        '10️⃣': '10.',
        # 영화순위 관련 이모지 추가 제거
        '🍿': '',  # 팝콘 이모지 제거
        '📅': '',  # 달력 이모지 제거
        '📊': '',  # 차트 이모지 제거
        # 카카오톡 메신저 봇에서 문제 될 수 있는 특수문자
        '·': '-',  # 중점을 하이픈으로 변경
        '「': '"',  # 특수 따옴표 변경
        '」': '"',
        '『': '"',
        '』': '"',
    }
    
    for old, new in replacements.items():
        msg = msg.replace(old, new)
    
    # 3. 연속된 줄바꿈 정리
    while '\n\n\n' in msg:
        msg = msg.replace('\n\n\n', '\n\n')
    
    return msg.strip()

def get_cache_key(room: str, sender: str, msg: str) -> str:
    """캐시 키 생성"""
    return f"{room}:{sender}:{msg}"

async def get_reply_with_timeout(room: str, sender: str, msg: str, timeout: float = None):
    """타임아웃이 있는 응답 생성 (개선 버전)"""
    
    # 0. 권한 체크 (command_manager 사용)
    can_use, error_msg = command_manager.check_command_permission(msg, sender, room)
    if not can_use:
        return error_msg
    
    # 명령어 추출
    cmd = command_manager.find_command(msg)
    command_name = cmd.name if cmd else msg.split()[0] if msg else ""
    
    # 오류 모니터링 - 명령어 시작 기록
    start_time = error_monitor.log_command_start(command_name, room, sender)
    if start_time < 0:
        # 비활성화된 명령어
        return f"⚠️ {command_name} 명령어는 현재 비활성화되었습니다.\n오류가 자주 발생하여 일시적으로 차단되었습니다."
    
    # 명령어별 타임아웃 결정 (함수 사용)
    if timeout is None:
        timeout = get_command_api_timeout(msg)
        logger.debug(f"명령어 '{msg[:20]}' 타임아웃: {timeout}초")
    
    # 1. 캐시 확인 (중복 요청 방지)
    cache_key = get_cache_key(room, sender, msg)
    now = datetime.datetime.now()
    
    if cache_key in response_cache:
        cached_data, cached_time = response_cache[cache_key]
        cache_timeout = get_command_cache_timeout(msg)  # 함수 사용
        
        # 캐시 유효성 확인
        if cache_timeout > 0 and (now - cached_time).total_seconds() < cache_timeout:
            logger.info(f"캐시 히트: {cache_key[:30]} (TTL: {cache_timeout}초)")
            update_cache_stats(is_hit=True)  # 통계 업데이트
            return cached_data
        
        # 만료된 캐시 제거
        del response_cache[cache_key]
    
    update_cache_stats(is_hit=False)  # 캐시 미스
    
    # 2. 장시간 명령어 처리 (10초 이상)
    if timeout >= 10.0:
        try:
            logger.info(f"장시간 명령어 처리 시작: {msg}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor, 
                functools.partial(get_reply_msg, room, sender, msg)
            )
            
            logger.info(f"장시간 명령어 처리 완료: {result[:100] if result else 'None'}")
            
            # 캐시 저장
            cache_timeout = get_command_cache_timeout(msg)
            if cache_timeout > 0:
                save_to_cache(cache_key, result, now)
            
            # 오류 모니터링 - 성공 기록
            error_monitor.log_command_success(command_name, start_time)
            
            return result
            
        except Exception as e:
            logger.error(f"장시간 명령어 처리 오류: {e}")
            
            # 오류 모니터링 - 오류 기록
            should_disable = error_monitor.log_command_error(
                command_name, room, sender, str(e), start_time
            )
            
            if should_disable:
                return f"⚠️ {command_name} 명령어가 자동 비활성화되었습니다.\n오류율이 50%를 초과했습니다."
            
            return get_timeout_message(msg, timeout)
    
    # 3. 기본 처리 (타임아웃 적용)
    try:
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            executor,
            functools.partial(get_reply_msg, room, sender, msg)
        )
        
        result = await asyncio.wait_for(future, timeout=timeout)
        
        # 캐시 저장
        cache_timeout = get_command_cache_timeout(msg)
        if cache_timeout > 0:
            save_to_cache(cache_key, result, now)
        
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"타임아웃: {msg[:30]} ({timeout}초 초과)")
        
        # 이전 캐시 데이터 활용 시도
        fallback_result = try_fallback_cache(room, sender, msg)
        if fallback_result:
            return fallback_result
        
        # 사용자 친화적 에러 메시지
        return get_timeout_message(msg, timeout)
    
    except Exception as e:
        logger.error(f"응답 생성 오류: {e}")
        return "⚠️ 처리 중 오류가 발생했습니다."

@app.post("/api/kakaotalk")
async def handle_message(request: Request):
    """개선된 메시지 처리"""
    response_data = {'is_reply': False}
    room, sender, msg = None, None, None
    
    try:
        # 1. 요청 파싱
        body = await request.body()
        
        # 요청 헤더 로깅
        logger.debug(f"요청 헤더: {dict(request.headers)}")
        logger.debug(f"요청 메소드: {request.method}")
        logger.debug(f"Content-Type: {request.headers.get('content-type', 'None')}")
        logger.debug(f"Body 길이: {len(body)} bytes")
        
        # Form 데이터 처리 추가 (카카오톡 봇이 form-data로 보낼 수 있음)
        if request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
            try:
                form_data = await request.form()
                data = dict(form_data)
                logger.debug(f"Form 데이터로 파싱: {data}")
            except:
                data = {}
        else:
            # 인코딩 자동 감지
            try:
                body_text = body.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    body_text = body.decode('euc-kr')
                except UnicodeDecodeError:
                    body_text = body.decode('cp949')
            
            logger.debug(f"수신 원본: {body_text[:500] if body_text else 'Empty'}")
            
            # JSON 파싱 시도
            try:
                data = json.loads(body_text) if body_text else {}
            except json.JSONDecodeError:
                # JSON이 아닌 경우 쿼리스트링 파싱 시도
                try:
                    from urllib.parse import parse_qs
                    parsed = parse_qs(body_text)
                    data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
                    logger.debug(f"쿼리스트링으로 파싱: {data}")
                except:
                    data = {}
        
        logger.debug(f"최종 파싱된 데이터: {data}")
        
        room = data.get('room', '').strip()
        sender = data.get('sender', '').strip()
        msg = data.get('msg', '').strip()
        
        logger.info(f"추출된 필드 - room: [{room}], sender: [{sender}], msg: [{msg}]")
        
        # 네이버 부동산 명령어 체크
        if msg and msg.startswith("/네이버부동산"):
            logger.info(f"네이버 부동산 명령어 감지: {msg}")
        
        # 필수 필드 확인
        if not room:
            room = "이국환"  # 허용된 실제 방 이름으로 기본값 설정
            logger.warning(f"room 필드 누락 - 기본값 사용: {room}")
        if not sender:
            sender = "이국환"  # 기본 sender 설정
            logger.warning(f"sender 필드 누락 - 기본값 사용: {sender}")
        if not msg:
            # msg가 비어있으면 빈 응답 반환
            logger.warning(f"msg 필드 누락 - 빈 메시지")
            # JSON 응답 생성 (ASCII 이스케이프 사용)
            json_str = json.dumps(response_data, ensure_ascii=True)
            return Response(content=json_str, media_type="application/json; charset=utf-8")
        
        # 2. 권한 확인
        if not config.is_room_enabled(room):
            logger.warning(f"허용되지 않은 방: {room}")
            # JSON 응답 생성 (ASCII 이스케이프 사용)
            json_str = json.dumps(response_data, ensure_ascii=True)
            return Response(content=json_str, media_type="application/json; charset=utf-8")
        
        # 3. 타임아웃이 있는 응답 생성 (AI 기능 비활성화)
        # AI 기능 비활성화 - 모든 메시지는 일반 명령어 타임아웃 사용
        reply_msg = await get_reply_with_timeout(room, sender, msg, timeout=4.0)  # 일반 명령어는 4초
        
        # 4. 응답 정리 및 전송
        if reply_msg:
            # 메시지 정리
            reply_msg = clean_message_for_kakao(reply_msg)
            
            response_data = {
                'is_reply': True,
                'reply_room': room,
                'reply_msg': reply_msg
            }
            
            # 영화순위는 전체 로그 표시
            if '/영화순위' in msg:
                logger.info(f"[영화순위 전체 응답] 길이: {len(reply_msg)}")
                logger.info(f"[영화순위 내용]: {reply_msg}")
                logger.info(f"[영화순위 JSON 응답]: {json.dumps(response_data, ensure_ascii=True)}")
            else:
                # AI 응답 로그 비활성화 (AI 기능 비활성화됨)
                logger.info(f"응답 생성: {room} - {reply_msg[:50]}...")
        else:
            logger.info(f"응답 없음: {room}/{sender}/{msg[:30]}")
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
    except Exception as e:
        logger.error(f"처리 오류: {e}\n{traceback.format_exc()}")
        
        # 오류시 간단한 메시지
        response_data = {
            'is_reply': True,
            'reply_room': room or config.get_admin_room(),
            'reply_msg': "⚠️ 일시적인 오류가 발생했습니다."
        }
    
    # JSON 응답 생성 (ASCII 이스케이프 사용)
    json_str = json.dumps(response_data, ensure_ascii=True)
    return Response(content=json_str, media_type="application/json; charset=utf-8")

@app.get("/")
async def welcome():
    """서버 상태 확인"""
    return {
        "message": "카카오톡 봇 서버 (개선 버전)",
        "status": "online",
        "version": "2.0",
        "improvements": [
            "타임아웃 처리",
            "캐시 시스템",
            "메시지 정리",
            "안정성 강화"
        ],
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """향상된 상태 체크"""
    now = datetime.datetime.now()
    
    # 캐시 통계 계산
    cache_by_command = {}
    cache_ages = []
    
    for key, (_, cached_time) in response_cache.items():
        msg_part = key.split(':')[-1] if ':' in key else 'unknown'
        
        # 명령어 타입 추출
        cmd_type = 'unknown'
        for cmd in CACHE_TIMEOUTS.keys():
            if msg_part.startswith(cmd):
                cmd_type = cmd
                break
        
        cache_by_command[cmd_type] = cache_by_command.get(cmd_type, 0) + 1
        cache_ages.append((now - cached_time).total_seconds())
    
    # 평균 캐시 나이 계산
    avg_cache_age = sum(cache_ages) / len(cache_ages) if cache_ages else 0
    
    return {
        "status": "healthy",
        "cache": {
            "size": len(response_cache),
            "limit": MAX_CACHE_SIZE,
            "by_command": cache_by_command,
            "avg_age_seconds": round(avg_cache_age, 1),
            "stats": {
                "hits": cache_stats['hits'],
                "misses": cache_stats['misses'],
                "hit_rate": f"{cache_stats['hit_rate']*100:.1f}%" if cache_stats['hit_rate'] > 0 else "0.0%",
                "total_requests": cache_stats['total_requests']
            }
        },
        "performance": {
            "active_threads": executor._threads.__len__() if hasattr(executor, '_threads') else 0,
            "max_threads": executor._max_workers
        },
        "timestamp": now.isoformat()
    }

@app.get("/test")
async def test_endpoint():
    """카카오톡 봇 연결 테스트용 엔드포인트"""
    return {
        "status": "서버 정상 작동중",
        "message": "카카오톡 봇 API 서버가 정상적으로 실행중입니다.",
        "test_response": {
            "is_reply": True,
            "reply_room": "테스트",
            "reply_msg": "테스트 메시지입니다."
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/test")
async def test_post(request: Request):
    """POST 요청 테스트 (카카오톡 봇 디버깅용)"""
    body = await request.body()
    headers = dict(request.headers)
    
    # 다양한 파싱 시도
    parsed_data = None
    
    # JSON 파싱
    try:
        parsed_data = json.loads(body.decode('utf-8'))
        parse_type = "JSON"
    except:
        pass
    
    # Form 데이터 파싱
    if not parsed_data:
        try:
            from urllib.parse import parse_qs
            parsed = parse_qs(body.decode('utf-8'))
            parsed_data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
            parse_type = "Form/QueryString"
        except:
            parsed_data = {"raw": body.decode('utf-8', errors='ignore')}
            parse_type = "Raw"
    
    # 메시지에 따른 간단한 테스트 응답
    test_msg = parsed_data.get('msg', '')
    if test_msg == '/안녕':
        reply_message = "테스트: 안녕하세요!"
    elif test_msg == '/시간':
        reply_message = f"테스트 시간: {datetime.datetime.now().strftime('%H:%M:%S')}"
    else:
        reply_message = f"테스트 에코: {test_msg}"
    
    return {
        "received": {
            "headers": headers,
            "body_length": len(body),
            "parsed_type": parse_type,
            "parsed_data": parsed_data
        },
        "test_response": {
            "is_reply": True,
            "reply_room": parsed_data.get('room', '테스트'),
            "reply_msg": reply_message
        }
    }

# ========================================
# 차트 생성 엔드포인트
# ========================================
from fastapi.responses import Response
import sys
sys.path.append('.')  # 현재 디렉토리를 파이썬 경로에 추가

# 차트 데이터 임시 캐시 (5분간 유지)
chart_cache = {}
chart_cache_timeout = 300  # 5분

@app.get("/chart/exchange")
async def get_exchange_chart():
    """환율 차트 생성 및 반환"""
    try:
        from utils.chart_generator import create_exchange_chart, fig_to_bytes
        import fn
        import re
        import os
        import glob
        from datetime import datetime, timedelta
        
        # 최근 저장된 차트 확인 (1분 이내)
        current_time = datetime.now()
        charts_dir = 'charts'
        
        # 기존 차트 파일 확인
        if os.path.exists(charts_dir):
            exchange_files = glob.glob(os.path.join(charts_dir, 'exchange_*.png'))
            for file in exchange_files:
                # 파일 생성 시간 확인
                file_time = datetime.fromtimestamp(os.path.getmtime(file))
                if current_time - file_time < timedelta(minutes=1):
                    # 1분 이내 차트가 있으면 재사용
                    with open(file, 'rb') as f:
                        return Response(content=f.read(), 
                                      media_type="image/png",
                                      headers={
                                          "Cache-Control": "max-age=60",
                                          "ngrok-skip-browser-warning": "true"
                                      })
        
        # 환율 데이터 수집 (fn.py의 exchange 함수 활용)
        result = fn.exchange("chart", "system", "/환율")
        
        # 텍스트에서 환율 데이터 파싱
        exchange_data = {}
        
        # USD 파싱
        if 'USD' in result:
            usd_match = re.search(r'USD: ([\d,]+\.?\d*)원', result)
            if usd_match:
                exchange_data['USD'] = {'price': usd_match.group(1)}
        
        # EUR 파싱
        if 'EUR' in result:
            eur_match = re.search(r'EUR: ([\d,]+\.?\d*)원', result)
            if eur_match:
                exchange_data['EUR'] = {'price': eur_match.group(1)}
        
        # JPY 파싱
        if 'JPY' in result:
            jpy_match = re.search(r'JPY.*?: ([\d,]+\.?\d*)원', result)
            if jpy_match:
                exchange_data['JPY'] = {'price': jpy_match.group(1)}
        
        # CNY 파싱
        if 'CNY' in result:
            cny_match = re.search(r'CNY: ([\d,]+\.?\d*)원', result)
            if cny_match:
                exchange_data['CNY'] = {'price': cny_match.group(1)}
        
        # 차트 생성 및 파일 저장
        fig = create_exchange_chart(exchange_data)
        
        # 파일 저장 경로 설정
        timestamp = current_time.strftime('%Y%m%d_%H%M%S')
        save_path = f'charts/exchange_{timestamp}.png'
        
        # 이미지 생성 및 저장
        image_bytes = fig_to_bytes(fig, save_path)
        
        return Response(content=image_bytes, 
                       media_type="image/png",
                       headers={
                           "Cache-Control": "max-age=60",
                           "ngrok-skip-browser-warning": "true"
                       })
        
    except Exception as e:
        logger.error(f"환율 차트 생성 오류: {e}")
        # 오류 이미지 반환
        return Response(content=b"Error creating chart", 
                       media_type="text/plain",
                       status_code=500)

@app.get("/charts/{filename}")
async def get_saved_chart(filename: str):
    """저장된 차트 이미지 제공"""
    import os
    file_path = os.path.join('charts', filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return Response(
                content=f.read(),
                media_type="image/png",
                headers={
                    "Cache-Control": "max-age=3600",
                    "ngrok-skip-browser-warning": "true"
                }
            )
    else:
        return Response(
            content=b"Chart not found",
            status_code=404
        )

@app.get("/chart/stock/{stock_name}")
async def get_stock_chart(stock_name: str):
    """주식 차트 생성 및 반환"""
    try:
        from utils.chart_generator import create_stock_chart, fig_to_bytes
        import stock_improved
        import re
        import os
        import glob
        from datetime import datetime, timedelta
        
        # 최근 저장된 차트 확인 (1분 이내)
        current_time = datetime.now()
        charts_dir = 'charts'
        safe_name = stock_name.replace(' ', '_').replace('/', '_')
        
        # 기존 차트 파일 확인
        if os.path.exists(charts_dir):
            stock_files = glob.glob(os.path.join(charts_dir, f'stock_{safe_name}_*.png'))
            for file in stock_files:
                # 파일 생성 시간 확인
                file_time = datetime.fromtimestamp(os.path.getmtime(file))
                if current_time - file_time < timedelta(minutes=1):
                    # 1분 이내 차트가 있으면 재사용
                    with open(file, 'rb') as f:
                        return Response(content=f.read(), 
                                      media_type="image/png",
                                      headers={
                                          "Cache-Control": "max-age=60",
                                          "ngrok-skip-browser-warning": "true"
                                      })
        
        # 주식 데이터 수집
        result = stock_improved.stock_improved("chart", "system", f"/주식 {stock_name}")
        
        # 텍스트에서 주식 데이터 파싱
        stock_data = {
            'name': stock_name,
            'code': '000000'
        }
        
        # 현재가 파싱
        current_match = re.search(r'현재가: ([\d,]+)원', result)
        if current_match:
            stock_data['current'] = int(current_match.group(1).replace(',', ''))
        
        # 전일대비 파싱
        change_match = re.search(r'전일대비: ([▲▼─])\s*([\d,]+)', result)
        if change_match:
            stock_data['change'] = f"{change_match.group(1)}{change_match.group(2)}"
        
        # 변동률 파싱
        rate_match = re.search(r'\(([\+\-]?\d+\.?\d*%)\)', result)
        if rate_match:
            stock_data['rate'] = rate_match.group(1)
        
        # 시가, 고가, 저가 파싱
        open_match = re.search(r'시가: ([\d,]+)', result)
        if open_match:
            stock_data['open'] = int(open_match.group(1).replace(',', ''))
        
        high_match = re.search(r'고가: ([\d,]+)', result)
        if high_match:
            stock_data['high'] = int(high_match.group(1).replace(',', ''))
        
        low_match = re.search(r'저가: ([\d,]+)', result)
        if low_match:
            stock_data['low'] = int(low_match.group(1).replace(',', ''))
        
        # 거래량 파싱
        volume_match = re.search(r'거래량: ([\d,]+)', result)
        if volume_match:
            stock_data['volume'] = volume_match.group(1)
        
        # 종목 코드 파싱
        code_match = re.search(r'\((\d{6})\)', result)
        if code_match:
            stock_data['code'] = code_match.group(1)
        
        # 차트 생성 및 파일 저장
        fig = create_stock_chart(stock_data)
        
        # 파일 저장 경로 설정
        timestamp = current_time.strftime('%Y%m%d_%H%M%S')
        save_path = f'charts/stock_{safe_name}_{timestamp}.png'
        
        # 이미지 생성 및 저장
        image_bytes = fig_to_bytes(fig, save_path)
        
        return Response(content=image_bytes, 
                       media_type="image/png",
                       headers={
                           "Cache-Control": "max-age=60",
                           "ngrok-skip-browser-warning": "true"
                       })
        
    except Exception as e:
        logger.error(f"주식 차트 생성 오류: {e}")
        return Response(content=b"Error creating chart", 
                       media_type="text/plain",
                       status_code=500)

@app.on_event("startup")
async def startup_event():
    """서버 시작시 실행 (개선)"""
    logger.info("="*60)
    bot_info = config.get_bot_info()
    logger.info(f"{bot_info['name']} v{bot_info['version']} 서버 시작")
    logger.info("="*60)
    
    # 백그라운드 캐시 정리 작업 시작
    asyncio.create_task(cleanup_expired_cache())
    logger.info("✅ 백그라운드 캐시 정리 작업 시작 (5분 주기)")
    
    # 중요 명령어 사전 캐싱
    preload_commands = ['/영화순위', '/로또결과', '/명령어']
    
    for cmd in preload_commands:
        try:
            logger.info(f"사전 로딩 시작: {cmd}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(get_reply_msg, "이국환", "이국환", cmd)
            )
            if result:
                cache_key = get_cache_key("이국환", "이국환", cmd)
                response_cache[cache_key] = (result, datetime.datetime.now())
                cache_timeout = get_command_cache_timeout(cmd)
                logger.info(f"✅ {cmd} 사전 로딩 완료 (캐시: {cache_timeout}초)")
        except Exception as e:
            logger.error(f"❌ {cmd} 사전 로딩 실패: {e}")
    
    # 설정 정보 출력
    allowed_rooms = config.get_allowed_rooms()
    admin_room = config.get_admin_room()
    admin_users = config.BOT_CONFIG['ADMIN_USERS']
    
    logger.info(f"\n📋 설정 정보:")
    logger.info(f"  · 허용된 방 ({len(allowed_rooms)}개): {', '.join(allowed_rooms)}")
    logger.info(f"  · 관리자 방: {admin_room}")
    logger.info(f"  · 관리자 ({len(admin_users)}명): {', '.join(admin_users)}")
    
    logger.info(f"\n🚀 최적화 설정:")
    logger.info(f"  · 캐시 크기 제한: {MAX_CACHE_SIZE}개")
    logger.info(f"  · 백그라운드 정리: 5분 주기")
    logger.info(f"  · 캐시 히트율 추적: 활성화")
    logger.info(f"  · 사용자 친화적 에러: 활성화")
    logger.info(f"  · 명령어별 캐시 TTL: 0-86400초")
    logger.info(f"  · 명령어별 API 타임아웃: 1-15초")
    logger.info("="*60)

@app.on_event("shutdown") 
async def shutdown_event():
    """서버 종료시 실행"""
    executor.shutdown(wait=True)
    logger.info("서버 종료됨")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )