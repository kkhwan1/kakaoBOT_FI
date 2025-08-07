# 📂 프로젝트 구조 (2025.08.06 업데이트)

```
kakaoBot-main/
│
├── 📌 핵심 파일
│   ├── main_improved.py      # ✅ 메인 서버 (FastAPI)
│   ├── fn.py                 # 명령어 처리 함수
│   ├── config.py             # 중앙 설정 관리
│   └── command_manager.py    # 명령어 목록 관리
│
├── 📦 API 모듈
│   ├── naver.py             # 네이버 검색 API
│   └── stock_improved.py    # 주식 정보 API
│
├── 🎬 movie_modules/         # 영화 순위 모듈
│   ├── movie_rank_playwright.py  # Playwright 자동화
│   ├── movie_rank_selenium.py    # Selenium 자동화
│   └── movie_rank_direct.py      # 직접 API 호출
│
├── 🛠️ utils/                 # 유틸리티
│   ├── debug_logger.py      # 디버그 로거
│   ├── debug_movie_rank.py  # 영화 순위 디버그
│   └── install_playwright.py # Playwright 설치 도구
│
├── 🧪 test_files/            # 테스트 파일
│   ├── test_all_commands_now.py
│   ├── test_movie_api.py
│   └── test_movie_methods.py
│
├── 🚀 scripts/               # 실행 스크립트
│   ├── start_server.bat     # Windows 서버 시작
│   ├── start_server.ps1     # PowerShell 서버 시작
│   ├── start_ngrok.bat      # ngrok 터널 시작
│   ├── test_all_commands.py # 전체 명령어 테스트
│   └── ngrok_files/         # ngrok 관련 파일들
│       ├── NGROK_AUTH_GUIDE.md
│       ├── NGROK_실행_가이드.md
│       └── ...
│
├── 📚 docs/                  # 문서
│   ├── 📋_전체_명령어_목록.md
│   ├── 메신저R_점검사항.md
│   ├── 메신저R_테스트_가이드.md
│   ├── 명령어_검증_보고서.md
│   ├── 통합완료_보고서.md
│   ├── STATUS_REPORT.md
│   └── old_docs/            # 이전 버전 문서
│       ├── MOVIE_RANK_SETUP.md
│       ├── PROJECT_STRUCTURE.md
│       └── 메신저봇_설정가이드.md
│
├── 📊 debug_logs/            # 로그 파일 (자동 생성)
│   ├── debug_20250806.log
│   └── error_20250806.log
│
└── 📄 기타 파일
    ├── README.md            # 프로젝트 소개
    ├── README_봇사용법.md    # 봇 사용 가이드
    ├── requirements.txt     # Python 패키지 목록
    ├── 메신저r.js          # 카카오톡 봇 스크립트
    ├── start_server.bat    # 서버 실행 (루트)
    └── start_server.sh     # Linux/Mac 서버 실행

```

## 🚀 서버 실행 방법

### 방법 1: 직접 실행
```bash
python main_improved.py
```

### 방법 2: 배치 파일 사용 (Windows)
```bash
start_server.bat
# 또는 더블클릭
```

### 방법 3: Shell 스크립트 (Linux/Mac)
```bash
./start_server.sh
```

## ⚙️ 설정 변경

모든 설정은 `config.py`에서 중앙 관리:
```python
BOT_CONFIG = {
    "ALLOWED_ROOMS": [...],  # 허용된 방 목록
    "ADMIN_USERS": [...],    # 관리자 목록
    # ...
}
```
**서버 재시작하면 자동 적용!**

## ❌ 최근 제거된 기능

### 쿠팡 검색 (2025.08.06)
- **이유**: API 차단으로 작동 불가
- **삭제 파일**: 
  - coupang.py
  - coupang_partners_api.py  
  - coupang_playwright.py
- **코드 정리**: fn.py, command_manager.py에서 관련 코드 제거

### 이전 버전 파일
- **main.py**: main_improved.py로 대체
- **fn_optimized.py**: main_improved.py에 통합
- **setup_movie_rank.bat/sh**: 불필요하여 제거

## 📋 주요 기능

### ✅ 작동 중인 기능
- 날씨 정보
- 실시간 검색어
- 네이버 검색
- 주식 정보
- 환율 정보
- 암호화폐 시세
- 로또 번호
- 영화 순위 (KOBIS)
- AI 대화
- 유튜브 요약

### ⚠️ 제한적 작동
- 영화 순위: Selenium/Playwright 필요
- AI 기능: API 키 필요

## 🔧 개선 사항 (main_improved.py)

1. **타임아웃 처리**: 4초 자동 타임아웃
2. **응답 캐시**: 5초간 중복 요청 방지
3. **메시지 정리**: 1000자 제한, 이모지 변환
4. **안정성 강화**: 간헐적 실패 문제 해결

## 📝 유지보수 팁

- 로그 확인: `debug_logs/` 폴더
- 설정 변경: `config.py` 수정 후 서버 재시작
- 명령어 추가: `command_manager.py`와 `fn.py` 수정
- 테스트: `test_files/` 폴더의 스크립트 실행

---

*마지막 업데이트: 2025년 8월 6일*