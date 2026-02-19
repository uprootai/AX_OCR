# 진행 중인 작업

> **마지막 업데이트**: 2026-02-19
> **기준 커밋**: e488072 (docs: Agent-Native Verification UI 기획 문서 추가)

---

## 2026-02-19 완료 작업

### Agent-Native Verification UI (Phase 1+2) ✅
- **백엔드**: `CropService` (PIL 크롭/컨텍스트/참조 이미지) + `agent_verification_router` (3 엔드포인트)
- **프론트엔드**: `AgentVerificationPage.tsx` (standalone 라우트 `/verification/agent`)
- **신규 파일**: `crop_service.py` (141줄), `agent_verification_router.py` (242줄), `AgentVerificationPage.tsx` (411줄)
- **수정 파일**: `api_server.py` (+4줄), `App.tsx` (+2줄), `pages/index.ts` (+1줄)
- **Agent-Friendly**: `data-action` 속성, `id` 속성, 키보드 단축키 (A/R/S/←→), 고정 레이아웃
- **검증**: Python ast ✅, tsc --noEmit ✅, npm run build ✅

---

## 2026-02-14 완료 작업

### 동서기연 터빈 베어링 납품 패키지 생성 ✅
- **패키지**: `blueprint-ai-bom/exports/dsebearing-delivery/` (4.5GB)
- **내용**: Docker 이미지 2개 + 프로젝트 JSON + 설치 스크립트 (Linux/Windows)
- **테스트**: 클린 환경 포트 변경(5030/3010) → Import 53세션 성공, BOM 326개 확인
- **수정**: Import API multipart/form-data 방식 반영, docker-compose version 제거
- **체크섬**: CHECKSUMS.sha256 생성

### Self-contained Export에 프로젝트 데이터 + GT 라벨 포함 ✅
- **문제**: 외부 환경에서 Import 시 `project_id=None`이 되어 GT 비교 섹션 미표시
- **수정 파일**: 4개
  - `session_io_router.py`: import 엔드포인트에 `project_id` 파라미터 추가
  - `self_contained_export_service.py`: 패키지에 `project.json` + `gt_labels/` + `gt_reference/` 포함
  - `export_script_generator.py`: import 스크립트 5단계 → 8단계 확장 (프로젝트 복원, GT 주입, 세션 연결)
  - `api_server.py`: `project_service`를 `set_export_services()`에 전달 누락 수정
- **결과**: Import 후 GT 비교 정상 표시 (F1: 96.2%, Precision: 96.2%, Recall: 96.2%)
- **검증**: Playwright E2E ✅

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **프로젝트** | 동서기연 터빈 베어링 (a444211b) |
| **배치 분석** | 53/53 세션 완료 (100%) |
| **총 치수 추출** | 2,710개 (평균 51.1개/세션) |
| **어셈블리 그룹** | 7개 (T3~T8 + THRUST) |
| **빌드 상태** | ✅ 정상 |

---

## 2026-02-07 완료 작업

### 16. 1000줄 초과 파일 4개 리팩토링 ✅
- **대상**: 4개 파일 (총 5,817줄 → 16개 파일, 모두 600줄 이하)
- **Step 1**: `self_contained_export_service.py` 1304→550줄 + 모듈 2개
- **Step 2**: `analysisNodes.ts` 2019→17줄 (배럴) + 도메인 파일 4개
- **Step 3**: `api.ts` 1397→7줄 (배럴) + 모듈 4개
- **Step 4**: `ExecutionStatusPanel.tsx` 1097→171줄 + 컴포넌트 2개
- **검증**: py_compile ✅, tsc --noEmit ✅, npm run build ✅
- **패턴**: 배럴 re-export로 기존 import 경로 100% 유지

### 14. 프로젝트 관리 UI 재설계 ✅
- **계획 문서**: `.todo/2026-02-06_PROJECT_UI_REDESIGN.md`
- **11개 파일** 네이티브 재작성 (다크모드 지원)
- **390개** `dark:` 클래스 적용
- Phase 1-6 모두 완료
- 빌드 성공

### 15. Docker 네트워크 연결 수정 ✅
- **문제**: gateway-api → blueprint-ai-bom-backend 연결 불가
- **원인**: 컨테이너가 다른 Docker 네트워크에 있음
- **수정**: `docker network connect ax_poc_network blueprint-ai-bom-backend`
- **결과**: BlueprintFlow AI BOM 노드 정상 작동

---

## 2026-02-06 완료 작업

### 5. PDF/Excel 어셈블리 견적서 ✅
- **백엔드**: `quotation_service.py` - `export_assembly_pdf()`, `export_assembly_excel()`
- **라우터**: `project_router.py` - `/quotation/assembly/{assembly_dwg}/download`
- **프론트**: `AssemblyBreakdown.tsx` - PDF/Excel 다운로드 버튼 추가
- **결과**: 어셈블리 단위 견적서 내보내기 가능

### 6. E1 - Table Detector OCR 품질 개선 ✅ (기존 구현 확인)
- **파일**: `table_service.py`, `core_router.py`
- **기능**: `enable_cell_reocr=True`, `enable_crop_upscale=True` (기본 활성화)
- **사전 교정**: `_OCR_CORRECTIONS` 70+ 항목

### 7. E2 - 표제란 자동 OCR ✅ (기존 구현 확인)
- **파일**: `core_router.py:399-489`
- **기능**: `extract_text_regions()` 자동 실행, `title_block_ocr` feature 지원

### 8. dimension_service 다중 엔진 ✅ (기존 구현 확인)
- **파일**: `dimension_service.py`
- **지원 엔진**: paddleocr, edocr2, easyocr, trocr, suryaocr, doctr (6개)
- **가중 투표**: `_merge_multi_engine()` 구현

### 9. 패턴 확산 작업 ✅
- **P0 Excel Export 잔여 참조**: 없음 (FileSpreadsheet는 일반 아이콘)
- **P1-1 _safe_to_gray()**: `edgnet-api/thinning.py` 수정 완료
  - `line-detector-api/`는 이미 적용됨

### 10. BOMHierarchyTree 리비전 표시 ✅
- **파일**: `BOMHierarchyTree.tsx`
- **변경**: `doc_revision` 필드 추가, 보라색 `Rev.X` 뱃지로 표시

### 11. 단가 API 확장 ✅ (기존 구현 확인)
- **파일**: `bom_router.py:166-222`
- **GET /bom/{session_id}/pricing**: 단가 파일 조회
- **DELETE /bom/{session_id}/pricing**: 단가 파일 삭제 (글로벌 복원)

### 12. R&D 문서 업데이트 ✅
- **README.md**: 시스템 현황 추가 (21 API, 549 테스트, 29 노드)
- **SOTA_GAP_ANALYSIS.md**: OCR 6엔진 앙상블, PID2Graph 완료 반영
- **SOTA 부합도**: ~82% 유지 (P&ID 60% → 65% 개선)

### 13. 향후 기능 구현 ✅
- **NOTES 텍스트 추출**: 이미 구현됨 (`notes_extractor.py`, `longterm_router.py`)
- **뷰 라벨 인식**: 신규 구현 (`view_label_extractor.py`)
  - SECTION A-A, DETAIL B, VIEW C-C, 정면도/측면도 등 파싱
  - API: `POST/GET /longterm/view-labels/{session_id}`
- **DocLayout-YOLO Fine-tuning**: 준비 완료 (8클래스, 29이미지, 라벨링 필요)
- **YOLOv12 업그레이드 계획**: 문서화 완료 (`YOLOV12_UPGRADE_PLAN.md`)

---

## 이전 완료 작업 (2026-02-05~06)

### 1. eDOCr2 타임아웃 증가 ✅
- `timeout=120.0` → `timeout=600.0`

### 2. 대용량 이미지 자동 리사이즈 ✅
- MAX_DIMENSION=8000, MAX_PIXELS=64M

### 3. 어셈블리 단위 세션 관리 ✅
- 스키마, 서비스, UI 컴포넌트

### 4. 배치 분석 어셈블리 단위 실행 UI ✅
- `currentBatchDrawing`, `isAnalyzing` props

---

## 2026-02-06 P3 작업 완료

### 완료된 P3 작업 (11/11) ✅

| 작업 | 설명 | 파일 |
|------|------|------|
| ✅ P3-1 | Executor API 재시도/타임아웃 표준화 | `APICallerMixin` in `base_executor.py` |
| ✅ P3-2 | Docker GPU 자동 감지 | `scripts/docker-gpu-entrypoint.sh` |
| ✅ P3-3 | 가중 투표 공통 라이브러리 | `gateway-api/common/weighted_voting.py` |
| ✅ P3-4 | 제네릭 OverlayViewer | `GenericOverlayViewer.tsx` |
| ✅ P3-5 | useCanvasDrawing 훅 확장 | `drawBoundingBoxes`, `drawLine` 등 추가 |
| ✅ P3-6 | 크롭 영역 미리보기 도구 | `CropRegionPreview.tsx` |
| ✅ P3-7 | Blueprint AI BOM SVG 연동 | `BOMSessionOverlay.tsx` |
| ✅ P3-8 | 시각화 기능 확장 (공차 히트맵, BOM 연결선) | `ToleranceHeatmap.tsx`, `BOMConnectionLines.tsx` |
| ✅ P3-9 | 템플릿 버전 관리 | `template_service.py`, `TemplateVersionHistory.tsx` |
| ✅ P3-10 | Gateway 서비스 분리 | 기존 완료 (vl-api:5004, ocr-ensemble-api:5011) |
| ✅ P3-11 | QuotePreview i18n | 기존 완료 확인 |

**P1/P2/P3 모든 작업 완료** - 100% 진행

---

## 검증 결과

| 항목 | 결과 |
|------|------|
| **Python 컴파일** | ✅ 전체 정상 |
| **TypeScript 빌드** | ✅ 에러 0개 |
| **Frontend 빌드** | ✅ 성공 |
| **Docker 배포** | ✅ 정상 |
| **배치 분석** | ✅ 53/53 완료 (100%) |

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| 패턴 확산 작업 | `.todo/PENDING_PATTERN_PROPAGATION.md` |
| 백로그 | `.todo/BACKLOG.md` |
| 완료 아카이브 | `.todo/COMPLETED.md` |

---

*마지막 업데이트: 2026-02-07 (1000줄 초과 파일 리팩토링 완료)*
