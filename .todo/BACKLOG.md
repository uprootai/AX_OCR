# 백로그 (향후 작업)

> 마지막 업데이트: 2026-02-06
> 미래 작업 및 참조 문서

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **동서기연 배치 분석** | 53/53 세션 완료 (100%) |
| **총 치수 추출** | 2,710개 (평균 51.1개/세션) |
| **빌드** | ✅ 정상 |
| **ESLint** | 0 errors |
| **노드 정의** | 29개 (Excel Export 제거) |
| **API 서비스** | 21개 |

---

## P1: 패턴 확산 작업 (2026-02-01 기준)

> 상세: `.todo/PENDING_PATTERN_PROPAGATION.md`

### ~~P1-1. _safe_to_gray() 다른 OCR API 적용~~ ✅ 완료 (2026-02-06)

- eDOCr2, Line Detector, EDGNet에 `_safe_to_gray()` 적용 완료
- 기타 OCR API는 라이브러리 내부 처리

### ~~P1-2. Excel Export 잔여 참조 정리~~ ✅ 완료 (2026-02-06)

- FileSpreadsheet 참조는 Lucide 아이콘 (정상 사용)
- `excelexport` 노드 참조 없음 확인됨

### ~~P1-3. Executor API 호출 메서드 분리~~ ✅ 완료 (2026-02-03)

| # | Executor | 상태 |
|---|----------|------|
| 1 | `bom_executor.py` | ✅ `_call_api()`, `_post_api()`, `_patch_api()` 분리 완료 |
| 2 | `pdfexport_executor.py` | ✅ `_post_api()` 분리 완료 |
| 3 | `pidfeatures_executor.py` | ✅ `_post_api()` 분리 완료 |

---

## P1: 기존 작업 (2026-01-30 이전)

### ~~P1-4. BOM 프론트엔드 세션 단가 표시~~ ✅ 완료 (2026-02-03)

| # | 작업 | 상태 |
|---|------|------|
| 1 | 세션 조회 시 `has_custom_pricing` 반환 | ✅ `session_router.py` |
| 2 | BOM 헤더에 "커스텀 단가" 배지 | ✅ `BOMSection.tsx` |
| 3 | types/index.ts에 필드 추가 | ✅ 완료 |

### ~~P1-5. DetectionResultsSection 클래스 하이라이트~~ ✅ 완료 (2026-02-03)

| # | 작업 | 상태 |
|---|------|------|
| 1 | `selectedClassName` state 추가 | ✅ 완료 |
| 2 | 클래스 목록 클릭 핸들러 (필터 UI) | ✅ 완료 |
| 3 | Canvas 렌더링에 선택 상태 반영 (opacity/lineWidth) | ✅ 완료 |

### ~~P1-6. data.yaml 방식 표준화 검토~~ ✅ 완료 (2026-02-06)

- 6개 모델 모두 `class_names` 보유 확인
- `panasia` 모델에 `data_yaml: panasia_data.yaml` 이미 설정됨
- `registry.py`에서 data_yaml → model.names 오버라이드 로직 구현됨

### ~~P1-7. Docker 빌드 panasia_data.yaml 확인~~ ✅ 완료 (2026-02-06)

- `Dockerfile:25` - `COPY models/ ./models/` 로 전체 복사
- `panasia_data.yaml`, `model_registry.yaml` 포함됨
- `.dockerignore` 없음 (yaml 제외 없음)

---

## P2: 중기 작업

### ~~P2-0. 치수 전용 워크플로우 일반 텍스트 OCR 강화~~ ✅ 대부분 완료 (2026-02-06)

**구현 완료**:
- ✅ **표제란 OCR 자동 실행**: `title_block_ocr` feature 지원 (`core_router.py:399-489`)
- ✅ **Table Detector OCR 후처리**: `enable_cell_reocr=True`, `enable_crop_upscale=True` 기본 활성화
- ✅ **사전 교정 사전**: `_OCR_CORRECTIONS` 70+ 항목

**추가 구현 완료 (2026-02-06)**:
- ✅ NOTES 텍스트 추출: `notes_extractor.py`, `longterm_router.py`
- ✅ 뷰 라벨 인식: `view_label_extractor.py`, `longterm_router.py`

---

### ~~P2-1. 단가 API 확장 (GET/DELETE)~~ ✅ 완료 (기존 구현 확인 2026-02-06)

- `GET /bom/{session_id}/pricing` - 단가 파일 조회
- `DELETE /bom/{session_id}/pricing` - 단가 파일 삭제 (글로벌 복원)
- 파일: `bom_router.py:166-222`

### ~~P2-2. BOM 테이블 ↔ 도면 하이라이트 연동~~ ✅ 완료 (2026-02-03)

```
BOMSection.tsx → onClassSelect callback
  → WorkflowPage.tsx → bomHighlightClass state lift
  → FinalResultsSection.tsx → selectedClassName/onClassSelect props
```
양방향 연동: BOM 테이블 클릭 ↔ 도면 하이라이트 동기화

### ~~P2-3. SAHI 모드 data.yaml class_names 호환~~ ✅ 완료 (2026-02-06)

- `sahi_inference.py`에 `class_names` 파라미터 추가
- `detection_router.py`에서 model_registry의 class_names를 SAHI에 전달
- class_id → class_name 매핑이 data_yaml 오버라이드 지원

### ~~P2-4. dimension_service 다른 OCR 엔진 통합~~ ✅ 완료 (2026-02-06)

- 6개 엔진 지원: paddleocr, edocr2, easyocr, trocr, suryaocr, doctr
- 가중 투표: `_merge_multi_engine()` 구현
- 파일: `dimension_service.py`

### ~~P2-5. CLAUDE.md 노드/파라미터 목록 갱신~~ ✅ 완료 (2026-02-06)

- 노드 수: 29개 (기존 정확)
- BOM `features` 파라미터 문서화 완료

---

## 고려 사항

### Claude Code Agent Teams 도입 검토

- **기능**: 여러 Claude Code 인스턴스를 리더+팀원 구조로 병렬 협업 (실험적 기능)
- **현재 판단**: 지금은 불필요 — subagent 방식으로 충분
- **도입 시점**: 프로덕션 전환 대규모 리팩토링, 신규 기업 3~4개 동시 온보딩, 프론트/백엔드/AI 동시 대규모 변경 시
- **참고**: https://code.claude.com/docs/ko/agent-teams

---

## P3: 장기 작업

### 완료된 P3 작업 (2026-02-06)

| 작업 | 설명 | 파일 |
|------|------|------|
| ~~Executor API 재시도/타임아웃 표준화~~ | `APICallerMixin` 생성 | `base_executor.py`, `bom/pdfexport/pidfeatures_executor.py` |
| ~~Docker GPU 자동 감지~~ | 엔트리포인트 스크립트 | `scripts/docker-gpu-entrypoint.sh`, `yolo-api/Dockerfile` |
| ~~가중 투표 공통 라이브러리~~ | `WeightedVoter` 클래스 | `gateway-api/common/weighted_voting.py` |
| ~~제네릭 OverlayViewer~~ | 공통 컴포넌트 | `web-ui/src/components/common/GenericOverlayViewer.tsx` |
| ~~useCanvasDrawing 훅 확장~~ | 유틸리티 추가 | `web-ui/src/hooks/useCanvasDrawing.ts` |
| ~~크롭 영역 미리보기 도구~~ | 빌더 컴포넌트 | `web-ui/src/components/common/CropRegionPreview.tsx` |
| ~~QuotePreview i18n~~ | 기존 완료 | `ko.json`, `en.json` 에 `quote.*` 키 존재 |
| ~~Blueprint AI BOM SVG 연동~~ | 세션 치수 오버레이 | `web-ui/src/components/bom/BOMSessionOverlay.tsx` |
| ~~시각화 기능 확장~~ | 공차 히트맵, BOM 연결선 | `web-ui/src/components/visualization/` |
| ~~템플릿 버전 관리~~ | 히스토리 및 롤백 | `blueprint-ai-bom/backend/`, `web-ui/src/components/templates/` |
| ~~Gateway 서비스 분리~~ | VL, Ensemble API를 별도 컨테이너로 분리 | 기존 완료 (vl-api:5004, ocr-ensemble-api:5011) |

### P3 작업 모두 완료 ✅

모든 P1/P2/P3 작업이 완료되었습니다

---

## 완료된 백로그 항목

| 작업 | 완료일 |
|------|--------|
| **NOTES 텍스트 추출** (LLM + regex 기반 추출) | 2026-02-06 |
| **뷰 라벨 인식** (SECTION, DETAIL, VIEW 등 파싱) | 2026-02-06 |
| **P2-5 CLAUDE.md 노드/파라미터 목록 갱신** (BOM features 문서화) | 2026-02-06 |
| **P1-6 data.yaml 방식 표준화** (6개 모델 class_names 확인) | 2026-02-06 |
| **P1-7 Docker 빌드 확인** (panasia_data.yaml 포함) | 2026-02-06 |
| **P2-3 SAHI class_names 호환** (data_yaml 오버라이드 지원) | 2026-02-06 |
| **P2-0 일반 텍스트 OCR 강화** (표제란 자동, Table OCR 후처리) | 2026-02-06 |
| **P2-1 단가 API 확장** (GET/DELETE 엔드포인트) | 2026-02-06 |
| **P2-4 dimension_service 6개 OCR 엔진 통합** | 2026-02-06 |
| **P1-1 _safe_to_gray() 패턴 확산** (eDOCr2, Line Detector, EDGNet) | 2026-02-06 |
| **P1-2 Excel Export 잔여 참조 정리** | 2026-02-06 |
| **eDOCr2 타임아웃 600초 증가** (47.2% → 98.1% 성공률) | 2026-02-05 |
| **대용량 이미지 자동 리사이즈** (139MP 이미지 처리 가능) | 2026-02-05 |
| **어셈블리 단위 세션 관리 Step 1-3** (스키마, 서비스, UI) | 2026-02-05 |
| **동서기연 배치 분석 100%** (53/53 세션, 2,710 치수) | 2026-02-05 |
| **P1-3 Executor API 호출 메서드 분리** (bom, pdfexport, pidfeatures) | 2026-02-03 |
| **P1-4 BOM 프론트엔드 세션 단가 표시** | 2026-02-03 |
| **P1-5 DetectionResultsSection 클래스 하이라이트** | 2026-02-03 |
| **P2-2 BOM ↔ 도면 하이라이트 연동** (양방향 동기화) | 2026-02-03 |
| **DSE Bearing BOM 계층 워크플로우 Phase 1** (PDF 파싱, 도면 매칭, 세션 일괄 생성) | 2026-02-04 |
| **DSE Bearing BOM 계층 워크플로우 Phase 2** (5단계 위저드 UI, 트리뷰, 매칭 테이블) | 2026-02-04 |
| **DSE Bearing BOM 계층 워크플로우 Phase 3** (견적 집계 서비스, MaterialBreakdown, QuotationDashboard) | 2026-02-04 |
| **eDOCr2 5개 버그 수정** | 2026-02-01 |
| **BOM executor features 병합 + drawing_type 폴백** | 2026-02-01 |
| **Table Detector multi-crop + 품질 필터** | 2026-02-01 |
| **Excel Export 노드 완전 제거** | 2026-02-01 |
| **DSE Bearing 템플릿 정리 (12→6)** | 2026-02-01 |
| **DSE Bearing 6개 템플릿 aibom 파라미터 설정** | 2026-02-01 |
| **dimension_service 멀티 엔진 리팩토링** | 2026-02-01 |
| 빌더 단가 파일 업로드 | 2026-01-30 |
| YOLO data.yaml 방식 전환 | 2026-01-30 |
| FinalResults 클래스 하이라이트 | 2026-01-30 |
| DSE Bearing 100점 | 2026-01-22 |
| Blueprint AI BOM Phase 2 | 2026-01-24 |

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| **현재 작업** | `.todo/ACTIVE.md` |
| **완료 아카이브** | `.todo/COMPLETED.md` |
| **패턴 확산 작업** | `.todo/PENDING_PATTERN_PROPAGATION.md` |
| 새 API 추가 가이드 | `.claude/skills/api-creation-guide.md` |
| 모듈화 가이드 | `.claude/skills/modularization-guide.md` |

---

*마지막 업데이트: 2026-02-06 (NOTES/뷰 라벨 구현 완료)*
