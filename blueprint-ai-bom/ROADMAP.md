# Blueprint AI BOM - 구현 로드맵

> **목표**: Streamlit → React + FastAPI 전환 + 장기 로드맵 기능 완성
> **상태**: ✅ 완료 (v10.3 - 2025-12-27)

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
| **Phase 8** | **장기 로드맵 기능** | **✅ 완료** | **2025-12-27** |

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

## Phase 8: 장기 로드맵 기능 ✅

> **버전**: v10.0 ~ v10.3
> **완료일**: 2025-12-27

### 완료된 작업

- [x] **🤖 VLM 자동 분류** (v10.0)
  - GPT-4o-mini 기본, OpenAI/Anthropic/로컬 멀티 프로바이더
  - 도면 타입, 산업 분야, 복잡도 AI 분류
  - 기능 자동 추천
  - `vlm_classifier.py` 서비스

- [x] **📋 노트 추출** (v10.1)
  - GPT-4o-mini LLM + 정규식 폴백
  - 10개 카테고리 자동 분류 (재료, 열처리, 표면처리 등)
  - `notes_extractor.py` 서비스

- [x] **🗺️ 영역 세분화** (v10.2)
  - 휴리스틱 + VLM 하이브리드 방식
  - 11개 영역 타입 자동 검출
  - `region_segmenter.py` 서비스

- [x] **🔄 리비전 비교** (v10.3)
  - SSIM 이미지 비교 (OpenCV)
  - 세션 데이터 비교 (심볼, 치수, 노트)
  - VLM 지능형 비교 (선택)
  - `revision_comparator.py` 서비스

### API 엔드포인트 (longterm_router.py)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/analysis/vlm-classify/{id}` | VLM 분류 |
| GET | `/analysis/vlm-classify/{id}` | 분류 결과 조회 |
| POST | `/analysis/notes/{id}/extract` | 노트 추출 |
| GET | `/analysis/notes/{id}` | 노트 결과 조회 |
| POST | `/analysis/drawing-regions/{id}/segment` | 영역 세분화 |
| GET | `/analysis/drawing-regions/{id}` | 영역 결과 조회 |
| POST | `/analysis/revision/compare` | 리비전 비교 |
| GET | `/analysis/revision/{id}` | 비교 결과 조회 |

### 생성된 파일

```
backend/
├── services/
│   ├── vlm_classifier.py      # VLM 분류 (멀티 프로바이더)
│   ├── notes_extractor.py     # 노트 추출 (LLM + 정규식)
│   ├── region_segmenter.py    # 영역 세분화 (휴리스틱 + VLM)
│   └── revision_comparator.py # 리비전 비교 (SSIM + 데이터 + VLM)
├── routers/
│   └── longterm_router.py     # 장기 로드맵 API
├── schemas/
│   └── longterm.py            # 장기 로드맵 스키마
└── tests/
    ├── test_revision_comparator.py  # 단위 테스트 (19개)
    └── test_longterm_api.py         # API 테스트 (13개)
```

---

## 향후 계획

### 🟢 낮은 우선순위 (선택)

| 항목 | 설명 | 상태 |
|------|------|------|
| GNN 관계 분석 | 그래프 신경망 부품 관계 학습 | 미정 |
| 온프레미스 테스트 | 고객사 환경 검증 | 대기 |
| 모델 재학습 자동화 | Feedback Loop → YOLO 자동 재학습 | 대기 |

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
| Revision Comparator | 19개 | ✅ 통과 |
| Longterm API | 13개 | ✅ 통과 |
| **총계** | **59개** | **✅ 통과** |

---

**최초 완료일**: 2025-12-23 (v5.0)
**장기 로드맵 완료일**: 2025-12-27 (v10.3)
