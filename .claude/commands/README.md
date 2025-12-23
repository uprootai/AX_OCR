# Custom Claude Code Commands

이 디렉토리에는 일반적인 작업을 위한 워크플로우 템플릿이 포함되어 있습니다.

## 📚 사용 가능한 Commands (5개)

### `/test-api`
개별 API 엔드포인트를 다양한 시나리오로 테스트합니다.

**주요 기능**:
- YOLO API 테스트
- eDOCr2 v2 API 테스트
- PaddleOCR API 테스트
- Gateway Speed/Hybrid Mode 테스트
- 응답 시간 및 결과 검증

**사용 예시**:
```
/test-api yolo
/test-api edocr2
/test-api gateway
```

---

### `/debug-issue`
체계적인 워크플로우로 일반적인 문제를 디버깅합니다.

**주요 기능**:
- 로그 확인 (Gateway, 개별 API)
- 일반적인 이슈 패턴 분석
- KNOWN_ISSUES.md에 문서화

**일반적인 이슈 패턴**:
- "바운딩박스 값이 안나와요"
- API 500 에러
- Container unhealthy
- Connection refused

---

### `/add-feature` (업그레이드됨)
모듈식 구조를 따라 API에 새 기능을 추가합니다.

**주요 기능**:
1. **Pre-Flight Checks**
   - 리스크 평가 (🟢Low ~ 🔴Critical)
   - Dry-Run 프리뷰

2. **Implementation Steps**
   - 서비스 모듈 생성
   - `__init__.py` 내보내기
   - API 스펙 생성
   - Response 모델 추가
   - Executor 생성 (BlueprintFlow용)

3. **Quality Gate Checks**
   - Import 검증
   - Docker 설정 검증
   - API Health Check

4. **Post-Implementation**
   - 문서 업데이트
   - Git 커밋

**사용 예시**:
```
/add-feature tesseract-ocr
```

---

### `/rebuild-service`
Docker 서비스를 안전하게 재빌드하고 재시작합니다.

**주요 기능**:
- 단일 서비스 재빌드
- 전체 서비스 재빌드
- Health 검증
- Docker 캐시 정리

**일반 서비스 목록**:
| 서비스 | 포트 |
|--------|------|
| gateway-api | 8000 |
| yolo-api | 5005 |
| edocr2-v2-api | 5002 |
| paddleocr-api | 5006 |
| skinmodel-api | 5003 |
| web-ui | 5173 |

**사용 예시**:
```
/rebuild-service gateway-api
/rebuild-service all
```

---

### `/track-issue` (업그레이드됨)
사용자가 보고한 이슈를 KNOWN_ISSUES.md에 추적합니다.

**주요 기능**:
1. **리스크 레벨 분류**
   | 레벨 | 아이콘 | 응답 시간 |
   |------|--------|----------|
   | Critical | 🔴 | 즉시 |
   | High | 🟠 | < 4시간 |
   | Medium | 🟡 | < 24시간 |
   | Low | 🟢 | 다음 스프린트 |

2. **이슈 템플릿**
   - "안된다" (It doesn't work) - 조사 시작
   - "잘된다" (It works) - 해결 완료

3. **카테고리별 템플릿**
   - API 연결 이슈
   - Frontend 빌드 실패
   - 워크플로우 실행 실패

4. **조사 워크플로우**
   - Quick Diagnosis 명령어
   - Investigation Log
   - Resolution 문서화

**사용 예시**:
```
/track-issue
```

---

## 🚀 빠른 사용

채팅에서 커맨드를 입력하면 됩니다:
```
/test-api
/debug-issue
/add-feature gateway-api
/rebuild-service yolo-api
/track-issue
```

Claude Code가 프롬프트를 확장하고 워크플로우를 안내합니다.

---

## 📋 Best Practices

### 1. 반복 작업에 커맨드 사용
```bash
# 매일 아침
/test-api gateway   # API 상태 확인
/debug-issue        # 이슈 확인
```

### 2. 템플릿 일관성 유지
- 모든 새 기능은 `/add-feature` 사용
- 이슈는 항상 `/track-issue`로 추적

### 3. 문서화 습관
- KNOWN_ISSUES.md 업데이트
- ROADMAP.md 진행 상황 업데이트
- Lessons Learned 기록

### 4. 리스크 인지
- 변경 전 리스크 레벨 확인
- 🟠High/🔴Critical은 신중하게
- Dry-run 먼저 실행

---

## 🔗 관련 Skills

Commands와 함께 Skills도 활용하세요:
- `/skill feature-implementer` - 단계별 기능 구현
- `/skill code-janitor` - 코드 품질 검사
- `/skill doc-updater` - 문서 자동 업데이트

---

**마지막 업데이트**: 2025-12-23
**버전**: 2.0.0
