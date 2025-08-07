# 카카오톡 챗봇 프로젝트 구조

## 📁 프로젝트 구조

```
kakaoBot-main/
│
├── 📄 main.py                    # 메인 서버 실행 파일
├── 📄 command_manager.py         # 명령어 관리 시스템
├── 📄 config.py                  # 설정 및 환경 변수
├── 📄 debug_logger.py            # 디버깅 로거
│
├── 📂 API 모듈/
│   ├── 📄 fn.py                  # 모든 명령어 구현 (영화, 날씨, 주식 등)
│   ├── 📄 naver.py              # 네이버 API 통합
│   ├── 📄 coupang.py            # 쿠팡 검색 (우선순위 시스템)
│   ├── 📄 coupang_partners_api.py # 쿠팡 파트너스 공식 API
│   └── 📄 coupang_playwright.py # Playwright 기반 스크래핑
│
├── 📂 scripts/                   # 유틸리티 스크립트
│   ├── 📄 start_server.bat      # 서버 시작 (Windows)
│   ├── 📄 start_server.ps1      # 서버 시작 (PowerShell)
│   ├── 📄 test_all_commands.py  # 전체 명령어 테스트
│   └── 📂 ngrok_files/          # ngrok 관련 스크립트
│
├── 📂 docs/                      # 문서화
│   └── 📄 API_DOCUMENTATION.md  # API 문서
│
├── 📄 메신저r.js                # 카카오톡 연동 스크립트
├── 📄 README.md                  # 프로젝트 설명서
├── 📄 requirements.txt           # Python 패키지 의존성
└── 📄 .gitignore                # Git 제외 파일

```

## 🚀 주요 기능

### 구현된 명령어
- **!영화순위** - 실시간 박스오피스 (KOBIS API)
- **!날씨 [지역]** - 실시간 날씨 정보 (기상청 API)
- **!쿠팡 [상품]** - 쿠팡 상품 검색 (파트너스 API)
- **!유튜브인기** - 인기 동영상 (YouTube API)
- **!주식 [종목]** - 주식 시세 (ScrapingBee)
- **!칼로리 [음식]** - 칼로리 정보 (식품안전나라)
- **!운세 [띠]** - 오늘의 운세
- **!도움말** - 명령어 목록

### 기술 스택
- **Backend**: Python 3.x, Flask
- **APIs**: KOBIS, 기상청, YouTube, 쿠팡 파트너스
- **스크래핑**: BeautifulSoup, Playwright, ScrapingBee
- **통신**: ngrok (로컬 터널링)

## 📝 설정 방법

1. **환경 변수 설정** (config.py)
   - 각 API 키 설정 필요
   - ScrapingBee API 키
   - YouTube API 키
   - 쿠팡 파트너스 API 키

2. **서버 실행**
   ```bash
   python main.py
   # 또는
   ./scripts/start_server.bat
   ```

3. **ngrok 터널링**
   ```bash
   ngrok http 8002
   ```

## 🔧 유지보수

- 모든 테스트 파일은 삭제됨
- 로그 폴더는 자동 생성됨 (gitignore 처리)
- 캐시 파일은 자동 정리됨