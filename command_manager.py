"""
========================================
STORIUM Bot 통합 명령어 관리 시스템
========================================
모든 명령어를 중앙에서 관리하고 권한을 체크합니다.
"""

import config
from typing import Dict, List, Tuple, Optional

# ========================================
# 명령어 정의 (모든 명령어를 한 곳에 정리)
# ========================================
ALL_COMMANDS = [
    # === AI 응답 ===
    {
        "name": "?",
        "description": "AI가 답변해요",
        "usage": "?저녁메뉴 추천해줘",
        "category": "AI",
        "emoji": "🤖",
        "handler": "get_ai_answer",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    
    # === 기본 명령어 ===
    {
        "name": "/명령어",
        "description": "명령어 목록",
        "aliases": ["/가이드", "/도움말"],
        "category": "기본",
        "emoji": "📖",
        "handler": "show_commands",
        "status": "✅ 정상작동"
    },
    
    # === 검색 명령어 ===
    {
        "name": "/실시간검색어",
        "description": "실시간 검색어",
        "category": "검색",
        "emoji": "🔍",
        "handler": "real_keyword",
        "status": "✅ 정상작동"
    },
    {
        "name": "/뉴스",
        "description": "실시간 뉴스",
        "aliases": ["/실시간뉴스"],
        "category": "검색",
        "emoji": "📰",
        "handler": "real_news",
        "status": "✅ 정상작동"
    },
    {
        "name": "/블로그",
        "description": "네이버 블로그 검색",
        "usage": "/블로그 파이썬",
        "category": "검색",
        "emoji": "📝",
        "handler": "search_blog",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    
    # === 운세 ===
    {
        "name": "/운세",
        "description": "오늘의 운세",
        "usage": "/운세90",
        "category": "운세",
        "emoji": "🔮",
        "handler": "fortune",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/물병자리",
        "description": "별자리 운세 (12개 별자리)",
        "aliases": ["/물고기자리", "/양자리", "/황소자리", "/쌍둥이자리", 
                   "/게자리", "/사자자리", "/처녀자리", "/천칭자리", 
                   "/전갈자리", "/사수자리", "/궁수자리", "/염소자리"],
        "category": "운세",
        "emoji": "⭐",
        "handler": "zodiac",
        "status": "✅ 정상작동"
    },
    
    # === 날씨 ===
    {
        "name": "/날씨",
        "description": "지역 날씨",
        "usage": "/날씨 강남구",
        "category": "날씨",
        "emoji": "🌞",
        "handler": "whether",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    
    # === 정보 ===
    {
        "name": "/주식",
        "description": "주식 정보",
        "usage": "/주식 삼성전자",
        "category": "정보",
        "emoji": "📊",
        "handler": "stock",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/환율",
        "description": "실시간 환율",
        "category": "정보",
        "emoji": "💲",
        "handler": "exchange",
        "status": "✅ 정상작동"
    },
    {
        "name": "/코인",
        "description": "코인 시세 TOP 10",
        "category": "정보",
        "emoji": "🪙",
        "handler": "coin",
        "status": "✅ 정상작동"
    },
    {
        "name": "/금값",
        "description": "금 시세 정보",
        "category": "정보",
        "emoji": "💰",
        "handler": "gold",
        "status": "✅ 정상작동"
    },
    {
        "name": "/상한가",
        "description": "상한가 종목",
        "category": "정보",
        "emoji": "📈",
        "handler": "stock_upper",
        "status": "✅ 정상작동"
    },
    {
        "name": "/하한가",
        "description": "하한가 종목",
        "category": "정보",
        "emoji": "📉",
        "handler": "stock_lower",
        "status": "✅ 정상작동"
    },
    
    # === 엔터 ===
    {
        "name": "/로또",
        "description": "로또 번호 생성",
        "category": "엔터",
        "emoji": "🍀",
        "handler": "lotto",
        "status": "✅ 정상작동"
    },
    {
        "name": "/로또결과",
        "description": "로또 당첨번호",
        "category": "엔터",
        "emoji": "🎰",
        "handler": "lotto_result",
        "status": "✅ 정상작동"
    },
    {
        "name": "/인급동",
        "description": "유튜브 인기동영상",
        "category": "엔터",
        "emoji": "📺",
        "handler": "youtube_popular_all",
        "status": "✅ 정상작동"
    },
    
    # === 유틸 ===
    {
        "name": "/지도",
        "description": "네이버지도 검색",
        "usage": "/지도 강남 맛집",
        "aliases": ["/맵"],
        "category": "유틸",
        "emoji": "🗺️",
        "handler": "naver_map",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/네이버부동산",
        "description": "네이버 부동산 검색",
        "usage": "/네이버부동산 래미안",
        "category": "정보",
        "emoji": "🏠",
        "handler": "naver_land",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/칼로리",
        "description": "음식의 칼로리",
        "usage": "/칼로리 감자",
        "category": "유틸",
        "emoji": "🍲",
        "handler": "calorie",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    
    # === 스케줄 ===
    {
        "name": "/스케줄",
        "description": "스케줄 등록",
        "usage": "/스케줄 매일 09:00 /뉴스 → 이국환",
        "category": "스케줄",
        "emoji": "⏰",
        "handler": "schedule_add",
        "is_prefix": True,
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/스케줄목록",
        "description": "등록된 스케줄 조회",
        "category": "스케줄",
        "emoji": "📋",
        "handler": "schedule_list",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/스케줄삭제",
        "description": "스케줄 삭제",
        "usage": "/스케줄삭제 sch_xxx",
        "category": "스케줄",
        "emoji": "🗑️",
        "handler": "schedule_delete",
        "is_prefix": True,
        "admin_only": True,
        "status": "✅ 정상작동"
    },

    # === 관리자 ===
    {
        "name": "/방추가",
        "description": "방 추가",
        "usage": "/방추가 [방이름]",
        "category": "관리",
        "emoji": "➕",
        "handler": "room_add",
        "admin_only": True,
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/방삭제",
        "description": "방 삭제",
        "usage": "/방삭제 [방이름]",
        "category": "관리",
        "emoji": "➖",
        "handler": "room_remove",
        "admin_only": True,
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/방목록",
        "description": "방 목록 확인",
        "category": "관리",
        "emoji": "📋",
        "handler": "room_list",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/재부팅",
        "description": "기기 재부팅",
        "category": "관리",
        "emoji": "🔄",
        "handler": "reboot",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    
    # === 오류 모니터링 (관리자) ===
    {
        "name": "/오류로그",
        "description": "최근 오류 로그 조회",
        "usage": "/오류로그 [개수]",
        "category": "관리",
        "emoji": "📋",
        "handler": "error_logs",
        "admin_only": True,
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/오류통계",
        "description": "명령어별 오류 통계",
        "category": "관리",
        "emoji": "📊",
        "handler": "error_stats",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/사용통계",
        "description": "명령어 사용 통계",
        "category": "관리",
        "emoji": "📈",
        "handler": "usage_stats",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/명령어활성화",
        "description": "비활성화된 명령어 활성화",
        "usage": "/명령어활성화 [명령어]",
        "category": "관리",
        "emoji": "✅",
        "handler": "enable_command",
        "admin_only": True,
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/통계리셋",
        "description": "명령어 통계 초기화",
        "usage": "/통계리셋 [명령어]",
        "category": "관리",
        "emoji": "🔄",
        "handler": "reset_command_stats",
        "admin_only": True,
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/성능추천",
        "description": "성능 최적화 추천",
        "category": "관리",
        "emoji": "⚡",
        "handler": "performance_recommendations",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/캐시초기화",
        "description": "캐시 메모리 초기화",
        "category": "관리",
        "emoji": "🗑️",
        "handler": "clear_cache",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    {
        "name": "/캐시상태",
        "description": "캐시 상태 조회",
        "category": "관리",
        "emoji": "💾",
        "handler": "cache_status",
        "admin_only": True,
        "status": "✅ 정상작동"
    },
    
    # === 특수 ===
    {
        "name": "#",
        "description": "키워드 분석",
        "usage": "#해외여행지 추천",
        "category": "특수",
        "emoji": "🔑",
        "handler": "naver_keyword",
        "is_prefix": True,
        "status": "✅ 정상작동"
    },
    
    # === 추가 뉴스 ===
    {
        "name": "/경제뉴스",
        "description": "경제 뉴스",
        "category": "검색",
        "emoji": "💹",
        "handler": "economy_news",
        "status": "✅ 정상작동"
    },
    {
        "name": "/IT뉴스",
        "description": "IT 뉴스",
        "category": "검색",
        "emoji": "💻",
        "handler": "it_news",
        "status": "✅ 정상작동"
    },
]

class CommandInfo:
    """명령어 정보를 담는 클래스"""
    def __init__(self, data: dict):
        self.name = data.get("name")
        self.description = data.get("description")
        self.usage = data.get("usage", self.name)
        self.category = data.get("category", "기타")
        self.emoji = data.get("emoji", "🔸")
        self.handler = data.get("handler")
        self.aliases = data.get("aliases", [])
        self.admin_only = data.get("admin_only", False)
        self.is_prefix = data.get("is_prefix", False)
        self.status = data.get("status", "❓ 미확인")

class CommandManager:
    """명령어 관리자 클래스"""
    
    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.prefix_commands: List[CommandInfo] = []
        self._initialize_commands()
    
    def _initialize_commands(self):
        """모든 명령어 등록"""
        for cmd_data in ALL_COMMANDS:
            cmd = CommandInfo(cmd_data)
            
            # 메인 명령어 등록
            self.commands[cmd.name] = cmd
            
            # 별칭 등록
            for alias in cmd.aliases:
                self.commands[alias] = cmd
            
            # 접두사 명령어는 별도 리스트에도 추가
            if cmd.is_prefix:
                self.prefix_commands.append(cmd)
    
    def find_command(self, msg: str) -> Optional[CommandInfo]:
        """메시지에 해당하는 명령어 찾기"""
        # 1. 정확한 매칭 먼저 확인
        if msg in self.commands:
            return self.commands[msg]
        
        # 2. 접두사 기반 명령어 확인
        for cmd in self.prefix_commands:
            if msg.startswith(cmd.name):
                return cmd
        
        return None
    
    def get_handler_name(self, msg: str) -> Optional[str]:
        """메시지에 대한 핸들러 함수명 반환"""
        cmd = self.find_command(msg)
        return cmd.handler if cmd else None
    
    def check_permission(self, msg: str, user: str, room: str) -> Tuple[bool, str]:
        """명령어 사용 권한 확인"""
        cmd = self.find_command(msg)
        
        if not cmd:
            return True, ""  # 명령어가 아니면 통과
        
        # 관리자 명령어 체크
        if cmd.admin_only and not config.is_admin_user(user):
            return False, "⚠️ 관리자만 사용할 수 있는 명령어입니다."
        
        # 방 허용 체크
        if not config.is_room_enabled(room):
            return False, "이 방에서는 봇을 사용할 수 없습니다."
        
        return True, ""
    
    def get_command_list(self, is_admin: bool = False) -> str:
        """명령어 목록 생성 (상세 버전)"""
        message = "📌 **전체 명령어 목록** 📌\n\n"
        
        # 카테고리별로 정리
        categories = {}
        seen = set()  # 중복 제거를 위한 set
        
        for cmd_name, cmd in self.commands.items():
            # 중복 제거 (별칭은 한 번만)
            if cmd.name in seen:
                continue
            seen.add(cmd.name)
            
            # 관리자 명령어는 관리자만 볼 수 있음
            if cmd.admin_only and not is_admin:
                continue
            
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)
        
        # 카테고리 순서 (관리자는 관리 카테고리도 표시)
        order = ["AI", "기본", "검색", "운세", "날씨", "정보",
                "엔터", "유틸", "게임", "특수", "스케줄"]
        if is_admin:
            order.append("관리")
        
        for cat in order:
            if cat not in categories:
                continue
            
            message += f"【{cat}】\n"
            for cmd in categories[cat]:
                status_icon = "✅" if "✅" in cmd.status else "❌"
                # 별칭이 있는 경우 함께 표시
                if cmd.aliases:
                    alias_text = f" ({', '.join(cmd.aliases)})"
                else:
                    alias_text = ""
                message += f"{status_icon} {cmd.emoji} {cmd.name}{alias_text}: {cmd.description}\n"
                # 사용법이 있는 경우 표시
                if cmd.usage and cmd.usage != cmd.name:
                    message += f"   사용법: {cmd.usage}\n"
            message += "\n"
        
        # 통계 정보
        total_commands = len(seen)
        message += f"📊 총 {total_commands}개 명령어 지원\n"
        if not is_admin:
            message += "💡 관리자 명령어는 관리자만 볼 수 있습니다."
        
        return message
    
    def get_help_message(self, is_admin: bool = False) -> str:
        """도움말 메시지 생성 (간결한 버전)"""
        message = "✨ STORIUM Bot 가이드 ✨\n\n"
        
        # 주요 기능 하이라이트
        message += "🤖 ?를 앞에 붙이면 AI가 답변해요\n"
        message += "   예) ?오늘 서울 날씨 알려줘\n\n"
        
        # 주요 명령어만 간단히 표시
        # 날씨
        message += "🌞 /날씨 [지역명] : 현재 날씨 정보\n"
        
        # 증시/투자
        message += "📈 /주식 [종목명] : 개별 종목 정보\n"
        message += "💰 /금값 : 실시간 금 시세\n"
        message += "💲 /환율 : 실시간 환율 정보\n"
        message += "🪙 /코인 : 코인 시세 TOP 10\n"
        
        # 생활정보
        message += "🗺️ /지도 [장소명] : 네이버지도 검색\n"
        message += "🏠 /부동산 [단지명] : 부동산 정보\n"
        message += "🍲 /칼로리 [음식명] : 칼로리 정보\n"
        
        # 엔터테인먼트
        message += "🎰 /로또 : 행운의 로또 번호 생성\n"
        message += "🎰 /로또결과 : 최신 당첨번호 확인\n"
        message += "📺 /인급동 : 유튜브 인기 동영상\n"
        
        # 운세
        message += "🔮 /운세 [생년] : 오늘의 운세\n"
        message += "⭐ /[별자리] : 별자리 운세\n"
        
        # 검색
        message += "🔍 /실시간검색어 : 네이버 실시간 검색어\n"
        message += "📰 /뉴스, /경제뉴스, /IT뉴스 : 카테고리별 뉴스\n"
        message += "📝 /블로그 [검색어] : 블로그 검색\n"
        
        # 게임
        
        # 관리자 명령어 (관리자만 볼 수 있음)
        if is_admin:
            message += "\n【 관리자 전용 】\n"
            message += "➕ /방추가 [방이름] : 봇 사용 방 추가\n"
            message += "➖ /방삭제 [방이름] : 봇 사용 방 제거\n"
            message += "📋 /방목록 : 허용된 방 목록\n"
            message += "🔄 /재부팅 : 기기 재부팅\n"
        
        message += "\n💡 더 자세한 명령어는 /명령어목록 을 입력하세요!\n"
        message += "📱 카카오톡에서 편리하게 사용하세요!"
        
        return message
    
    def get_command_status_report(self) -> str:
        """명령어 상태 보고서"""
        total = len(ALL_COMMANDS)
        working = sum(1 for cmd in ALL_COMMANDS if "✅" in cmd.get("status", ""))
        
        report = "📊 **명령어 상태 보고서**\n\n"
        report += f"전체 명령어: {total}개\n"
        report += f"✅ 정상작동: {working}개 ({working/total*100:.1f}%)\n"
        report += f"❌ 미구현: {total-working}개 ({(total-working)/total*100:.1f}%)\n\n"
        
        # 카테고리별 상태
        report += "【카테고리별 상태】\n"
        cat_stats = {}
        for cmd in ALL_COMMANDS:
            cat = cmd.get("category", "기타")
            if cat not in cat_stats:
                cat_stats[cat] = {"total": 0, "working": 0}
            cat_stats[cat]["total"] += 1
            if "✅" in cmd.get("status", ""):
                cat_stats[cat]["working"] += 1
        
        for cat, stats in cat_stats.items():
            report += f"{cat}: {stats['working']}/{stats['total']}개 "
            report += f"({stats['working']/stats['total']*100:.0f}%)\n"
        
        return report

# 전역 CommandManager 인스턴스
command_manager = CommandManager()

def get_command_help(is_admin: bool = False) -> str:
    """명령어 도움말 반환"""
    return command_manager.get_help_message(is_admin)

def get_command_list(is_admin: bool = False) -> str:
    """명령어 목록 반환 (간략)"""
    return command_manager.get_command_list(is_admin)

def check_command_permission(msg: str, user: str, room: str) -> Tuple[bool, str]:
    """명령어 권한 체크"""
    return command_manager.check_permission(msg, user, room)

def get_handler_name(msg: str) -> Optional[str]:
    """핸들러 이름 반환"""
    return command_manager.get_handler_name(msg)

def find_command(msg: str) -> Optional[CommandInfo]:
    """명령어 찾기"""
    return command_manager.find_command(msg)