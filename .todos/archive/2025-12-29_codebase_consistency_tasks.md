# 코드베이스 일관성 작업 목록 (2025-12-29)

> **목적**: Design Checker 리팩토링에서 적용된 패턴들을 다른 API/노드에도 일관되게 적용
> **우선순위**: P0(긴급) > P1(중요) > P2(권장) > P3(선택)

---

## 1. [P0] on_event Deprecated 마이그레이션 (15개 API)

FastAPI의 `@app.on_event("startup/shutdown")`이 deprecated됨. `lifespan` 패턴으로 마이그레이션 필요.

### 영향받는 API 목록

| API | 파일 | startup | shutdown | 우선순위 |
|-----|------|---------|----------|----------|
| yolo-api | `models/yolo-api/api_server.py` | O | O | P0 |
| edocr2-v2-api | `models/edocr2-v2-api/api_server.py` | O | O | P0 |
| paddleocr-api | `models/paddleocr-api/api_server.py` | O | O | P0 |
| vl-api | `models/vl-api/api_server.py` | O | O | P1 |
| knowledge-api | `models/knowledge-api/api_server.py` | O | O | P1 |
| edgnet-api | `models/edgnet-api/api_server.py` | O | X | P2 |
| esrgan-api | `models/esrgan-api/api_server.py` | O | X | P2 |
| trocr-api | `models/trocr-api/api_server.py` | O | X | P2 |
| doctr-api | `models/doctr-api/api_server.py` | O | X | P2 |
| easyocr-api | `models/easyocr-api/api_server.py` | O | X | P2 |
| surya-ocr-api | `models/surya-ocr-api/api_server.py` | O | X | P2 |

### 마이그레이션 패턴 (Design Checker 참조)

```python
# Before (deprecated)
@app.on_event("startup")
async def startup_event():
    logger.info("Starting...")
    # 초기화 로직

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    # 정리 로직

# After (lifespan pattern)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting...")
    # 초기화 로직

    yield  # 앱 실행

    # Shutdown
    logger.info("Shutting down...")
    # 정리 로직

app = FastAPI(
    title="API Name",
    lifespan=lifespan  # 추가
)
```

### 작업 체크리스트 (2025-12-29 완료)

- [x] yolo-api lifespan 마이그레이션 ✅
- [x] edocr2-v2-api lifespan 마이그레이션 ✅
- [x] paddleocr-api lifespan 마이그레이션 ✅
- [x] vl-api lifespan 마이그레이션 ✅
- [x] knowledge-api lifespan 마이그레이션 ✅
- [x] edgnet-api lifespan 마이그레이션 ✅
- [x] esrgan-api lifespan 마이그레이션 ✅
- [x] trocr-api lifespan 마이그레이션 ✅
- [x] doctr-api lifespan 마이그레이션 ✅
- [x] easyocr-api lifespan 마이그레이션 ✅
- [x] surya-ocr-api lifespan 마이그레이션 ✅
- [x] edocr2 레거시 v1/v2 마이그레이션 ✅ (2025-12-29)
- [x] gateway-api lifespan 마이그레이션 ✅ (2025-12-29)

---

## 2. [P0] 대형 API 라우터 분리 (1000줄 이상) - ✅ 완료

CLAUDE.md 규칙: 모든 소스 파일은 1000줄 이하로 유지

### 영향받는 API 목록 (2025-12-29 업데이트)

| API | 이전 줄 수 | 현재 줄 수 | 상태 | 비고 |
|-----|-----------|-----------|------|------|
| pid-analyzer-api | 1,926줄 | 137줄 | ✅ 완료 | services/ + routers/ 분리 |
| line-detector-api | 1,422줄 | 136줄 | ✅ 완료 | services/ + routers/ 분리 |
| vl-api | 1,035줄 | 202줄 | ✅ 완료 | services/ + routers/ + schemas.py 분리 (2025-12-29) |
| yolo-api | 864줄 | 864줄 | ⚠️ 양호 | 모니터링 중 |

### PID Analyzer 분리 결과 ✅

```
models/pid-analyzer-api/
├── api_server.py           # 137줄 (lifespan + health endpoints)
├── equipment_analyzer.py   # 기존 (장비 분석)
├── region_extractor.py     # 기존 (영역 추출)
├── region_rules.yaml       # 기존 (영역 규칙)
├── services/
│   ├── __init__.py         # 51줄
│   └── analysis_service.py # 725줄 (핵심 분석 함수)
└── routers/
    ├── __init__.py         # 16줄
    ├── analysis_router.py  # 244줄 (/api/v1/analyze, /info)
    ├── bwms_router.py      # 238줄 (/api/v1/bwms/*)
    ├── equipment_router.py # 288줄 (/api/v1/equipment/*)
    └── region_router.py    # 464줄 (/api/v1/region-*, /valve-signal/*)
총 2,163줄 (평균 파일: ~240줄)
```

### Line Detector 분리 결과 ✅

```
models/line-detector-api/
├── api_server.py               # 136줄 (lifespan + health endpoints)
├── services/
│   ├── __init__.py             # 71줄
│   ├── constants.py            # 52줄 (상수 정의)
│   ├── detection_service.py    # 281줄 (LSD/Hough 검출)
│   ├── classification_service.py # 310줄 (스타일/색상 분류)
│   ├── region_service.py       # 171줄 (영역 검출)
│   └── visualization_service.py # 98줄 (시각화)
└── routers/
    ├── __init__.py             # 8줄
    └── process_router.py       # 321줄 (/api/v1/process, /info)
총 1,448줄 (평균 파일: ~161줄)
```

### 작업 체크리스트

- [x] pid-analyzer-api services/ + routers/ 폴더 생성 ✅
- [x] pid-analyzer-api services/analysis_service.py 분리 ✅
- [x] pid-analyzer-api routers/analysis_router.py 분리 ✅
- [x] pid-analyzer-api routers/bwms_router.py 분리 ✅
- [x] pid-analyzer-api routers/equipment_router.py 분리 ✅
- [x] pid-analyzer-api routers/region_router.py 분리 ✅
- [x] line-detector-api services/ + routers/ 폴더 생성 ✅
- [x] line-detector-api services/* 분리 ✅
- [x] line-detector-api routers/process_router.py 분리 ✅
- [x] vl-api services/ + routers/ + schemas.py 분리 ✅ (2025-12-29)
- [x] vl-api api_server.py 202줄로 슬림화 ✅

---

## 3. [P1] pid_symbol → pid_class_aware 통일

`pid_symbol` 모델 타입이 `pid_class_aware`로 변경되어야 하는데, 일부 파일에서 아직 이전 이름 사용 중.

### 영향받는 파일 목록

| 파일 | 현재 상태 | 필요 작업 |
|------|----------|----------|
| `gateway-api/services/yolo_service.py` | pid_symbol 언급 | 주석/설명 업데이트 |
| `models/yolo-api/api_server.py` | pid_symbol 옵션 포함 | 옵션 순서/설명 변경 |
| `models/yolo-api/models/model_registry.yaml` | pid_symbol 모델 정의 | 유지 (레거시 호환) |

### 변경 방침

1. **프론트엔드**: `pid_symbol` 옵션 제거, `pid_class_aware` 사용
2. **백엔드**: `pid_symbol` 요청 시 `pid_class_aware`로 자동 매핑 (하위 호환)
3. **문서**: `pid_class_aware` 중심으로 작성, `pid_symbol`은 deprecated 표기

### 작업 체크리스트

- [ ] yolo_service.py 주석 업데이트
- [ ] yolo-api api_server.py 옵션 순서 변경
- [ ] yolo-api model_registry.yaml에 deprecated 표기 추가
- [ ] 프론트엔드 노드 정의에서 pid_symbol 완전 제거 확인

---

## 4. [P1] Docker Compose 볼륨 마운트 일관성

Design Checker에 `config` 볼륨 마운트가 추가됨. 다른 API들도 동적 설정이 필요한 경우 동일 패턴 적용.

### 현재 추가된 마운트

```yaml
# design-checker-api
volumes:
  - ./models/design-checker-api/config:/app/config  # 신규 추가
```

### 검토 필요 API

| API | 동적 설정 필요 | 권장 마운트 |
|-----|--------------|------------|
| pid-analyzer-api | region_rules.yaml | `config:/app/config` |
| yolo-api | model_registry.yaml | 이미 마운트됨 |
| knowledge-api | graph 설정 | 검토 필요 |

### 작업 체크리스트

- [ ] pid-analyzer-api config 볼륨 마운트 추가
- [ ] 다른 API 동적 설정 필요 여부 검토

---

## 5. [P1] Executor 입력 패턴 표준화

`designchecker_executor.py`에 `texts` 입력이 추가됨. 다른 executor들도 동일한 패턴 적용 필요.

### 추가된 패턴

```python
# texts 입력 처리
if "texts" in inputs:
    texts = inputs.get("texts", [])
if "text_results" in inputs:
    texts = inputs.get("text_results", [])

# from_ prefix 처리 (Merge 패턴)
for key, value in inputs.items():
    if key.startswith("from_") and isinstance(value, dict):
        if "texts" in value and not texts:
            texts = value.get("texts", [])
        if "text_results" in value and not texts:
            texts = value.get("text_results", [])
```

### 검토 필요 Executor

| Executor | texts 입력 필요 | 현재 상태 |
|----------|----------------|----------|
| designchecker_executor | O | ✅ 완료 |
| pidanalyzer_executor | O | ❌ **누락됨** |
| bom_executor | X | - |
| yolo_executor | X | - |

### pidanalyzer_executor 수정 필요 사항

`gateway-api/blueprintflow/executors/pidanalyzer_executor.py`에 texts 입력 처리 추가 필요:

```python
# 현재 (누락됨)
symbols = []
lines = []
intersections = []
image_base64 = ""

# 수정 필요 (texts 추가)
symbols = []
lines = []
intersections = []
texts = []  # 추가
regions = []  # 추가 (valve signal 추출용)
image_base64 = ""

# 직접 입력 확인에 추가
if "texts" in inputs:
    texts = inputs.get("texts", [])
if "text_results" in inputs:
    texts = inputs.get("text_results", [])
if "regions" in inputs:
    regions = inputs.get("regions", [])

# from_ prefix 처리에 추가
for key, value in inputs.items():
    if key.startswith("from_") and isinstance(value, dict):
        if "texts" in value and not texts:
            texts = value.get("texts", [])
        if "text_results" in value and not texts:
            texts = value.get("text_results", [])
        if "regions" in value and not regions:
            regions = value.get("regions", [])
```

### 작업 체크리스트

- [ ] pidanalyzer_executor texts 입력 처리 추가 (**중요**)
- [ ] pidanalyzer_executor regions 입력 처리 추가
- [ ] json_body에 texts, regions 추가
- [ ] 다른 executor 검토

---

## 6. [P2] API 문서 구조 표준화

Design Checker에 추가된 문서 패턴을 다른 API에도 적용.

### 현재 Design Checker 문서 구조

```
docs/api/design-checker/
├── parameters.md       # 파라미터 + 아키텍처
├── endpoints.md        # 전체 엔드포인트 목록 (신규)
└── bwms-rules.md       # 도메인 특화 문서 (신규)
```

### 적용 권장 API

| API | 추가 필요 문서 | 우선순위 |
|-----|--------------|----------|
| pid-analyzer | endpoints.md, region-rules.md | P1 |
| line-detector | endpoints.md | P2 |
| yolo | model-types.md (상세) | P2 |
| blueprint-ai-bom | 이미 상세 문서 있음 | - |

### 작업 체크리스트

- [ ] pid-analyzer endpoints.md 작성
- [ ] pid-analyzer region-rules.md 작성
- [ ] line-detector endpoints.md 작성
- [ ] yolo model-types.md 상세화

---

## 7. [P2] 프론트엔드 노드 정의 일관성

`analysisNodes.ts`에 추가된 패턴들이 다른 노드에도 일관되게 적용되어야 함.

### 추가된 패턴

1. **optional 입력 명시**:
```typescript
{
  name: 'regions',
  type: 'Region[]',
  description: '📦 ...',
  optional: true,  // 명시적 optional
}
```

2. **recommendedInputs 상세화**:
```typescript
recommendedInputs: [
  {
    from: 'linedetector',
    field: 'regions',
    reason: '📦 점선 영역 정보로...',
  },
]
```

### 검토 필요 노드

| 노드 파일 | 검토 항목 |
|----------|----------|
| ocrNodes.ts | optional 입력 명시 |
| segmentationNodes.ts | recommendedInputs 상세화 |
| detectionNodes.ts | 이미 업데이트됨 ✅ |
| analysisNodes.ts | 이미 업데이트됨 ✅ |

### 작업 체크리스트

- [ ] ocrNodes.ts optional 입력 검토
- [ ] segmentationNodes.ts recommendedInputs 검토
- [ ] knowledgeNodes.ts 검토
- [ ] aiNodes.ts 검토

---

## 8. [P2] API 스펙 YAML 확장 패턴

`yolo.yaml`에 추가된 `modelTypes` 섹션 패턴을 다른 API에도 적용.

### 추가된 패턴

```yaml
# yolo.yaml
modelTypes:
  engineering:
    name: "Engineering (기계도면)"
    classes: 14
    description: "..."
    detectableSymbols: [...]
    recommendedParams:
      confidence: 0.25
      iou: 0.45
    useCases: [...]
```

### 적용 권장 API

| API | 확장 섹션 | 내용 |
|-----|----------|------|
| ocr-ensemble | engineWeights | 각 OCR 엔진별 가중치 |
| edgnet | segmentationModes | 각 모드별 상세 |
| line-detector | lineTypes | 라인 스타일별 상세 |

### 작업 체크리스트

- [ ] ocr-ensemble.yaml engineWeights 섹션 추가
- [ ] line-detector.yaml lineTypes 섹션 추가
- [ ] edgnet.yaml segmentationModes 섹션 추가

---

## 9. [P3] 테스트 결과 정리

삭제된 테스트 결과 파일들 정리 완료 확인.

### 삭제된 파일

```
test-results/pid-analysis-new/         (전체 삭제)
test-results/pid-analysis/00-29-48_*/  (전체 삭제)
test-results/pid-debug/                (전체 삭제)
```

### 작업 체크리스트

- [ ] test-results/.gitkeep 추가 (폴더 유지)
- [ ] .gitignore에 test-results/*.json 추가 확인

---

## 10. [P3] 신규 파일 Git 추가

Untracked 파일들 중 Git에 추가해야 할 항목.

### 추가 필요 파일

| 파일/폴더 | Git 추가 | 이유 |
|----------|---------|------|
| docs/api/design-checker/bwms-rules.md | O | 문서 |
| docs/api/design-checker/endpoints.md | O | 문서 |
| models/design-checker-api/bwms_rules.py | O | 코드 |
| models/design-checker-api/checker.py | O | 코드 |
| models/design-checker-api/config/ | O | 설정 폴더 |
| models/design-checker-api/constants.py | O | 코드 |
| models/design-checker-api/excel_parser.py | O | 코드 |
| models/design-checker-api/routers/ | O | 코드 |
| models/design-checker-api/rule_loader.py | O | 코드 |
| models/design-checker-api/schemas.py | O | 코드 |
| models/design-checker-api/templates/ | O | 템플릿 |
| models/pid-analyzer-api/region_extractor.py | O | 코드 |
| models/pid-analyzer-api/region_rules.yaml | O | 설정 |
| **models/vl-api/routers/** | O | 코드 (**신규 - 2025-12-29**) |
| **models/vl-api/schemas.py** | O | 코드 (**신규 - 2025-12-29**) |
| **models/vl-api/services/** | O | 코드 (**신규 - 2025-12-29**) |
| web-ui/public/samples/bwms_pid_sample.png | O | 샘플 |
| apply-company/techloss/test_output/ | X | 테스트 출력 |
| .todos/TECHCROSS_요구사항_분석_20251229.md | O | TODO |

### 작업 체크리스트

- [ ] 위 파일들 git add
- [ ] test_output/ .gitignore 추가
- [ ] **vl-api 신규 파일 git add (routers/, schemas.py, services/)**

---

## 11. [발견된 불일치] 프론트엔드-백엔드 파라미터 (2025-12-29 검증)

### ❌ min_region_area 불일치

| 위치 | default | min | 상태 |
|------|---------|-----|------|
| 프론트엔드 (segmentationNodes.ts) | 1000 | 500 | ❌ 변경됨 |
| 백엔드 (line-detector.yaml) | 5000 | 1000 | ✅ 원본 |
| 백엔드 (process_router.py) | 5000 | - | ✅ 원본 |

**수정 필요:**
```typescript
// web-ui/src/config/nodes/segmentationNodes.ts
// 프론트엔드를 백엔드와 일치시켜야 함
default: 5000,  // 1000 → 5000
min: 1000,      // 500 → 1000
```

### ⚠️ PID Analyzer Valve Signal 파라미터 누락

프론트엔드에 추가된 파라미터가 백엔드 API 스펙에 누락됨:

| 파라미터 | 프론트엔드 | 백엔드 코드 | API 스펙 |
|---------|-----------|-----------|---------|
| extract_valve_signals | ✅ | ❌ | ❌ |
| valve_signal_rule_id | ✅ | ❌ | ❌ |
| text_margin | ✅ | ✅ | ✅ |
| export_valve_signal_excel | ✅ | ✅ (별도 API) | ❌ |

**결정 필요:**
- 옵션 1: 프론트엔드에서 미구현 파라미터 제거
- 옵션 2: 백엔드에 파라미터 구현 추가

---

## 요약: 우선순위별 작업량

| 우선순위 | 작업 수 | 예상 시간 |
|----------|--------|----------|
| **P0 (긴급)** | 14개 | 2-3시간 |
| **P1 (중요)** | 8개 | 2-3시간 |
| **P2 (권장)** | 12개 | 3-4시간 |
| **P3 (선택)** | 4개 | 30분 |

---

## 11. [참고] 신규 추가된 모듈 및 기능

### Design Checker 신규 모듈

| 파일 | 줄 수 | 역할 |
|------|------|------|
| `schemas.py` | 81줄 | Pydantic 모델 정의 |
| `constants.py` | 219줄 | 규칙 상수 정의 (20개) |
| `checker.py` | 354줄 | 설계 검증 로직 |
| `bwms_rules.py` | 822줄 | BWMS 규칙 엔진 |
| `rule_loader.py` | 260줄 | YAML 규칙 로더 |
| `excel_parser.py` | 210줄 | Excel 체크리스트 파서 |
| `routers/check_router.py` | 220줄 | 검증 엔드포인트 |
| `routers/rules_router.py` | 295줄 | 규칙 관리 엔드포인트 |
| `routers/checklist_router.py` | 311줄 | 체크리스트 엔드포인트 |

### PID Analyzer 신규 모듈

| 파일 | 줄 수 | 역할 |
|------|------|------|
| `region_extractor.py` | 929줄 | 영역 기반 텍스트 추출 엔진 |
| `region_rules.yaml` | 229줄 | 영역 추출 규칙 (4개 규칙 + 템플릿) |

### 신규 API 엔드포인트

**Design Checker (20개)**:
- `/api/v1/check`, `/api/v1/check/bwms`, `/api/v1/process`
- `/api/v1/rules`, `/api/v1/rules/bwms`, `/api/v1/rules/status`
- `/api/v1/rules/files`, `/api/v1/rules/reload`
- `/api/v1/rules/disable`, `/api/v1/rules/enable`
- `/api/v1/rules/profile/activate`, `/api/v1/rules/profile/deactivate`
- `/api/v1/checklist/template`, `/api/v1/checklist/upload`
- `/api/v1/checklist/files`, `/api/v1/checklist/load`, `/api/v1/checklist/current`
- `/health`, `/api/v1/health`, `/api/v1/info`

**PID Analyzer (신규 추가)**:
- `/api/v1/region-rules` (GET, POST)
- `/api/v1/region-rules/{rule_id}` (GET, PUT, DELETE)
- `/api/v1/region-text/extract` (POST)
- `/api/v1/valve-signal/extract` (POST)
- `/api/v1/valve-signal/export-excel` (POST)

### BlueprintFlow 변경

**새 샘플 추가**:
- `bwms_pid_sample.png` - BWMS P&ID 샘플 (SIGNAL 영역 테스트용)

**노드 정의 확장**:
- `analysisNodes.ts`: PID Analyzer에 region_extraction 파라미터 추가
- `detectionNodes.ts`: pid_class_aware 우선 순위 변경
- `segmentationNodes.ts`: min_region_area 기본값 변경

---

**작성일**: 2025-12-29
**작성자**: Claude Code (Opus 4.5)
**관련 커밋**: Design Checker v1.0 리팩토링, PID Analyzer Region Extraction 추가
