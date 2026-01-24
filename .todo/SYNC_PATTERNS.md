# 패턴 동기화 및 향후 작업

> **마지막 업데이트**: 2026-01-25
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

## 🔴 P0: 즉시 동기화 필요

### 1. Dimension Parser 패턴 동기화

**문제**: Gateway와 BOM의 치수 파싱 패턴이 불일치

| 파일 | 위치 | 패턴 수 | 상태 |
|------|------|---------|------|
| `dimensionparser_executor.py` | gateway-api | **21개** | ✅ 최신 |
| `dimension_service.py` | blueprint-ai-bom | 3개 | ❌ 구버전 |
| `notes_extractor.py` | blueprint-ai-bom | 일부 | ⚠️ 확인 필요 |

**Gateway에 추가된 패턴 (BOM에 미반영)**:

```python
# 1. 직경 + 대칭 공차: Φ50±0.05
r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)"

# 2. 직경 + 비대칭 공차: Φ50+0.05/-0.02
r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)"

# 3. 직경 + 역순 비대칭: Φ50-0.02+0.05
r"[ØφΦ⌀]\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)"

# 4. 역순 비대칭: 100-0.02+0.05
r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)"

# 5. 단방향 공차 (상한): 50 +0.05/0
r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*0(?!\d)"

# 6. 단방향 공차 (하한): 50 0/-0.05
r"(\d+\.?\d*)\s*0\s*/\s*-\s*(\d+\.?\d*)"

# 7. 나사 치수: M10×1.5
r"M\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*))?"

# 8. 각도: 45°
r"(\d+\.?\d*)\s*°"

# 9. 표면 거칠기: Ra 3.2
r"Ra\s*(\d+\.?\d*)"
```

**작업 항목**:

| # | 작업 | 파일 | 우선순위 |
|---|------|------|----------|
| 1 | tolerance_patterns 배열 확장 | `dimension_service.py:249-253` | P0 |
| 2 | 나사/각도/표면거칠기 추출 추가 | `dimension_service.py` | P0 |
| 3 | 패턴 테스트 케이스 추가 | `tests/test_dimension_service.py` | P1 |
| 4 | notes_extractor.py 패턴 확인 | `notes_extractor.py` | P1 |

---

## 🟡 P1: 연관 서비스 확장 필요

### 2. 고객-모델 매핑 연동

**현재 상태**:
- `customer_config.py`: 8개 고객 프로파일 (PANASIA, HANJIN 추가)
- `classes_panasia.txt`: PANASIA용 YOLO 클래스 정의 (28개)
- `model_registry.yaml`: Panasia 모델 등록됨

**누락된 연동**:

| 항목 | 현재 | 필요 |
|------|------|------|
| 고객별 YOLO 모델 자동 선택 | ❌ | customer_id → model_type 매핑 |
| 고객별 OCR 프로파일 | 부분 | ocr_profile 활용 로직 |
| PANASIA 가격표 | ❌ | price_database.py에 PANASIA 가격 추가 |

**작업 항목**:

| # | 작업 | 파일 | 우선순위 |
|---|------|------|----------|
| 1 | CUSTOMER_TO_MODEL_MAP 추가 | `detection_router.py` 또는 `customer_config.py` | P1 |
| 2 | PANASIA 가격 데이터 추가 | `price_database.py` | P1 |
| 3 | 고객별 모델 선택 API | `dsebearing_router.py` | P2 |

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

## 🟢 P2: Phase 2 아키텍처 확산

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

**향후 작업**:

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 1 | Gateway에서 Template 기반 실행 | 템플릿 ID로 파이프라인 실행 | P2 |
| 2 | 고객별 기본 템플릿 설정 | customer_config에 default_template 추가 | P2 |
| 3 | 템플릿 버전 관리 | 템플릿 히스토리 및 롤백 | P3 |

---

## 📋 작업 체크리스트

### 즉시 수행 (P0)

- [ ] `dimension_service.py` 패턴 동기화
  - [ ] 직경+공차 복합 패턴 3개 추가
  - [ ] 역순 비대칭 패턴 추가
  - [ ] 단방향 공차 패턴 2개 추가
  - [ ] 나사/각도/표면거칠기 패턴 추가
  - [ ] 테스트 케이스 작성

### 단기 (P1)

- [ ] PANASIA 가격 데이터 추가
- [ ] 고객별 YOLO 모델 자동 선택
- [ ] notes_extractor.py 패턴 검토

### 중기 (P2)

- [ ] web-ui Export 옵션 추가
- [ ] Gateway Template 기반 실행
- [ ] 고객별 기본 템플릿

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
| TBD | dimension_service.py 동기화 | ⏳ 대기 |
| TBD | PANASIA 가격 데이터 | ⏳ 대기 |

---

*이 문서는 부분적 변경이 다른 서비스에 미치는 영향을 추적합니다.*
*새로운 패턴이 추가되면 이 문서를 업데이트하세요.*
