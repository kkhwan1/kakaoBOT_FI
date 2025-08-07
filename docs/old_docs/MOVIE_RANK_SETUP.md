# 영화 순위 기능 설정 가이드

## 문제 해결 방법

### 1. 서버에서 영화 순위가 작동하지 않을 때

#### 방법 1: Playwright 설치 (권장)
```bash
# Playwright 설치
pip install playwright

# 브라우저 설치 (중요!)
python -m playwright install chromium

# 또는 모든 브라우저 설치
python -m playwright install
```

#### 방법 2: Selenium 설치 (대안)
```bash
# Selenium 설치
pip install selenium

# ChromeDriver 설치 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install chromium-driver

# 또는 수동 설치
# 1. https://chromedriver.chromium.org/ 에서 다운로드
# 2. PATH에 추가
```

### 2. 디버그 방법

서버에서 다음 스크립트를 실행하여 문제를 파악하세요:

```bash
python debug_movie_rank.py
```

### 3. 서버 환경별 설정

#### Linux 서버 (Ubuntu/Debian)
```bash
# 필수 패키지 설치
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    libgbm-dev \
    libgtk-3-0

# Playwright 설치
pip install playwright
python -m playwright install chromium
python -m playwright install-deps  # 시스템 의존성 자동 설치
```

#### Windows 서버
```powershell
# Playwright 설치
pip install playwright
python -m playwright install chromium
```

### 4. 권한 문제 해결

서버에서 권한 문제가 발생하면:

```bash
# Playwright 캐시 디렉토리 권한 설정
chmod -R 755 ~/.cache/ms-playwright/

# Selenium용 Chrome 권한 설정
chmod +x /usr/bin/chromedriver
```

### 5. 메모리 부족 문제

서버 메모리가 부족한 경우:

1. `fn.py`에서 Playwright/Selenium 부분을 비활성화
2. 직접 스크래핑 방법만 사용

```python
# fn.py의 movie_rank 함수에서
# Playwright와 Selenium 부분을 주석 처리하고
# 네이버 영화 스크래핑만 사용
```

### 6. 테스트 명령어

```bash
# 각 방법별 테스트
python test_movie_methods.py

# 실제 함수 테스트
python -c "from fn import movie_rank; print(movie_rank('test', 'user', '/영화순위'))"
```

## 현재 동작 순서

`movie_rank` 함수는 다음 순서로 데이터를 가져옵니다:

1. **Playwright** (KOBIS 실시간)
2. **Selenium** (KOBIS 실시간) 
3. **KOBIS API** (직접 호출)
4. **직접 스크래핑** (KOBIS/네이버)
5. **네이버 영화** (정적 스크래핑)
6. **CGV** (정적 스크래핑)
7. **실패 메시지**

## 로그 확인

서버 로그에서 다음 패턴을 확인하세요:

```
[영화순위] Playwright 시도 중...
[영화순위] Playwright 성공/실패
[영화순위] Selenium 시도 중...
[영화순위] Selenium 성공/실패
```

## 자주 발생하는 오류

### 1. "Executable doesn't exist"
```bash
# Playwright 브라우저 재설치
python -m playwright install --force chromium
```

### 2. "Chrome not reachable"
```bash
# Chrome 프로세스 확인
ps aux | grep chrome
# 남은 프로세스 종료
pkill chrome
```

### 3. "Permission denied"
```bash
# 실행 권한 부여
chmod +x movie_rank_*.py
```

## 문의

문제가 지속되면 서버 로그와 함께 다음 정보를 제공해주세요:
- OS 종류 및 버전
- Python 버전
- 설치된 패키지 목록 (`pip list`)
- `debug_movie_rank.py` 실행 결과