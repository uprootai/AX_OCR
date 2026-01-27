# 미커밋 변경사항 및 동기화 필요 항목

> **생성일**: 2026-01-27
> **마지막 커밋**: bfcadb6 (feat: Blueprint AI BOM Phase 2 완료 및 Self-contained Export 강화)
> **변경 파일**: 37개 (+3,494줄 / -656줄)

---

## 1. 핵심 변경 요약

| # | 변경 | 파일 | 영향도 |
|---|------|------|--------|
| 1 | **confidence_threshold 0.5→0.4** | `schemas/analysis_options.py` | 🔴 높음 |
| 2 | **Dimension Parser 21패턴 동기화** | `services/dimension_service.py` | 🟡 중간 |
| 3 | **GT 비교 시각화 (TP/FP/FN 통합)** | `DetectionResultsSection.tsx` | 🟢 낮음 |
| 4 | **고객-모델 자동 매핑** | `customer_config.py` | 🟡 중간 |
| 5 | **PANASIA BWMS 가격 데이터** | `price_database.py` | 🟢 낮음 |
| 6 | **템플릿 기반 워크플로우 실행** | `workflow_router.py` | 🟡 중간 |
| 7 | **참조 도면 세트 관리 API** | `reference_router.py` (신규) | 🟢 낮음 |
| 8 | **Self-contained Export 강화** | `self_contained_export_service.py` | 🟢 낮음 |
| 9 | **BOM 노드 features 파라미터 제거** | `bomNodes.ts` | 🟢 낮음 |

---

## 2. 동기화 필요 항목 (다른 노드/서비스에 적용)

### 2.1 confidence_threshold 일관성 검토 🔴

**변경 내용**: Blueprint AI BOM의 기본 confidence가 0.5에서 0.4로 변경됨 (drawing-bom-extractor와 동일화)

**영향받는 파일**:
```
blueprint-ai-bom/backend/schemas/analysis_options.py  ✅ 완료 (0.4)
```

**검토 필요 파일**:
| 파일 | 현재 값 | 권장 값 | 상태 |
|------|---------|---------|------|
| `gateway-api/blueprintflow/executors/yolo_executor.py` | ? | 0.4 | ⏳ 확인 필요 |
| `models/yolo-api/config.py` | ? | 0.4 | ⏳ 확인 필요 |
| `web-ui/src/config/nodes/detectionNodes.ts` (YOLO default) | ? | 0.4 | ⏳ 확인 필요 |

**작업**:
```bash
# 1. YOLO executor 기본값 확인
grep -r "confidence" gateway-api/blueprintflow/executors/yolo_executor.py

# 2. YOLO API 기본값 확인
grep -r "confidence" models/yolo-api/

# 3. 노드 정의 기본값 확인
grep -r "confidence" web-ui/src/config/nodes/
```

---

### 2.2 Dimension Parser 패턴 동기화 🟡

**변경 내용**: `dimension_service.py`에 21개 복합 치수 패턴 추가 (gateway dimensionparser_executor.py와 동기화)

**동기화 완료**:
```
gateway-api/blueprintflow/executors/dimensionparser_executor.py  ✅ 소스 (21개 패턴)
blueprint-ai-bom/backend/services/dimension_service.py           ✅ 동기화됨
```

**추가된 패턴**:
| 패턴 | 예시 | DimensionType |
|------|------|---------------|
| 직경+대칭공차 | Φ50±0.05 | DIAMETER |
| 직경+비대칭공차 | Φ50+0.05/-0.02 | DIAMETER |
| 직경+역순공차 | Φ50-0.02+0.05 | DIAMETER |
| 직경+공차등급 | Ø50H7 | DIAMETER |
| 나사 | M10×1.5 | THREAD |
| 챔퍼 | C2×45° | CHAMFER |

**검토 필요**:
| 서비스 | 파일 | 상태 |
|--------|------|------|
| eDOCr2 API | `models/edocr2-v2-api/dimension_parser.py` | ⏳ 확인 필요 |
| OCR Ensemble | `models/ocr-ensemble-api/` | ⏳ 확인 필요 |

---

### 2.3 고객-모델 매핑 시스템 🟡

**변경 내용**: `customer_config.py`에 고객별/도면타입별 YOLO 모델 자동 선택 로직 추가

**새로운 매핑**:
```python
CUSTOMER_TO_MODEL_MAP = {
    "PANASIA": "pid_symbol",      # P&ID 도면
    "STX": "pid_symbol",
    "KEPCO": "bom_detector",      # 전력 단선도
    "DSE": "engineering",         # 기계도면
    "DOOSAN": "engineering",
}

DRAWING_TYPE_TO_MODEL_MAP = {
    "pid": "pid_symbol",
    "sld": "bom_detector",
    "mechanical": "engineering",
    "mcp": "panasia",
}
```

**적용 필요**:
| 위치 | 상태 | 설명 |
|------|------|------|
| `gateway-api/routers/workflow_router.py` | ✅ 사용 가능 | `get_model_for_customer()` 호출 |
| `blueprint-ai-bom/backend/services/detection_service.py` | ⏳ 적용 필요 | 고객 ID로 모델 자동 선택 |
| `web-ui BlueprintFlow` | ⏳ 적용 필요 | 고객 선택 시 모델 자동 설정 |

---

### 2.4 템플릿 기반 실행 엔드포인트 🟡

**새로운 Gateway 엔드포인트**:
```
GET  /api/v1/workflow/templates              # 템플릿 목록
GET  /api/v1/workflow/templates/{id}         # 템플릿 상세
POST /api/v1/workflow/execute-template/{id}  # 템플릿 실행
POST /api/v1/workflow/execute-template-stream/{id}  # SSE 스트리밍
```

**내장 폴백 템플릿** (BOM API 연결 실패 시):
- `yolo-detection`: YOLO 객체 검출
- `ocr-extraction`: eDOCr2 텍스트 추출
- `full-analysis`: YOLO + OCR + 공차 분석

**프론트엔드 적용 필요**:
| 파일 | 상태 | 작업 |
|------|------|------|
| `web-ui/src/lib/api.ts` | ⏳ | 템플릿 API 호출 함수 추가 |
| `BlueprintFlowTemplates.tsx` | ⏳ | Gateway 템플릿 목록 연동 |

---

## 3. 신규 파일

### 3.1 reference_router.py (참조 도면 세트 관리)

**위치**: `blueprint-ai-bom/backend/routers/reference_router.py`

**엔드포인트**:
```
GET    /reference-sets                    # 세트 목록
POST   /reference-sets                    # 세트 생성
GET    /reference-sets/{id}               # 세트 상세
PUT    /reference-sets/{id}               # 세트 수정
DELETE /reference-sets/{id}               # 세트 삭제
POST   /reference-sets/{id}/images        # 이미지 추가
DELETE /reference-sets/{id}/images/{img}  # 이미지 삭제
```

**등록 필요**:
```python
# api_server.py에 등록
from routers.reference_router import router as reference_router
app.include_router(reference_router)
```

### 3.2 ProfileManager.tsx & profileStore.ts

**위치**: `web-ui/src/components/blueprintflow/`

**용도**: 고객 프로파일 관리 UI (미완성)

**상태**: ⏳ 구현 필요 또는 삭제 결정

---

## 4. 변경 파일 상세

### 4.1 Backend (Blueprint AI BOM)

| 파일 | 변경 | 라인 |
|------|------|------|
| `api_server.py` | reference_router 등록 준비 | +6 |
| `schemas/analysis_options.py` | confidence 0.5→0.4 | +1/-1 |
| `schemas/dimension.py` | THREAD, CHAMFER 타입 추가 | +4/-1 |
| `services/dimension_service.py` | 21개 복합 패턴 추가 | +108 |
| `services/self_contained_export_service.py` | 프론트엔드 자동 포함 | +549 |
| `routers/session_router.py` | 이미지 관리 API | +56 |
| `routers/export_router.py` | Export 옵션 확장 | +4/-1 |

### 4.2 Frontend (Blueprint AI BOM)

| 파일 | 변경 | 라인 |
|------|------|------|
| `DetectionResultsSection.tsx` | GT 비교 통합 뷰 (TP/FP/FN) | +200 |
| `WorkflowSidebar.tsx` | 이미지 관리, 참조 도면 | +1205 |
| `WorkflowPage.tsx` | 이미지 핸들러 | +83 |
| `sessionStore.ts` | 이미지 관련 상태 | +30 |
| `types/index.ts` | GT 비교 타입 | +6 |

### 4.3 Gateway API

| 파일 | 변경 | 라인 |
|------|------|------|
| `workflow_router.py` | 템플릿 기반 실행 | +457 |
| `customer_config.py` | 고객-모델 매핑 | +77 |
| `price_database.py` | BWMS 재질/가공비 | +191 |

### 4.4 Web-UI

| 파일 | 변경 | 라인 |
|------|------|------|
| `bomNodes.ts` | features 파라미터 제거 | +22/-22 |
| `api.ts` | API 확장 | +274 |
| `NodeDetailPanel.tsx` | 상세 패널 개선 | +80 |
| Guide 섹션들 | 문서 업데이트 | ~200 |

---

## 5. 커밋 전 체크리스트

### 5.1 빌드 확인
```bash
# Frontend 빌드
cd blueprint-ai-bom/frontend && npm run build

# Web-UI 빌드
cd web-ui && npm run build

# Gateway 테스트
cd gateway-api && pytest tests/ -v
```

### 5.2 린트 확인
```bash
cd web-ui && npm run lint
cd blueprint-ai-bom/frontend && npm run lint
```

### 5.3 Docker 재빌드
```bash
# Blueprint AI BOM
cd blueprint-ai-bom && docker-compose build

# 전체 서비스
docker-compose build
```

---

## 6. 향후 작업 (Optional)

| 우선순위 | 작업 | 설명 |
|----------|------|------|
| P3 | confidence 일관성 전파 | 모든 YOLO 호출에 0.4 기본값 적용 |
| P3 | 고객-모델 매핑 UI | BlueprintFlow에서 고객 선택 → 모델 자동 선택 |
| P3 | ProfileManager 완성 | 고객 프로파일 관리 UI |
| P3 | 템플릿 프론트엔드 연동 | Gateway 템플릿 API를 BlueprintFlow에서 사용 |

---

## 7. 참조

### 관련 문서
- `.todo/ACTIVE.md` - 현재 작업 상태
- `.todo/SYNC_PATTERNS.md` - Dimension Parser 패턴 상세
- `.todo/archive/BLUEPRINT_ARCHITECTURE_V2.md` - Phase 2 아키텍처

### 마지막 커밋 정보
```
commit bfcadb6
feat: Blueprint AI BOM Phase 2 완료 및 Self-contained Export 강화

- Phase 2A~2I 완료
- Self-contained Export에 프론트엔드 자동 포함
- 포트 오프셋 기능 (offset=10000)
```

---

*생성: Claude Code (Opus 4.5) | 2026-01-27*
