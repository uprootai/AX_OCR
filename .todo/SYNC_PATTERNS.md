# 패턴 동기화 및 향후 작업

> **마지막 업데이트**: 2026-01-26
> **목적**: 부분적 변경이 다른 서비스에도 적용되어야 하는 항목들 추적

---

## 📊 현재 커밋 대비 변경 요약

### 통계
- **수정된 파일**: 27개 (+3,116줄 / -201줄)
- **새로 추가된 파일**: 23개
- **주요 변경 영역**: Blueprint AI BOM Phase 2, Dimension Parser, 고객 프로파일

### 카테고리별 변경

| 영역 | 수정 | 신규 | 주요 변경 |
|------|------|------|----------|
| Blueprint AI BOM Backend | 6개 | 11개 | Phase 2 아키텍처, Self-contained Export |
| Blueprint AI BOM Frontend | 7개 | 6개+ | Customer/Project 페이지, 이미지 리뷰 |
| Gateway API | 2개 | 0개 | Dimension Parser 강화, 고객 프로파일 |
| Web-UI | 7개 | 3개 | 템플릿 모달, API 확장 |
| YOLO API | 2개 | 1개 | Panasia 모델, 모델 선택 로직 |
| TODO | 2개 | 1개 | 상태 업데이트 |

---

## ✅ P0: 완료 - Dimension Parser 패턴 동기화

> **완료일**: 2026-01-26

### 1. Dimension Parser 패턴 동기화

**상태**: ✅ **동기화 완료**

| 파일 | 위치 | 패턴 수 | 상태 |
|------|------|---------|------|
| `dimensionparser_executor.py` | gateway-api | **21개** | ✅ 최신 |
| `dimension_service.py` | blueprint-ai-bom | **21개** | ✅ **동기화됨** |
| `dimension.py` (스키마) | blueprint-ai-bom | THREAD, CHAMFER 추가 | ✅ 완료 |
| `notes_extractor.py` | blueprint-ai-bom | 별도 (노트 추출용) | ✅ 확인됨 |

**동기화된 패턴**:

```python
# dimension_service.py에 추가된 복합 패턴
# 1. 직경 + 대칭 공차: Φ50±0.05 ✅
# 2. 직경 + 비대칭 공차: Φ50+0.05/-0.02 ✅
# 3. 직경 + 역순 비대칭: Φ50-0.02+0.05 ✅
# 4. 직경 + 공차등급: Ø50H7 ✅
# 5. 나사: M10, M10×1.5 ✅
# 6. 챔퍼: C2, C2×45° ✅

# tolerance_patterns에 추가된 패턴
# 7. 역순 비대칭: 50-0.02+0.05 ✅
# 8. 단방향 상한: 50 +0.05/0 ✅
# 9. 단방향 하한: 50 0/-0.05 ✅

# DimensionType enum 추가
# - THREAD (나사)
# - CHAMFER (챔퍼)
```

**완료된 작업**:

| # | 작업 | 파일 | 상태 |
|---|------|------|------|
| 1 | `_parse_dimension_text` 복합 패턴 추가 | `dimension_service.py` | ✅ 완료 |
| 2 | `tolerance_patterns` 확장 (6개 패턴) | `dimension_service.py` | ✅ 완료 |
| 3 | THREAD, CHAMFER 타입 추가 | `schemas/dimension.py` | ✅ 완료 |
| 4 | IT 공차 오탐 방지 (R, C, M 제외) | `dimension_service.py` | ✅ 완료 |
| 5 | notes_extractor.py 확인 | `notes_extractor.py` | ✅ 별도 (동기화 불필요) |

**테스트 결과**: 20/20 통과

---

## ✅ P1: 완료 - 연관 서비스 확장

> **완료일**: 2026-01-26

### 2. 고객-모델 매핑 연동

**현재 상태**: ✅ **완료**

| 항목 | 상태 | 설명 |
|------|------|------|
| `customer_config.py` | ✅ | 8개 고객 + CUSTOMER_TO_MODEL_MAP |
| `price_database.py` | ✅ | PANASIA 재질 9종 + 가공비 12종 |
| `get_model_for_customer()` | ✅ | 고객/도면타입 기반 모델 자동 선택 |

**추가된 매핑**:

```python
CUSTOMER_TO_MODEL_MAP = {
    "PANASIA": "pid_symbol",    # BWMS P&ID
    "STX": "pid_symbol",        # 조선 P&ID
    "HANJIN": "pid_symbol",     # 조선 P&ID
    "HYUNDAI": "pid_symbol",    # 조선 P&ID
    "KEPCO": "bom_detector",    # 전력 단선도
    "DSE": "engineering",       # 기계도면
    "DOOSAN": "engineering",    # 기계도면
    "SAMSUNG": "engineering",   # 기본
}
```

**추가된 PANASIA 재질** (price_database.py):
- STS316L, STS304L, TITANIUM GR2, AL5083
- CPVC, HDPE, SUPER DUPLEX, BRONZE ALBZ, INCONEL 625

**추가된 PANASIA 가공비**:
- VALVE, PUMP, FILTER, PIPE, FLANGE
- UV_REACTOR, ELECTROLYZER, TANK, SENSOR
- CONTROL_PANEL, STRAINER, HEAT_EXCHANGER

---

### 3. Self-contained Export 확장성

**현재 매핑**:

```python
# self_contained_export_service.py
BACKEND_TO_FRONTEND_MAP = {
    "blueprint-ai-bom-backend": "blueprint-ai-bom-frontend",
}

FRONTEND_SERVICES = {"blueprint-ai-bom-frontend"}
```

**향후 확장 시 추가 필요**:

| 백엔드 | 프론트엔드 | 포트 | 비고 |
|--------|-----------|------|------|
| `gateway-api` | `web-ui` | 5173 | 옵션 (워크플로우 편집기) |
| `knowledge-api` | `knowledge-ui` | TBD | 향후 지식 그래프 UI |

**작업 항목**:

| # | 작업 | 파일 | 우선순위 |
|---|------|------|----------|
| 1 | web-ui 옵션 매핑 추가 | `self_contained_export_service.py` | P2 |
| 2 | `include_web_ui` 파라미터 | `export.py` (스키마) | P2 |
| 3 | Export 옵션 UI | `blueprint-ai-bom-frontend` | P3 |

---

## ✅ P2: Phase 2 아키텍처 확산 (완료)

### 4. Template → Project → Session 패턴

**신규 추가된 파일**:

```
blueprint-ai-bom/backend/
├── routers/
│   ├── export_router.py      # Export API
│   ├── project_router.py     # 프로젝트 CRUD
│   └── template_router.py    # 템플릿 CRUD
├── schemas/
│   ├── export.py             # SelfContainedExportRequest/Response
│   ├── project.py            # Project 스키마
│   ├── template.py           # Template 스키마
│   └── workflow_session.py   # LockLevel, SessionWorkflow
├── services/
│   ├── export_service.py     # 기본 Export
│   ├── project_service.py    # 프로젝트 관리
│   ├── template_service.py   # 템플릿 관리
│   └── self_contained_export_service.py  # Docker Export
└── docs/
    └── ARCHITECTURE_PHASE2_PROJECT.md
```

**web-ui 연동 현황**:

| 기능 | 파일 | 상태 |
|------|------|------|
| Save Template | `SaveTemplateModal.tsx` | ✅ 신규 |
| Load Template | `LoadTemplateModal.tsx` | ✅ 신규 |
| Deploy Template | `DeployTemplateModal.tsx` | ✅ 신규 |
| Template API | `api.ts` (+228줄) | ✅ 추가 |

**완료/향후 작업**:

| # | 작업 | 설명 | 우선순위 | 상태 |
|---|------|------|----------|------|
| 1 | Gateway에서 Template 기반 실행 | 템플릿 ID로 파이프라인 실행 | P2 | ✅ 완료 |
| 2 | 고객별 기본 템플릿 설정 | customer_config에 default_template 추가 | P3 | ⏳ |
| 3 | 템플릿 버전 관리 | 템플릿 히스토리 및 롤백 | P3 | ⏳ |

---

## 📋 작업 체크리스트

### ✅ 완료 (P0)

- [x] `dimension_service.py` 패턴 동기화 (2026-01-26)
  - [x] 직경+공차 복합 패턴 4개 추가
  - [x] 역순 비대칭 패턴 추가
  - [x] 단방향 공차 패턴 2개 추가
  - [x] 나사/챔퍼 패턴 추가
  - [x] DimensionType enum 확장 (THREAD, CHAMFER)
  - [x] IT 공차 오탐 방지 로직 추가
  - [x] 테스트 20/20 통과

### ✅ 완료 (P1) - 2026-01-26

- [x] PANASIA 가격 데이터 추가
  - [x] BWMS 재질 9종 (STS316L, TITANIUM GR2, CPVC, HDPE 등)
  - [x] BWMS 가공비 12종 (VALVE, PUMP, FILTER, UV_REACTOR 등)
  - [x] 고객 8개 설정 동기화
- [x] 고객별 YOLO 모델 자동 선택
  - [x] CUSTOMER_TO_MODEL_MAP (8개 고객)
  - [x] DRAWING_TYPE_TO_MODEL_MAP (8개 도면타입)
  - [x] get_model_for_customer() 헬퍼 함수
- [x] notes_extractor.py 패턴 검토 (별도 동기화 불필요)

### ✅ 완료 (P2) - 2026-01-26

- [x] web-ui Export 옵션 추가
  - [x] `include_web_ui` 필드 추가 (`schemas/export.py`)
  - [x] `SERVICE_PORT_MAP`에 web-ui:5173 추가
  - [x] `OPTIONAL_SERVICES` 딕셔너리 추가
  - [x] `detect_required_services()`, `get_preview()`, `create_package()` 업데이트
- [x] Gateway Template 기반 실행
  - [x] `GET /api/v1/workflow/templates` - 템플릿 목록 (BOM API 프록시)
  - [x] `GET /api/v1/workflow/templates/{id}` - 템플릿 상세
  - [x] `POST /api/v1/workflow/execute-template/{id}` - 템플릿 실행
  - [x] `POST /api/v1/workflow/execute-template-stream/{id}` - 템플릿 SSE 실행
  - [x] 내장 템플릿 폴백 (yolo-detection, ocr-extraction, full-analysis)
  - [x] 테스트 425개 통과
- [ ] 고객별 기본 템플릿 (P3로 이동)

### 장기 (P3)

- [ ] 템플릿 버전 관리
- [ ] Export 옵션 UI (프론트엔드)
- [ ] 지식 그래프 UI 연동

---

## 🔗 관련 파일 경로

### Dimension Parser
```
gateway-api/blueprintflow/executors/dimensionparser_executor.py  # 소스
blueprint-ai-bom/backend/services/dimension_service.py           # 동기화 대상
blueprint-ai-bom/backend/services/notes_extractor.py             # 확인 필요
```

### 고객 프로파일
```
gateway-api/services/customer_config.py      # 8개 고객
gateway-api/services/price_database.py       # 가격 데이터
models/yolo-api/models/classes_panasia.txt   # PANASIA 클래스
models/yolo-api/models/model_registry.yaml   # 모델 등록
```

### Self-contained Export
```
blueprint-ai-bom/backend/services/self_contained_export_service.py
blueprint-ai-bom/backend/schemas/export.py
blueprint-ai-bom/backend/routers/export_router.py
```

---

## 📝 변경 이력

| 날짜 | 작업 | 상태 |
|------|------|------|
| 2026-01-25 | Dimension Parser 9개 패턴 추가 | ✅ Gateway만 |
| 2026-01-25 | 고객 프로파일 8개 (PANASIA, HANJIN) | ✅ 완료 |
| 2026-01-25 | Self-contained 프론트엔드 포함 | ✅ 완료 |
| 2026-01-25 | Phase 2 아키텍처 (Template/Project/Session) | ✅ 완료 |
| 2026-01-26 | dimension_service.py 동기화 (21개 패턴) | ✅ 완료 |
| 2026-01-26 | PANASIA 가격 데이터 (재질 9종, 가공비 12종) | ✅ 완료 |
| 2026-01-26 | web-ui Export 옵션 (include_web_ui) | ✅ 완료 |
| 2026-01-26 | Gateway Template 기반 실행 (4개 엔드포인트) | ✅ 완료 |

---

*이 문서는 부분적 변경이 다른 서비스에 미치는 영향을 추적합니다.*
*새로운 패턴이 추가되면 이 문서를 업데이트하세요.*
