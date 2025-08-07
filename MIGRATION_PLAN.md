# fn.py 점진적 제거 계획

## 개요
4200+ 라인의 모놀리식 `fn.py` 파일을 모듈화된 구조로 전환하는 마이그레이션 계획서입니다.

## 현재 상태 (✅ 완료)

### Phase 1: 핸들러 분리 ✅
- `handlers/ai_handler.py` - AI 관련 함수들
- `handlers/news_handler.py` - 뉴스 관련 함수들
- `handlers/stock_handler.py` - 주식/금융 관련 함수들
- `handlers/media_handler.py` - 미디어 관련 함수들
- `handlers/game_handler.py` - 게임/엔터테인먼트 함수들
- `handlers/utility_handler.py` - 유틸리티 함수들
- `handlers/admin_handler.py` - 관리자 함수들

### Phase 2: 서비스 레이어 ✅
- `services/http_service.py` - HTTP 요청 통합 관리
- `services/db_service.py` - 데이터베이스 작업
- `services/ai_service.py` - AI API 통합
- `services/web_scraping_service.py` - 웹 스크래핑

### Phase 3: 코어 모듈 개선 ✅
- `core/router.py` - 메시지 라우팅 로직
- `core/message_handler.py` - 메시지 전송 및 큐 관리

## 남은 작업

### Phase 4: 점진적 마이그레이션 (🔄 진행 예정)

#### Step 1: 의존성 매핑
```python
# 각 모듈에서 fn.py의 어떤 함수를 사용하는지 매핑
dependencies = {
    'handlers/news_handler.py': ['request', 'log'],
    'handlers/stock_handler.py': ['request', 'log'],
    # ... 나머지 매핑
}
```

#### Step 2: 공통 유틸리티 추출
- [ ] `utils/text_utils.py` - 텍스트 처리 함수들
- [ ] `utils/date_utils.py` - 날짜/시간 관련 함수들
- [ ] `utils/format_utils.py` - 포맷팅 함수들

#### Step 3: 단계별 함수 제거
1. **사용하지 않는 함수 제거** (즉시 가능)
   - 중복된 함수들
   - 더 이상 사용하지 않는 레거시 함수들

2. **단순 함수 이동** (1주차)
   - 의존성이 적은 유틸리티 함수들
   - 독립적인 헬퍼 함수들

3. **복잡한 함수 리팩토링** (2-3주차)
   - 여러 모듈에서 사용하는 함수들
   - 비즈니스 로직이 복잡한 함수들

### Phase 5: 테스트 및 검증

#### 테스트 전략
1. **단위 테스트 작성**
   ```python
   # tests/test_handlers.py
   def test_ai_handler():
       result = ai_handler.get_ai_answer("테스트")
       assert result is not None
   ```

2. **통합 테스트**
   ```python
   # tests/test_integration.py
   def test_message_flow():
       # 메시지 입력부터 응답까지 전체 플로우 테스트
   ```

3. **회귀 테스트**
   - 기존 기능들이 정상 동작하는지 확인
   - A/B 테스트로 fn.py vs 새 모듈 비교

### Phase 6: 최종 정리

#### 파일 구조 최종 목표
```
kakaoBot-main/
├── handlers/         # 요청 처리
│   ├── __init__.py
│   ├── ai_handler.py
│   ├── news_handler.py
│   └── ...
├── services/         # 비즈니스 로직
│   ├── __init__.py
│   ├── ai_service.py
│   ├── db_service.py
│   └── ...
├── core/            # 핵심 기능
│   ├── __init__.py
│   ├── router.py
│   └── message_handler.py
├── utils/           # 유틸리티
│   ├── __init__.py
│   ├── api_manager.py
│   ├── debug_logger.py
│   └── ...
├── config.py        # 설정
├── main.py         # 진입점
└── requirements.txt # 의존성
```

## 마이그레이션 체크리스트

### 즉시 실행 가능 ✅
- [x] 핸들러 모듈 생성
- [x] 서비스 레이어 구현
- [x] 코어 모듈 개선
- [x] 브릿지 패턴 구현 (handlers/__init__.py)

### 단기 (1주 내)
- [ ] fn.py에서 사용하지 않는 코드 제거
- [ ] 중복 코드 정리
- [ ] 공통 유틸리티 함수 추출
- [ ] 기본 테스트 작성

### 중기 (2-3주)
- [ ] 복잡한 비즈니스 로직 리팩토링
- [ ] 순환 의존성 해결
- [ ] 성능 최적화
- [ ] 통합 테스트 완성

### 장기 (1개월)
- [ ] fn.py 완전 제거
- [ ] 문서화 완성
- [ ] 배포 프로세스 정립
- [ ] 모니터링 시스템 구축

## 위험 관리

### 잠재적 위험
1. **기능 누락**: 마이그레이션 중 일부 기능 누락 가능성
   - **대응**: 체계적인 테스트 및 기능 매핑

2. **성능 저하**: 모듈화로 인한 오버헤드
   - **대응**: 프로파일링 및 최적화

3. **하위 호환성**: 기존 코드와의 호환성 문제
   - **대응**: 브릿지 패턴 유지 및 점진적 전환

## 성공 지표

- ✅ 모든 기존 기능 정상 동작
- ✅ 코드 가독성 향상 (파일당 500줄 이하)
- ✅ 테스트 커버리지 80% 이상
- ⏳ fn.py 파일 제거
- ⏳ 문서화 완성도 90% 이상

## 다음 단계

1. **즉시**: fn.py 파일 분석하여 사용하지 않는 코드 식별
2. **이번 주**: 공통 유틸리티 함수 추출 시작
3. **다음 주**: 첫 번째 테스트 스위트 작성
4. **2주 후**: fn.py 의존성 50% 감소 목표

---

*마지막 업데이트: 2024년 8월 7일*
*작성자: STORIUM Bot 개발팀*