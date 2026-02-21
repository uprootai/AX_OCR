# 진행 중인 작업

> **마지막 업데이트**: 2026-02-21
> **기준 커밋**: 9e7bfda (fix: Agent 검증 status 버그 수정 + dimension 검증 지원)

---

## 2026-02-21 완료 작업

### Agent Verification Pipeline (Phase 3) ✅
- **목적**: LLM Agent가 검출/OCR 결과를 자동 검증하는 Python 스크립트
- **아키텍처**: 3-Level Hybrid (L1: auto-approve, L2: Claude Sonnet vision, L3: 스텁)
- **신규 파일**:
  - `scripts/agent_verify_prompts.py` (116줄) - Symbol/Dimension 검증 프롬프트 템플릿
  - `scripts/agent_verify.py` (613줄) - AgentVerifier 클래스 + CLI
- **기능**:
  - L1: confidence >= threshold 자동 승인
  - L2: Anthropic API로 크롭/컨텍스트/참조 이미지 분석 → approve/reject/modify
  - dry-run 모드: LLM 호출만 하고 결정 전송 생략, JSON 결과 저장
  - API 키: CLI → 환경변수 → BOM API Settings 순 해결
  - 에러 처리: Rate limit backoff, 개별 item 실패 시 uncertain 분류
- **검증**: Python ast ✅, 줄수 ✅ (116 + 621, 모두 1000줄 이하)
- **E2E 테스트**: L1-only 실행 → 116/147 auto-approve 성공, 0 에러
- **L2 시각 검증 (수동)**: 147/147 전체 검증 완료
  - L1 auto-approve: 116건 (conf >= 0.9)
  - Hatching artifact reject: 26건 (UI 4 + Batch API 22)
  - L2 시각 reject: 3건 (제목란/주석 영역 텍스트 오인식)
  - L2 시각 approve: 2건 (Ø2768, 30 - 실제 치수 확인)

### Agent Verification Phase 4: P&ID/치수 전용 뷰 ✅
- **drawing_type 뱃지**: 헤더에 도면 유형 표시 (P&ID/전기/치수BOM/기계/자동)
- **Dimension linked_to 패널**: 연결된 심볼 ID 표시 + Agent 검증 배지
- **P&ID 전용 패널**: 심볼 클래스 + 클래스 ID 표시 (drawing_type=pid일 때)
- **verified_by 필드**: ItemDetail 인터페이스에 추가
- **수정 파일**: `AgentVerificationPage.tsx` (535→588줄)
- **검증**: tsc ✅, npm run build ✅, Playwright 스크린샷 확인 ✅

### [별첨3] AI솔루션 세부 설명자료 — 솔루션5(도면 AI) 추가 ✅

**목적**: 기존 별첨3 (예측모델/신호처리/멀티모달 4개 솔루션)에 솔루션5 "제조 도면 기반 AI 자동 분석 및 견적 생성 시스템" 추가

**작업 내역**:

1. **HTML 전면 재구성**
   - 기존 PDF 기반 이미지 HTML → 텍스트 선택/복사 가능한 HTML 테이블로 재작성
   - 파일 크기: 5.5MB → 39KB (이미지 외부 분리)
   - p.10~11 신규 추가 (빨간 테두리 + NEW 뱃지)

2. **데이터 보유·수집 현황 검증 및 수정** (p.10)
   - 실제 코드/데이터와 대조하여 모든 수치 검증
   - 기계도면 YOLO: 14클래스, 합성 10,000장 (model_registry.yaml)
   - P&ID: 32클래스, 999장 (rnd/benchmarks/pid2graph/)
   - 전력설비: 27클래스, 참조이미지 26장 (blueprint-ai-bom/class_examples/)
   - 수요기업 기계: 부품도면 87장 + BOM/사양서 7장 (apply-company/dsebearing/)
   - 수요기업 P&ID: P&ID 16장 + 표준도면 24장 (apply-company/techloss/)

3. **성능 수치 검증 및 교체**
   - ✅ 근거 있음: mAP50 68.5%, Recall 66.0%, OCR 가중치 40/35/15/10, 21 마이크로서비스, 73 검출 클래스
   - ❌ 근거 없음 → 수정:
     - OCR 94.2% → "4엔진 앙상블 구축 완료, 목표 95%+ 최적화 개발 중"
     - 2.5초 → "~15-20초 (파이프라인 구현 완료), GPU 최적화 목표 5초"
     - 96.9% 시간절감 → "53세션 전량 자동 분석, 수작업 대비 대폭 단축 실현"
     - 99.6% 비용절감 → "Docker 온프레미스 구축 완료, API 비용 최소화 아키텍처 확보"
     - 98%+ 정확도 → "98%+ 목표, Active Learning 고도화 진행 중"

4. **파이프라인 다이어그램 HTML 교체** (p.11)
   - 기존 PNG 이미지(근거 없는 수치 포함) → HTML 다이어그램으로 재구성
   - 모든 수치를 실측 기반으로 교체

5. **복사/편의 기능 추가**
   - 전체 데이터 테이블(11개)에 "📋 복사" 버튼 추가 (탭 구분자 → 엑셀/워드 붙여넣기)
   - base64 이미지 7개 → `images/` 폴더 별도 PNG 파일로 분리
   - HWP 삽입용 p.10~11 고해상도 캡처 (2x, 1588px 폭)

**산출물 위치**: `/home/uproot/ax/AI-boucher/`
```
AI-boucher/
├── [별첨3] AI솔루션 세부 설명자료_전체.html  (39KB)
└── images/
    ├── p10_솔루션5_메인테이블_2x.png         (531KB, HWP용)
    ├── p11_솔루션5_파이프라인_2x.png         (560KB, HWP용)
    ├── p06_diagram.png
    ├── p09_screenshots.png
    └── p11_02~05_*.png                       (스크린샷 4장)
```

---

## 2026-02-19 완료 작업

### Agent-Native Verification UI (Phase 1+2) ✅
- **백엔드**: `CropService` (PIL 크롭/컨텍스트/참조 이미지) + `agent_verification_router` (3 엔드포인트)
- **프론트엔드**: `AgentVerificationPage.tsx` (standalone 라우트 `/verification/agent`)
- **신규 파일**: `crop_service.py` (142줄), `agent_verification_router.py` (311줄), `AgentVerificationPage.tsx` (535줄)
- **수정 파일**: `api_server.py` (+4줄), `App.tsx` (+2줄), `pages/index.ts` (+1줄)
- **Agent-Friendly**: `data-action` 속성, `id` 속성, 키보드 단축키 (A/R/S/N/←→), 고정 레이아웃

### Dimension 검증 개선 (50개 전수 분석 기반) ✅
- **분석**: 동서기연 세션 50개 치수 전수 검사 → 48% 에러율 발견 (7가지 카테고리)
- **백엔드 개선** (`agent_verification_router.py`):
  - `AgentDecisionRequest` 확장: `modified_unit`, `modified_type`, `modified_tolerance`, `reject_reason` 추가
  - modify 시 value/unit/type/tolerance 개별 수정 가능
  - reject 시 reject_reason 저장 (not_dimension, garbage, duplicate)
  - Active Learning 로그에 전체 수정 내역 포함
- **프론트엔드 개선** (`AgentVerificationPage.tsx`):
  - 10가지 dimension_type (length/diameter/radius/chamfer/angle/gdt/surface_roughness/note/label/unknown)
  - 4가지 unit (mm/°/μm/없음)
  - 컬러코드 타입 배지 (blue=길이, purple=GD&T, pink=표면거칠기 등)
  - 구조화된 수정 폼: value + unit + type + tolerance 개별 입력
  - 퀵리젝트: "치수아님(N)" + "가비지" 전용 버튼
  - N키 단축키 (not_dimension 즉시 리젝트)
- **E2E 테스트**: 7가지 에러 카테고리 모두 확인 (GD&T/표면거칠기/비치수/각도/공차절단/가비지/정상)
- **검증**: Python ast ✅, npm run build ✅, Docker rebuild ✅, 줄수 311+535 (모두 600줄 이하)

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
