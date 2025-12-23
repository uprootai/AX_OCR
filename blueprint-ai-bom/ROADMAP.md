# Blueprint AI BOM - 구현 로드맵

> **목표**: Streamlit → React + FastAPI 전환
> **상태**: ✅ 완료 (2025-12-23)

---

## 구현 상태 요약

| Phase | 내용 | 상태 | 완료일 |
|-------|------|------|--------|
| Phase 1 | 백엔드 API 분리 | ✅ 완료 | 2025-12-14 |
| Phase 2 | React 프론트엔드 | ✅ 완료 | 2025-12-16 |
| Phase 3 | 통합 및 테스트 | ✅ 완료 | 2025-12-19 |
| Phase 4 | GD&T 파서 | ✅ 완료 | 2025-12-19 |
| Phase 5 | 치수-심볼 관계 | ✅ 완료 | 2025-12-19 |
| Phase 6 | Active Learning | ✅ 완료 | 2025-12-23 |
| Phase 7 | TypedDict 타입 안전성 | ✅ 완료 | 2025-12-23 |

---

## Phase 1: 백엔드 API 분리 ✅

### 완료된 작업

- [x] `backend/` 디렉토리 구조 생성
- [x] `backend/requirements.txt` 작성
- [x] `backend/api_server.py` FastAPI 앱
- [x] 검출 서비스 분리 (`detection_service.py`)
- [x] BOM 서비스 분리 (`bom_service.py`)
- [x] 세션 서비스 (`session_service.py`)

### 생성된 파일

```
backend/
├── api_server.py
├── services/
│   ├── detection_service.py
│   ├── bom_service.py
│   └── session_service.py
├── routers/
│   ├── detection_router.py
│   ├── bom_router.py
│   └── session_router.py
└── schemas/
    ├── detection.py
    ├── bom.py
    └── session.py
```

---

## Phase 2: React 프론트엔드 ✅

### 완료된 작업

- [x] Vite + React 19 + TypeScript 프로젝트
- [x] TailwindCSS v4 설정
- [x] 라우팅 (react-router-dom)
- [x] API 클라이언트 (axios)
- [x] Zustand 스토어
- [x] 이미지 뷰어 (DrawingCanvas)
- [x] 바운딩 박스 오버레이
- [x] 검출 목록 UI
- [x] BOM 테이블
- [x] Export 버튼 (Excel/CSV/JSON/PDF)

### 생성된 파일

```
frontend/src/
├── pages/
│   ├── HomePage.tsx
│   ├── DetectionPage.tsx
│   ├── VerificationPage.tsx
│   ├── WorkflowPage.tsx
│   └── BOMPage.tsx
├── components/
│   ├── DrawingCanvas.tsx
│   ├── DetectionCard.tsx
│   ├── VerificationQueue.tsx
│   └── bom/
└── lib/
    └── api.ts
```

---

## Phase 3: 통합 및 테스트 ✅

### 완료된 작업

- [x] 프론트엔드 ↔ 백엔드 API 연동
- [x] 파일 업로드 플로우
- [x] 검출 → 검증 → BOM 전체 플로우
- [x] Docker 패키징
- [x] 단위 테스트 (27개)

---

## Phase 4: GD&T 파서 ✅

### 완료된 작업

- [x] 기하공차 심볼 파싱 (⌀, ⊥, ∥, ⊙, ⌖)
- [x] 데이텀 검출 (A, B, C)
- [x] 공차값 추출
- [x] `gdt_parser.py` 서비스
- [x] `gdt.py` 스키마
- [x] `GDTEditor.tsx` UI 컴포넌트

---

## Phase 5: 치수-심볼 관계 ✅

### 완료된 작업

- [x] `dimension_relation_service.py`
- [x] `relation.py` 스키마
- [x] `relation_router.py` API
- [x] `RelationOverlay.tsx` UI
- [x] `RelationList.tsx` 목록

---

## Phase 6: Active Learning ✅

### 완료된 작업

- [x] `active_learning_service.py`
- [x] `verification_router.py` API
- [x] `VerificationQueue.tsx` UI
- [x] 우선순위 분류 (CRITICAL/HIGH/MEDIUM/LOW)
- [x] 자동 승인 (신뢰도 ≥ 0.9)
- [x] 일괄 승인 기능
- [x] 검증 로그 저장 (재학습용)

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/verification/queue/{id}` | 검증 큐 조회 |
| GET | `/verification/stats/{id}` | 검증 통계 |
| POST | `/verification/verify/{id}` | 단일 검증 |
| POST | `/verification/auto-approve/{id}` | 자동 승인 |
| POST | `/verification/bulk-approve/{id}` | 일괄 승인 |
| GET | `/verification/training-data` | 재학습 데이터 |

---

## Phase 7: TypedDict 타입 안전성 ✅

### 완료된 작업

- [x] `typed_dicts.py` (16개 타입 정의)
- [x] 5개 서비스에 TypedDict 적용
- [x] `Dict[str, Any]` → 구체적 타입 변환
- [x] 단위 테스트 추가

### 정의된 타입

```python
# schemas/typed_dicts.py
- PricingInfo
- BBoxDict
- DetectionDict
- DimensionDict
- SymbolDict
- LineDict
- RelationDict
- SessionData
- BOMItemDict
- BOMSummaryDict
- ...
```

---

## 향후 계획

### 🟡 중간 우선순위

| 항목 | 설명 |
|------|------|
| VLM 자동 분류 | GPT-4V/Claude로 도면 타입 분류 |
| 온프레미스 테스트 | 고객사 환경 검증 |

### 🟢 낮은 우선순위

| 항목 | 설명 |
|------|------|
| GNN 관계 분석 | 그래프 신경망 부품 관계 학습 |
| 피드백 루프 | Active Learning 로그 → 모델 재학습 |

---

## 레거시 코드 매핑

| Streamlit | React | 비고 |
|-----------|-------|------|
| `st.file_uploader` | `HomePage` | react-dropzone |
| `st.image` | `DrawingCanvas` | SVG 기반 |
| `st_drawable_canvas` | `IntegratedOverlay` | 직접 구현 |
| `st.dataframe` | `BOMTable` | 직접 구현 |
| `st.download_button` | `ExportButtons` | Blob + anchor |

---

## 테스트 현황

| 카테고리 | 테스트 수 | 상태 |
|----------|----------|------|
| BOM Service | 9개 | ✅ 통과 |
| Detection Service | 7개 | ✅ 통과 |
| Pricing Utils | 11개 | ✅ 통과 |
| **총계** | **27개** | **✅ 통과** |

---

**완료일**: 2025-12-23
**버전**: v5.0
