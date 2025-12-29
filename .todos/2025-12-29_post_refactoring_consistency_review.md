# 리팩토링 후 일관성 검토 및 후속 작업 (2025-12-29)

> **목적**: 17개 API 리팩토링 완료 후 일관성 검토 및 누락된 작업 식별
> **작성일**: 2025-12-29
> **관련 커밋**: 17개 API 라우터 분리 + lifespan 패턴 적용

---

## 📊 리팩토링 완료 현황

### Staged 파일 (97개 new file)

| API | routers/ | services/ | schemas.py | 상태 |
|-----|----------|-----------|------------|------|
| design-checker-api | ✅ 3개 | ✅ 기존 | ✅ | 완료 |
| doctr-api | ✅ | ✅ 3개 | ✅ | 완료 |
| easyocr-api | ✅ | ✅ 3개 | ✅ | 완료 |
| edgnet-api | ✅ | ✅ 1개 | - | 완료 |
| edocr2-v2-api | ✅ | 기존 | 기존 | 완료 |
| esrgan-api | ✅ | ✅ 3개 | ✅ | 완료 |
| knowledge-api | ✅ 3개 | ✅ 1개 | 기존 | 완료 |
| line-detector-api | ✅ | ✅ 5개 | 기존 | 완료 |
| ocr-ensemble-api | ✅ | ✅ 3개 | ✅ | 완료 |
| paddleocr-api | ✅ | 기존 수정 | 기존 | 완료 |
| pid-analyzer-api | ✅ 4개 | ✅ 2개 | 기존 | 완료 |
| skinmodel-api | ✅ | 기존 | 기존 | 완료 |
| surya-ocr-api | ✅ | ✅ 3개 | ✅ | 완료 |
| tesseract-api | ✅ | ✅ 1개 | ✅ | 완료 |
| trocr-api | ✅ | ✅ 3개 | ✅ | 완료 |
| vl-api | ✅ | ✅ 2개 | ✅ | 완료 |
| yolo-api | ✅ 2개 | ✅ 2개 | 기존 | 완료 |

**코드 감소**: 9,219줄 제거 (api_server.py 총합)

---

## 🔍 일관성 검토 필요 항목

### 1. [P0] Modified 파일 스테이징 누락

**현재 상태**: 아래 파일들이 modified이지만 아직 스테이징되지 않음

```
Changes not staged for commit:
  - models/*/api_server.py (17개)
  - models/paddleocr-api/services/ocr.py
  - models/edgnet-api/services/__init__.py
  - models/knowledge-api/services/__init__.py
  - models/yolo-api/services/__init__.py
  - gateway-api/api_server.py
  - gateway-api/blueprintflow/executors/*.py
  - gateway-api/api_specs/*.yaml
  - web-ui/src/config/nodes/*.ts
  - docs/api/*.md
```

**작업**:
- [ ] 모든 modified 파일 검토 후 스테이징
- [ ] 커밋 준비

---

### 2. [P0] 한글→영어 주석 변환 일관성

리팩토링된 api_server.py들의 주석이 영어로 변환됨. 확인 필요:

| 파일 | 주석 언어 | 상태 |
|------|----------|------|
| doctr-api/api_server.py | 영어 | ✅ |
| easyocr-api/api_server.py | 영어 | ✅ |
| 기타 14개 | 확인 필요 | ⚠️ |

**확인 명령**:
```bash
grep -l "한글\|헬스\|시작\|종료" models/*/api_server.py
```

---

### 3. [P1] routers/__init__.py 패턴 일관성

**표준 패턴** (대부분 적용됨):
```python
"""
{API Name} API Routers
"""
from .{feature}_router import router as {feature}_router

__all__ = ['{feature}_router']
```

**확인 필요**: 모든 routers/__init__.py가 `__all__` 정의를 포함하는지

```bash
grep -L "__all__" models/*/routers/__init__.py
```

---

### 4. [P1] services/__init__.py 내보내기 패턴

두 가지 패턴이 혼재:

**패턴 A** (명시적 import):
```python
from .model import load_model, draw_overlay
from .state import get_model, set_model
```

**패턴 B** (함수만 노출):
```python
from .inference import YOLOInferenceService
```

**권장**: 패턴 A (명시적 함수 노출) 통일

---

### 5. [P1] schemas.py 누락 API 확인

일부 API는 schemas.py가 없고 기존 models/schemas.py 사용:

| API | schemas.py 위치 | 상태 |
|-----|----------------|------|
| edgnet-api | 없음 | ⚠️ 추가 검토 |
| edocr2-v2-api | models/schemas.py | ✅ 기존 |
| paddleocr-api | models/schemas.py | ✅ 기존 |
| skinmodel-api | models/schemas.py | ✅ 기존 |
| knowledge-api | 없음 | ⚠️ 추가 검토 |

**권장**: 필요시 루트에 schemas.py 생성

---

### 6. [P1] YOLO model_type 하위 호환성 확인

**변경 사항**:
- `pid_symbol` 옵션 UI에서 제거
- 백엔드에서 `pid_symbol` → `pid_class_aware` 자동 매핑 유지

**확인 위치**:
```python
# models/yolo-api/routers/detection_router.py:207
"pid_symbol": "pid_class_aware",  # 하위 호환성
```

**확인 사항**:
- [ ] 기존 워크플로우에서 `pid_symbol` 사용 시 정상 동작 확인
- [ ] API 스펙에 deprecated 표기 추가

---

### 7. [P2] Executor 입력 패턴 확장 완료 확인

**designchecker_executor.py**:
- [x] texts 입력 처리 추가 ✅
- [x] include_bwms 파라미터 추가 ✅

**pidanalyzer_executor.py**:
- [x] texts 입력 처리 추가 ✅
- [x] regions 입력 처리 추가 ✅
- [x] 출력에 texts, regions 패스스루 추가 ✅

---

### 8. [P2] 프론트엔드 노드 정의 변경 사항

**detectionNodes.ts**:
- [x] `pid_symbol` 제거 ✅
- [x] `pid_class_aware`, `pid_class_agnostic` 순서 변경 ✅
- [x] 설명 업데이트 ✅

**analysisNodes.ts**:
- [x] PID Analyzer 입력에 `texts` 추가 ✅
- [x] Design Checker `categories`에 `bwms` 추가 ✅
- [x] Design Checker `include_bwms` 파라미터 추가 ✅
- [x] recommendedInputs 업데이트 (pid_symbol → pid_class_aware) ✅

**segmentationNodes.ts**:
- [x] `min_region_area` 설명 업데이트 ✅

---

### 9. [P2] API 스펙 YAML 변경 사항

**yolo.yaml**:
- [x] model_type 옵션 순서 변경 ✅
- [x] modelTypes 상세 섹션 추가 ✅
- [x] pid_symbol 옵션 제거됨 ✅ (백엔드에서 하위 호환성 유지)

**design-checker.yaml**:
- [x] texts 입력 추가 ✅
- [x] categories에 bwms 옵션 추가 ✅
- [x] include_bwms 파라미터 추가 ✅

**pid-analyzer.yaml**:
- [x] 기본 inputs에는 texts/regions 없음 (의도적) ✅
- [x] additionalEndpoints에 /api/v1/region-text/extract 정의됨 (texts, regions 사용) ✅
- [x] executor에서 texts, regions 패스스루 지원 ✅
- **참고**: BlueprintFlow에서는 PaddleOCR → PID Analyzer 연결 시 executor가 자동 처리

---

### 10. [P2] 문서 업데이트

**새로 추가된 문서**:
- [x] docs/api/design-checker/endpoints.md ✅
- [x] docs/api/design-checker/bwms-rules.md ✅
- [x] docs/api/line-detector/endpoints.md ✅
- [x] docs/api/pid-analyzer/endpoints.md ✅

**업데이트 필요**:
- [ ] docs/api/README.md - 17 → 18 API 변경 확인
- [ ] docs/api/yolo/parameters.md - model_type 변경 반영
- [ ] CLAUDE.md - 버전 히스토리 업데이트

---

### 11. [P2] BlueprintFlow 샘플 추가

**새 샘플**:
```typescript
// web-ui/src/pages/blueprintflow/constants.ts
{
  id: 'sample-bwms',
  name: 'BWMS P&ID (SIGNAL 영역)',
  path: '/samples/bwms_pid_sample.png',
  recommended: true
}
```

**확인 필요**:
- [ ] `web-ui/public/samples/bwms_pid_sample.png` 파일 존재 확인
- [ ] 스테이징 여부 확인 (현재 untracked)

---

### 12. [P2] Dashboard APIDetail.tsx 변경

**변경 사항**:
```typescript
// model_type 옵션 변경
options: [
  { value: 'engineering', label: '기계도면 (14종)' },
  { value: 'bom_detector', label: '전력설비 (27종)' },  // 순서 변경
  { value: 'pid_class_aware', label: 'P&ID 분류 (32종)' },
  { value: 'pid_class_agnostic', label: 'P&ID 위치만' }
]
// pid_symbol 제거됨
```

---

### 13. [P3] 테스트 결과 파일 삭제

**삭제된 파일**:
```
test-results/pid-analysis-new/
test-results/pid-analysis/00-29-48_P_ID_Analysis_Pipeline/
test-results/pid-debug/
```

**작업**:
- [ ] test-results/.gitkeep 추가 (폴더 유지)
- [ ] .gitignore에 `test-results/**/*.json` 확인

---

### 14. [P3] Untracked 파일 처리

| 파일 | 처리 |
|------|------|
| .todos/*.md | 스테이징 |
| apply-company/techloss/test_output/ | .gitignore |
| web-ui/public/samples/bwms_pid_sample.png | 스테이징 |

---

## 📋 Docker 빌드 테스트 체크리스트

리팩토링 후 Docker 빌드가 정상 동작하는지 확인:

```bash
# 1. 전체 서비스 빌드 테스트
docker-compose build --no-cache yolo-api edocr2-v2-api paddleocr-api

# 2. 개별 API 시작 테스트
docker-compose up -d yolo-api
docker-compose logs yolo-api | tail -20

# 3. Health 체크
curl http://localhost:5005/health
```

**테스트 우선순위**:
1. [ ] yolo-api (가장 큰 변경)
2. [ ] pid-analyzer-api (신규 router 4개)
3. [ ] design-checker-api (신규 기능 다수)
4. [ ] line-detector-api (services 5개)
5. [ ] 기타 OCR API들

---

## 🎯 권장 커밋 순서

### 커밋 1: API 리팩토링 (구조 변경)
```bash
git add models/*/api_server.py
git add models/*/routers/
git add models/*/services/
git add models/*/schemas.py
git commit -m "refactor: 17개 API 라우터/서비스 분리 및 lifespan 패턴 적용

- api_server.py 9,219줄 제거 (평균 60-70% 감소)
- routers/, services/, schemas.py 분리
- @app.on_event() → lifespan 패턴 마이그레이션
- 한글 주석 → 영어 주석 통일"
```

### 커밋 2: Executor 및 프론트엔드 업데이트
```bash
git add gateway-api/blueprintflow/executors/
git add web-ui/src/config/nodes/
git add web-ui/src/pages/blueprintflow/constants.ts
git add web-ui/src/pages/admin/APIDetail.tsx
git commit -m "feat: Executor texts/regions 입력 지원 및 노드 정의 업데이트

- designchecker_executor: texts 입력, include_bwms 파라미터
- pidanalyzer_executor: texts, regions 입력 및 패스스루
- pid_symbol → pid_class_aware 마이그레이션
- BWMS 샘플 이미지 추가"
```

### 커밋 3: API 스펙 및 문서
```bash
git add gateway-api/api_specs/
git add docs/api/
git commit -m "docs: API 스펙 업데이트 및 엔드포인트 문서 추가

- yolo.yaml modelTypes 상세 섹션 추가
- design-checker.yaml BWMS 파라미터 추가
- endpoints.md 문서 추가 (design-checker, line-detector, pid-analyzer)"
```

---

## ⚠️ 발견된 잠재적 이슈

### 1. min_region_area 기본값 불일치

| 위치 | 기본값 |
|------|--------|
| segmentationNodes.ts | 1000 |
| line-detector.yaml | 5000 |
| process_router.py | 5000 |

**권장**: 프론트엔드를 5000으로 변경하거나, 명시적으로 다른 값 사용 의도 문서화

### 2. PID Analyzer valve signal 파라미터

프론트엔드에 정의되었지만 백엔드 미구현:
- `extract_valve_signals`
- `valve_signal_rule_id`
- `export_valve_signal_excel`

**권장**: 별도 API 엔드포인트로 구현됨 (/api/v1/valve-signal/*) - 프론트엔드에서 분리된 API 호출로 변경 필요

---

## 📌 완료 체크리스트 요약

### P0 (긴급)
- [ ] 모든 modified 파일 스테이징
- [ ] Docker 빌드 테스트 (최소 3개 API)

### P1 (중요)
- [ ] routers/__init__.py `__all__` 확인
- [ ] pid_symbol deprecated 표기 추가
- [ ] pid-analyzer.yaml 입력 스펙 확인

### P2 (권장)
- [ ] CLAUDE.md 버전 히스토리 업데이트
- [ ] bwms_pid_sample.png 스테이징
- [ ] test-results/.gitkeep 추가

### P3 (선택)
- [ ] 전체 API health 체크 스크립트 실행
- [ ] 번역 파일 (locales) 검토

---

**작성**: Claude Code (Opus 4.5)
**상태**: 리팩토링 완료, 스테이징/커밋 대기 중
