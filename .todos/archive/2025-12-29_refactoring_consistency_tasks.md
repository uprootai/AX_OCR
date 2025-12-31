# API 리팩토링 일관성 작업 목록

> **생성일**: 2025-12-29
> **목적**: git status 분석 기반 코드베이스 일관성 확보

---

## 📊 현황 요약

| 구분 | 완료 | 부분 | 미적용 | 총계 |
|------|------|------|--------|------|
| 라우터 분리 | 9개 | 4개 | 4개 | 17개 |
| Lifespan 패턴 | 14개 | - | 3개 | 17개 |
| endpoints.md | 3개 | - | 16개 | 19개 |

### 즉시 필요한 작업
1. **8개 API 라우터 분리** (300줄 이상 유지 중)
2. **3개 API Lifespan 패턴 적용** (skinmodel, tesseract, ocr-ensemble)
3. **16개 API endpoints.md 문서 생성**
4. **Untracked 파일 git add** (12개 디렉토리/파일)

### 검증 완료 사항
- ✅ `pid_symbol` → `pid_class_aware` 마이그레이션 완료
- ✅ YOLO API 스펙 modelTypes 상세화 완료
- ✅ Design Checker BWMS 규칙 시스템 추가 완료

---

## 1. 변경사항 요약

### 핵심 패턴 변경
1. **Lifespan 패턴 마이그레이션**: `@app.on_event("startup/shutdown")` → `lifespan` 컨텍스트 매니저
2. **라우터 분리 패턴**: 500줄 이상 API를 `routers/`, `services/`, `schemas.py`로 분리
3. **상태 관리 패턴**: 글로벌 상태를 `services/state.py`로 중앙화
4. **문서화**: `docs/api/*/endpoints.md` 엔드포인트 문서 추가

---

## 2. API별 리팩토링 상태

### ✅ 완전 리팩토링 완료 (9개)
| API | api_server.py | lifespan | routers/ | services/state.py |
|-----|---------------|----------|----------|-------------------|
| design-checker-api | 175줄 | ✅ | ✅ | N/A (routers에서 직접 import) |
| line-detector-api | 136줄 | ✅ | ✅ | ✅ |
| pid-analyzer-api | 137줄 | ✅ | ✅ | ✅ |
| vl-api | 202줄 | ✅ | ✅ | ✅ |
| yolo-api | 165줄 | ✅ | ✅ | ✅ (registry.py) |
| edgnet-api | 213줄 | ✅ | ✅ | ✅ |
| esrgan-api | 114줄 | ✅ | ✅ | ✅ |
| knowledge-api | 279줄 | ✅ | ✅ | ✅ |
| ocr-ensemble-api | 99줄 | N/A | ✅ | N/A (모델 로딩 불필요) |

### ⚠️ 부분 리팩토링 (4개) - 라우터 분리 필요
| API | api_server.py | lifespan | routers/ | services/ | 상태 |
|-----|---------------|----------|----------|-----------|------|
| edocr2-v2-api | 357줄 | ✅ | ❌ | ✅ ocr_processor.py | routers 분리 필요 |
| paddleocr-api | 324줄 | ✅ | ❌ | ✅ ocr.py | routers 분리 필요 |
| skinmodel-api | 384줄 | ❌ | ❌ | ✅ tolerance.py | lifespan + routers 필요 |
| tesseract-api | 341줄 | ❌ | ❌ | ❌ (빈 디렉토리) | 전체 리팩토링 필요 |

### ❌ 리팩토링 미적용 (4개) - 전체 리팩토링 필요
| API | api_server.py | lifespan | routers/ | services/ |
|-----|---------------|----------|----------|-----------|
| doctr-api | 373줄 | ✅ | ❌ | ❌ |
| easyocr-api | 368줄 | ✅ | ❌ | ❌ |
| surya-ocr-api | 390줄 | ✅ | ❌ | ❌ |
| trocr-api | 402줄 | ✅ | ❌ | ❌ |

---

## 3. 상세 작업 목록

### 3.1 Lifespan 패턴 적용 필요 (2개)

#### [ ] skinmodel-api
- 현재: `@app.on_event` 사용 없음 (startup 로직 없음)
- 필요: lifespan 패턴 추가 (서비스 초기화 명시적 처리)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SkinModel API...")
    yield
    logger.info("Shutting down SkinModel API...")
```

#### [ ] tesseract-api
- 현재: startup/shutdown 로직 없음
- 필요: lifespan 패턴 추가 (Tesseract 모델 체크)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Tesseract API...")
    if not TESSERACT_AVAILABLE:
        logger.warning("Tesseract not available")
    yield
    logger.info("Shutting down Tesseract API...")
```

---

### 3.2 라우터 분리 필요 (8개)

#### 우선순위 1: 400줄 이상
| API | 줄 수 | 분리 대상 엔드포인트 |
|-----|-------|---------------------|
| trocr-api | 402줄 | /health, /api/v1/info, /api/v1/ocr |
| surya-ocr-api | 390줄 | /health, /api/v1/info, /api/v1/ocr, /api/v1/layout |
| skinmodel-api | 384줄 | /health, /api/v1/info, /api/v1/tolerance, /api/v1/gdt/validate |
| doctr-api | 373줄 | /health, /api/v1/info, /api/v1/ocr |
| easyocr-api | 368줄 | /health, /api/v1/info, /api/v1/ocr |

#### 우선순위 2: 300-400줄
| API | 줄 수 | 분리 대상 엔드포인트 |
|-----|-------|---------------------|
| edocr2-v2-api | 357줄 | /health, /api/v1/info, /api/v1/ocr, /api/v2/ocr |
| tesseract-api | 341줄 | /health, /api/v1/info, /api/v1/ocr |
| paddleocr-api | 324줄 | /health, /api/v1/info, /api/v1/ocr |

#### 라우터 분리 템플릿
```
models/{api-name}/
├── api_server.py          # 슬림화 (< 200줄)
├── schemas.py             # Pydantic 모델
├── routers/
│   ├── __init__.py
│   └── ocr_router.py      # 엔드포인트 핸들러
└── services/
    ├── __init__.py
    ├── state.py           # 글로벌 상태 관리
    └── {feature}_service.py
```

---

### 3.3 서비스 상태 관리 패턴 적용

현재 services/ 디렉토리가 있지만 state.py가 없는 API:
- [ ] edocr2-v2-api - `services/state.py` 추가 필요
- [ ] paddleocr-api - `services/state.py` 추가 필요
- [ ] skinmodel-api - `services/state.py` 추가 필요

#### state.py 템플릿
```python
"""
{API Name} Global State Management
"""
from typing import Optional

_service_instance: Optional[SomeService] = None

def get_service() -> Optional[SomeService]:
    return _service_instance

def set_service(service: Optional[SomeService]):
    global _service_instance
    _service_instance = service
```

---

### 3.4 문서화 작업

#### endpoints.md 파일 필요 (16개 API)
현재 endpoints.md 있는 API: design-checker, line-detector, pid-analyzer

| API | parameters.md | endpoints.md | 작업 필요 |
|-----|---------------|--------------|-----------|
| blueprint-ai-bom | ✅ | ❌ | 생성 필요 |
| doctr | ✅ | ❌ | 생성 필요 |
| easyocr | ✅ | ❌ | 생성 필요 |
| edgnet | ✅ | ❌ | 생성 필요 |
| edocr2 | ✅ | ❌ | 생성 필요 |
| esrgan | ✅ | ❌ | 생성 필요 |
| knowledge | ✅ | ❌ | 생성 필요 |
| ocr-ensemble | ✅ | ❌ | 생성 필요 |
| paddleocr | ✅ | ❌ | 생성 필요 |
| skinmodel | ✅ | ❌ | 생성 필요 |
| surya-ocr | ✅ | ❌ | 생성 필요 |
| tesseract | ✅ | ❌ | 생성 필요 |
| trocr | ✅ | ❌ | 생성 필요 |
| vl | ✅ | ❌ | 생성 필요 |
| yolo | ✅ | ❌ | 생성 필요 |

#### endpoints.md 템플릿
```markdown
# {API Name} API Endpoints

## Health Check
- **GET** `/health` - 서비스 상태 확인

## API Info
- **GET** `/api/v1/info` - BlueprintFlow 메타데이터

## Core Endpoints
- **POST** `/api/v1/{action}` - 주요 기능
  - Parameters: ...
  - Response: ...
```

---

## 4. 스테이징 필요 파일 (Untracked)

### 최근 리팩토링 결과물 (git add 필요)
```bash
git add models/edgnet-api/routers/
git add models/edgnet-api/services/state.py
git add models/esrgan-api/routers/
git add models/esrgan-api/schemas.py
git add models/esrgan-api/services/
git add models/knowledge-api/routers/
git add models/knowledge-api/services/state.py
git add models/ocr-ensemble-api/routers/
git add models/ocr-ensemble-api/schemas.py
git add models/ocr-ensemble-api/services/
git add models/yolo-api/routers/
git add models/yolo-api/services/registry.py
git add models/yolo-api/services/sahi_inference.py
```

---

## 5. 삭제된 파일 확인

test-results/ 디렉토리의 테스트 결과 파일들이 삭제됨:
- test-results/pid-analysis-new/
- test-results/pid-analysis/00-29-48_P_ID_Analysis_Pipeline/
- test-results/pid-debug/

→ 테스트 결과는 임시 데이터이므로 삭제 유지 권장

---

## 6. 작업 우선순위

### Phase 1: 긴급 (라우터 분리 없이 400줄+ 유지)
1. [ ] trocr-api 라우터 분리 (402줄)
2. [ ] surya-ocr-api 라우터 분리 (390줄)
3. [ ] skinmodel-api 라우터 분리 + lifespan (384줄)
4. [ ] doctr-api 라우터 분리 (373줄)
5. [ ] easyocr-api 라우터 분리 (368줄)

### Phase 2: 중요 (300-400줄)
6. [ ] edocr2-v2-api 라우터 분리 (357줄)
7. [ ] tesseract-api 라우터 분리 + lifespan (341줄)
8. [ ] paddleocr-api 라우터 분리 (324줄)

### Phase 3: 문서화
9. [ ] 16개 API에 endpoints.md 추가

### Phase 4: Git 정리
10. [ ] Untracked 파일 스테이징
11. [ ] 커밋 생성

---

## 7. 검증 체크리스트

각 API 리팩토링 완료 시:
- [ ] `python3 -m py_compile` 구문 검증
- [ ] `docker-compose build {service}` 빌드 성공
- [ ] `curl http://localhost:{port}/health` 응답 확인
- [ ] `curl http://localhost:{port}/api/v1/info` 메타데이터 확인

---

## 8. Web-UI 및 Gateway-API 변경사항

### 8.1 YOLO model_type 변경
| 이전 | 현재 | 비고 |
|------|------|------|
| pid_symbol | ❌ 제거됨 | pid_class_aware로 대체 |
| pid_class_aware | ✅ 주력 모델 | 32종 P&ID 심볼 분류 |
| pid_class_agnostic | ✅ 유지 | 위치만 검출 |
| engineering | ✅ 유지 | 기계도면 14종 |
| bom_detector | ✅ 유지 | 전력설비 27종 |

**영향 받는 파일**:
- `gateway-api/api_specs/yolo.yaml` - 상세 modelTypes 정의 추가
- `web-ui/src/config/nodes/detectionNodes.ts` - 옵션 순서 변경, 설명 업데이트
- `web-ui/src/config/nodes/analysisNodes.ts` - pid_symbol → pid_class_aware 참조 변경

### 8.2 Design Checker BWMS 카테고리 추가
- categories 옵션에 'bwms' 추가됨
- TECHCROSS 전용 규칙 검사 카테고리
- `texts` 입력 추가 (BWMS 규칙 검사용 OCR 텍스트)

### 8.3 PID Analyzer 변경
- Valve Signal 추출 기능이 별도 API로 분리됨 (`/api/v1/valve-signal/extract`)
- 설명 텍스트 간소화

### 8.4 Gateway-API 변경
| 파일 | 변경 내용 |
|------|----------|
| api_server.py | 146줄 리팩토링 (+140/-72) |
| designchecker_executor.py | BWMS 검사 기능 추가 |
| pidanalyzer_executor.py | 46줄 추가 (새 기능) |
| yolo_service.py | model_type 매핑 수정 |

### 8.5 일관성 검증 필요 사항

#### [ ] 다른 노드 정의 파일 검토
- `ocrNodes.ts` - pid_symbol 참조 있는지 확인
- `preprocessingNodes.ts` - 관련 참조 확인
- `controlNodes.ts` - 관련 참조 확인

#### [ ] API 스펙 파일 동기화
기존 `pid_symbol` 참조가 남아있는지 확인 필요:
```bash
grep -r "pid_symbol" gateway-api/api_specs/
grep -r "pid_symbol" web-ui/src/
```

---

## 9. 참고: 리팩토링된 API 패턴 예시

### yolo-api (165줄) - 가장 잘 정리된 예시
```
models/yolo-api/
├── api_server.py (165줄)      # FastAPI app, lifespan, health endpoint
├── routers/
│   ├── __init__.py            # detection_router, models_router export
│   ├── detection_router.py    # /detect, /extract_dimensions
│   └── models_router.py       # /models CRUD
├── services/
│   ├── __init__.py
│   ├── inference.py           # YOLOInferenceService
│   ├── registry.py            # ModelRegistry, global state
│   └── sahi_inference.py      # SAHI slicing inference
├── models/
│   └── schemas.py             # Pydantic 모델
└── utils/
    └── helpers.py             # 유틸리티 함수
```

### 핵심 원칙
1. **api_server.py < 300줄**: lifespan, health, router include만
2. **routers/*.py**: 엔드포인트 핸들러, 비즈니스 로직 호출
3. **services/state.py**: 글로벌 상태 getter/setter
4. **services/*_service.py**: 실제 비즈니스 로직
5. **schemas.py**: Pydantic 모델 정의
