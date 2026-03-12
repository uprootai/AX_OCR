# 완료된 작업 아카이브

> 마지막 업데이트: 2026-03-12
> 완료된 작업들의 기록 (참조용)

---

## 2026-03-12 완료

### E07: Operational Excellence — WeekdayCode 4축 적용

WeekdayCode 27개 영상 인사이트 4축(테스트=해자, 모델비종속, 스택단순화, 운영비용+보안) 적용.

- **S01**: Web-UI 컴포넌트 테스트 4개 추가 (46 tests)
- **S02**: OCR A/B 비교 프레임워크 (edocr2/paddleocr/vl 3엔진, DSE GT 3장)
- **S03**: `GET /admin/cost-report` 원가 지표 API
- **S04**: 업로드 파일 24시간 TTL 자동 삭제 + 이벤트 로깅
- **S05**: table-detector-api 테스트 + CI model-services job
- **S06**: OCR 엔진 교체 가이드 문서 (ocr-engine-swap.mdx)
- **검증**: gateway 450 + web-ui 349 + model 6 = 805개 테스트 통과, 117p 빌드

---

## 2026-02-27 완료

### E02: 테크로스 P&ID 자동 설계 검증 납품

**상태**: ✅ **완료** | **커밋**: `b3e8c4b`~`8c1eb8d` (6 commits)

| Story | 요약 |
|-------|------|
| S01 파이프라인 테스트 | YOLO 257건, OCR 141건, BWMS API 60-70% 기구현 확인 |
| S02 BWMS 태그 인식 | 6/10 장비 검출, NoneType+bbox+OCR 3건 버그 수정 |
| S03 Excel 출력 | 9건 버그 수정, Equipment(6행)+Valve Signal(2행) Excel 생성 |
| S04 BWMS 규칙 | 96개 규칙 실행, 1건 위반(BWMS-006) 감지 |
| S05 프리셋 템플릿 | 4개 템플릿 OCR Ensemble 보강 |
| S06 E2E 검증 | 46% 자동화 커버리지 (목표 30%+ 초과 달성) |

**핵심 성과**:
- OCR: PaddleOCR(23 texts) → OCR Ensemble(157 texts) 전환
- Design Checker: 96개 BWMS 규칙 (builtin 7 + dynamic 89)
- 자동화 커버리지: 44/96 = **46%**
- 검증 리포트: `apply-company/techloss/E02-validation-report.md`

---

### BMAD-Lite 도입 (솔로 개발자 + AI 에이전트 워크플로)

**상태**: ✅ **완료**

| 항목 | 내용 |
|------|------|
| 템플릿 2개 | `EPIC_TEMPLATE.md`, `STORY_TEMPLATE.md` |
| 첫 Epic | E01 성과발표회 PPT (Story 3개: S01 ✅, S02 ✅, S03 대기) |
| 신규 스킬 | `presentation-guide.md` (PPT 디자인 규격 + 3중 검증) |
| 신규 커맨드 | `/plan-epic` (Epic 기획 → Story 분해) |
| BACKLOG.md | Epic 인덱스 형태로 구조 전환 |
| CLAUDE.md | Epic/Story 워크플로 섹션 추가 (545줄) |

**구조**: `.todo/templates/` + `.todo/epics/{id}/` + `.todo/decisions/`

---

## 2026-02-26 완료

### MoAI-ADK 아이디어 차용 + Hook 시스템 강화

**상태**: ✅ **완료** | **커밋**: `aefc22a`

| 항목 | 내용 |
|------|------|
| 신규 Hook 2개 | `post-edit-quality.sh` (Quality Gate), `handle-prompt-submit.sh` (세션 인사) |
| 버그 수정 6건 | injection, stdout 누수, word splitting, newline, 시크릿 미검출, 하드코딩 경로 |
| settings.local.json | 누락 훅 3개 등록 → 7개 SSOT |
| CLAUDE.md | 서브에이전트 모델 배정, AX Tag, Hooks 7개 테이블 (+33줄) |
| skills/README.md | 10개→15개, Quick Ref 열, Progressive Disclosure L0/L1/L2 |

**MoAI-ADK 분석 결과**: Go 34K줄, 28 에이전트, 52 스킬, 16 Hook 이벤트. GPL 코드 복사 없이 아이디어만 차용.

---

### 문서 통합 마이그레이션 (5173/docs → 3001 Docusaurus)

**상태**: ✅ **완료**

| 항목 | 내용 |
|------|------|
| Phase 1 | 4개 신규 섹션 추가 (~48 파일) |
| Phase 2 | 3개 기존 섹션 보강 (+3 파일) |
| Phase 3 | web-ui /docs → localhost:3001 리다이렉트 |
| Phase 4 | sidebars.ts, docusaurus.config.ts 업데이트, 빌드 검증 |

**Phase 1 신규 섹션**:
- `research/` — 16파일 (index + 15 논문, papers/ 기반)
- `api-reference/` — 19파일 (index + 18 API 파라미터, api/ 기반)
- `developer/` — 7파일 (index + 6 가이드, CONTRIBUTING/GIT_WORKFLOW 등)
- `deployment/` — 6파일 (index + 5 가이드, INSTALLATION/ONPREMISE 등)

**Phase 2 기존 섹션 보강**:
- `system-overview/architecture-decisions.md` — DECISION_MATRIX + MODEL_SELECTION_CRITERIA 통합
- `blueprintflow/optimization.md` — 3개 최적화 파일 통합
- `quality-assurance/evaluation-reports.md` — 2개 보고서 통합

**Phase 3 web-ui 수정**:
- `Docs.tsx` — 512줄 → 25줄 (리다이렉트 컴포넌트)
- `Sidebar.tsx` — 외부 링크 지원 추가 (ExternalLink 아이콘)
- `DocsSection.tsx` — localhost:3001 링크
- `ExportToBuiltinDialog.tsx` — /docs → localhost:3001/docs
- `web-ui/public/docs/` — **전체 삭제** (87 파일)

**결과**: 10섹션 48페이지 → **14섹션 101페이지**, 빌드 ✅ (docs-site + web-ui)

---

## 2026-02-23 완료

### 문서 사이트 전체 한글화

**상태**: ✅ **완료**

- 10개 섹션 49개 MDX/MD 파일 한글 번역
- React TSX 다이어그램 컴포넌트 7개 중 5개 한글화
- 커밋: c1895d7, a15cda3, 8f5b927

---

## 2026-02-19 완료

### Agent-Native Verification UI (Phase 1+2) + Dimension 검증 개선

**상태**: ✅ **완료**

| 항목 | 내용 |
|------|------|
| 백엔드 신규 | `crop_service.py` (142줄), `agent_verification_router.py` (311줄) |
| 프론트엔드 신규 | `AgentVerificationPage.tsx` (535줄) |
| 백엔드 수정 | `api_server.py` (라우터 등록 + CropService DI) |
| 프론트엔드 수정 | `App.tsx` (라우트), `pages/index.ts` (export) |
| 라우트 | `/verification/agent?session={sid}&type=symbol|dimension` |

**Agent-Friendly 설계**:
- Playwright 셀렉터: `#btn-approve`, `#btn-reject`, `[data-action="reject-not-dimension"]`, `[data-action="reject-garbage"]`
- 키보드 단축키: A=승인, R=거부, N=치수아님, S=건너뛰기, ←→=이동
- 구조화 수정: `#input-modify-value`, `#select-modify-unit`, `#select-modify-type`, `#input-modify-tolerance`

**Dimension 검증 개선 (50개 전수 분석 기반)**:
- 에러 카테고리 7가지 식별 (GD&T 7건, 가비지 8건, 비치수 4건, 공차절단 3건, 표면거칠기 2건, 각도 2건)
- 백엔드: AgentDecisionRequest 확장 (modified_unit/type/tolerance, reject_reason)
- 프론트엔드: 10가지 dimension_type, 4가지 unit, 컬러코드 배지, 퀵리젝트 버튼

**E2E 검증**: 7가지 에러 카테고리 × Playwright 테스트 → 백엔드 데이터 저장 확인 ✅

---

## 2026-02-14 완료

### 동서기연 터빈 베어링 납품 패키지 생성

**상태**: ✅ **완료**

| 항목 | 내용 |
|------|------|
| 패키지 위치 | `blueprint-ai-bom/exports/dsebearing-delivery/` |
| 총 크기 | 4.5GB (비압축 9.1GB → 50% 절감) |
| Backend 이미지 | 4.5GB (gzip) |
| Frontend 이미지 | 25MB (gzip) |
| 프로젝트 데이터 | 546KB (53 세션, BOM 326개) |
| 설치 스크립트 | setup.sh (Linux/macOS) + setup.ps1 (Windows) |
| 체크섬 | CHECKSUMS.sha256 (SHA-256) |

**클린 환경 테스트 결과**:
- Docker compose up: backend healthy → frontend 200 OK
- Import: 53 세션 / 0 실패, BOM 326개 확인
- 발견 수정: Import API가 multipart/form-data 방식 → setup.sh/ps1 수정

---

### Self-contained Export에 프로젝트 데이터 + GT 라벨 포함

**상태**: ✅ **완료**

| 수정 파일 | 변경 내용 |
|----------|----------|
| `session_io_router.py` | import 엔드포인트에 `project_id` 파라미터 추가 |
| `self_contained_export_service.py` | `project.json` + `gt_labels/` + `gt_reference/` 패키지 포함 |
| `export_script_generator.py` | import 스크립트 5→8단계 (프로젝트/GT 복원) |
| `api_server.py` | `project_service` 주입 누락 수정 |

**결과**: Import 환경에서 GT 비교 정상 작동 (F1: 96.2%, Precision: 96.2%, Recall: 96.2%)

---

## 2026-02-07 완료

### 1000줄 초과 파일 4개 리팩토링

**상태**: ✅ **완료**

| 원본 파일 | 이전 | 이후 | 신규 모듈 |
|----------|------|------|----------|
| `self_contained_export_service.py` | 1304줄 | 550줄 | `export_script_generator.py` (527), `export_docker_handler.py` (247) |
| `analysisNodes.ts` | 2019줄 | 17줄 | `analysisNodesPid.ts` (453), `analysisNodesDocument.ts` (539), `analysisNodesBom.ts` (559), `analysisNodesQuality.ts` (468) |
| `api.ts` | 1397줄 | 7줄 | `apiTypes.ts` (242), `apiServices.ts` (567), `apiHealth.ts` (273), `apiProject.ts` (385) |
| `ExecutionStatusPanel.tsx` | 1097줄 | 171줄 | `FinalResultView.tsx` (530), `OutputDisplays.tsx` (416) |

**패턴**: 배럴 re-export로 기존 import 경로 유지
**검증**: Python 문법 ✅, TypeScript 빌드 ✅, 프로덕션 빌드 ✅

---

## 2026-02-05~06 완료

### DSE Bearing BOM 배치 분석 100% 달성

**상태**: ✅ **완료**

| 항목 | 결과 |
|------|------|
| 세션 수 | 53/53 (100%) |
| 총 치수 | 2,710개 |
| 평균 치수/세션 | 51.1개 |
| 처리 시간 | ~3시간 |

**해결한 문제들**:
1. **eDOCr2 타임아웃 이슈**: 120초 → 600초 증가 (47.2% → 98.1%)
2. **대용량 이미지 OOM**: 139MP 이미지 자동 리사이즈 (98.1% → 100%)

**구현 파일**:
- `services/dimension_service.py` - timeout 600초
- `services/image_utils.py` - resize_image_if_needed() 신규
- `routers/session_router.py` - 업로드 시 자동 리사이즈

---

### 어셈블리 단위 세션 관리 (Step 1-3)

**상태**: ✅ **완료**

| Step | 작업 | 상태 |
|------|------|------|
| Step 1 | 데이터 스키마 확장 | ✅ |
| Step 2 | 견적 집계 서비스 | ✅ |
| Step 3 | UI 컴포넌트 | ✅ |

**결과**: 7개 어셈블리 그룹 감지, 51/53 세션 매핑

---

## 2026-02-04 완료

### DSE Bearing BOM 계층 워크플로우 Phase 1-3

**상태**: ✅ **완료**

| Phase | 작업 | 상태 |
|-------|------|------|
| Phase 1 | BOM PDF 파싱, 도면 매칭, 세션 일괄 생성 | ✅ |
| Phase 2 | 5단계 위저드 UI, 트리뷰, 매칭 테이블 | ✅ |
| Phase 3 | 견적 집계, MaterialBreakdown, QuotationDashboard | ✅ |

**커밋**: cfd35cc

---

## 2026-02-03 완료

### P1-3 Executor API 호출 메서드 분리

| Executor | 상태 |
|----------|------|
| bom_executor.py | ✅ `_call_api()`, `_post_api()`, `_patch_api()` |
| pdfexport_executor.py | ✅ `_post_api()` |
| pidfeatures_executor.py | ✅ `_post_api()` |

### P1-4 BOM 프론트엔드 세션 단가 표시

- 세션 조회 시 `has_custom_pricing` 반환
- BOM 헤더에 "커스텀 단가" 배지

### P1-5 DetectionResultsSection 클래스 하이라이트

- `selectedClassName` state
- 클래스 필터 UI
- Canvas 렌더링 (opacity/lineWidth)

### P2-2 BOM ↔ 도면 하이라이트 연동

양방향 동기화: BOM 테이블 클릭 ↔ 도면 하이라이트

---

## 2026-01-22 완료

### 0. DSE Bearing 100점 달성 (P1)

**상태**: ✅ **전체 완료**

| Phase | 작업 | 상태 |
|-------|------|------|
| Phase 1 | Title Block Parser | ✅ 완료 |
| Phase 2 | Parts List 강화 | ✅ 완료 |
| Phase 3 | Dimension Parser | ✅ 완료 |
| Phase 4 | BOM 자동 매칭 | ✅ 완료 |
| Phase 5 | 견적 자동화 (Excel/PDF) | ✅ 완료 |
| Phase 6 | 통합 파이프라인 | ✅ 완료 |

**구현 내역**:
- `gateway-api/routers/dsebearing_router.py` - 전체 API 라우터
- `gateway-api/services/` - 4개 서비스 (parser, price_db, customer, exporter)
- `gateway-api/blueprintflow/executors/` - 5개 Executor
- `tests/unit/test_dsebearing_services.py` - 25개 단위 테스트
- `tests/e2e/test_dsebearing_pipeline.py` - E2E 테스트
- `gateway-api/api_specs/dsebearing.yaml` - 통합 API 스펙
- `apply-company/dsebearing/API_GUIDE.md` - 사용 가이드

**기능**:
- 12개 재질 가격 DB (SF45A, ASTM B23 등)
- 2개 고객 프로파일 (DSE 5%, DOOSAN 8% 할인)
- 수량별 할인 (10개 5%, 50개 10%, 100개 15%)
- Excel/PDF 견적서 출력

---

### 1. P2: 테스트 커버리지 확대 (+119 tests)

**커밋**: `9931dfd`

| 테스트 파일 | 테스트 수 |
|------------|----------|
| `hooks/useAPIRegistry.test.ts` | 14 |
| `hooks/useHyperParameters.test.ts` | 12 |
| `lib/api.test.ts` | 43 |
| `services/apiRegistryService.test.ts` | 19 |
| `utils/specToHyperparams.test.ts` | 16 |
| `charts/ConfidenceDistributionChart.test.tsx` | 15 |
| **합계** | **119** |

**결과**: 549 → 668 테스트 (web-ui 304, gateway 364)

---

### 2. P3: 신뢰도 분포 차트

**커밋**: `3bc6876`

| 기능 | 상태 |
|------|------|
| ConfidenceDistributionChart 컴포넌트 | ✅ 구현 |
| 5단계 색상 코딩 히스토그램 | ✅ |
| 통계 표시 (평균/중앙값/표준편차) | ✅ |
| 컴팩트 모드 | ✅ |
| YOLOVisualization 통합 | ✅ |
| 15개 테스트 | ✅ |

---

### 3. DSE Bearing 템플릿 완성

**커밋**: `041f76c`

| 작업 | 상태 |
|------|------|
| ExcelExport 파라미터 API 스펙 동기화 | ✅ |
| 12개 노드 파라미터 정리 | ✅ |
| 템플릿 점수: 95/100 → 100/100 | ✅ |

---

### 4. Archive 정리 및 .todo 관리 시스템 문서화

| 작업 | 상태 |
|------|------|
| Archive 파일 검토 (29개) | ✅ |
| 완료/중복/역사적 파일 삭제 (27개) | ✅ |
| 진행 중 파일 유지 (2개) | ✅ |
| CLAUDE.md에 .todo/ 관리 섹션 추가 | ✅ |
| skills/README.md 경로 수정 | ✅ |

**삭제된 파일 (27개)**:
- 완료된 문서: AUDIT_PHASE1-6.md, CONFIG/NODE/API 관련 문서
- 중복 문서: 01_NEW_API_CHECKLIST.md (skills/api-creation-guide.md와 동일)
- 역사적 문서: FILE_INVENTORY.md, DIRECTORY_AUDIT_PLAN.md

**유지된 파일 (2개)**:
- `02_VISUALIZATION_EXTENSION.md` - BOM 통합 작업 진행 중
- `04_GATEWAY_SERVICE_SEPARATION.md` - 향후 아키텍처 작업

---

## 2026-01-19 완료

### 5. Config 디렉토리 일관성

| API | 상태 |
|-----|------|
| 18개 API config/ 디렉토리 | ✅ 완료 |
| defaults.py 또는 대안 패턴 | ✅ 검증 |

---

### 6. 프로파일 시스템 통합

| 작업 | 상태 |
|------|------|
| 백엔드 config/defaults.py 패턴 | ✅ 19/19 API |
| 프론트엔드 ProfileDefinition 타입 | ✅ |
| NodeDefinitions profiles 필드 | ✅ 18 노드 |

---

### 7. 디렉토리 정리

**커밋**: `73fae41`

| 작업 | 상태 |
|------|------|
| rnd/ 정리 및 모델 추가 | ✅ |
| scripts/ 정리 (training scripts 이동) | ✅ |
| web-ui/ 정리 (test artifacts 삭제) | ✅ |
| root 파일 정리 (32 → 15개) | ✅ |
| docs/ 정리 (보수적 접근) | ✅ |

---

## 2026-01-16 완료

### 8. 코드 정리 작업 (P0~P3)

| 작업 | 상태 |
|------|------|
| PID 컴포넌트 API 호출 수정 | ✅ Design Checker API (5019) |
| eDOCr2 version 파라미터 정리 | ✅ |
| 린트 에러 수정 (21개 → 0개) | ✅ |
| 모델 레지스트리 동기화 | ✅ 5개 모델 타입 |
| Excel 파일 정리 | ✅ gitignore |

---

### 9. Design Checker Pipeline 통합 (P0~P1)

| 작업 | 상태 |
|------|------|
| YOLO + eDOCr2 통합 파이프라인 | ✅ |
| 서비스 레이어 추가 | ✅ yolo_service.py, edocr2_service.py |
| 테스트 코드 작성 | ✅ 74개 |
| API 스펙 업데이트 | ✅ design-checker.yaml |

---

### 10. Feature Implication 시스템 (P0~P1)

| 작업 | 상태 |
|------|------|
| implies/impliedBy 관계 정의 | ✅ 6개 헬퍼 |
| isPrimary 속성 추가 | ✅ |
| 자동 활성화 로직 | ✅ 29개 테스트 |

---

### 11. Toast 마이그레이션

| 작업 | 상태 |
|------|------|
| 12개 파일 마이그레이션 | ✅ |
| APIStatusMonitor 토스트 | ✅ |
| BlueprintFlow 노드 실행 토스트 | ✅ |
| 전역 로딩 오버레이 시스템 | ✅ |

---

## 관련 커밋 히스토리

| 날짜 | 커밋 | 내용 |
|------|------|------|
| 2026-01-22 | `1745d92` | docs: P2/P3 완료 상태 업데이트 |
| 2026-01-22 | `3bc6876` | feat: 신뢰도 분포 히스토그램 차트 |
| 2026-01-22 | `9931dfd` | test: 신규 테스트 추가 549→653 |
| 2026-01-22 | `041f76c` | fix: DSE Bearing ExcelExport 파라미터 |
| 2026-01-19 | `73fae41` | chore: 디렉토리 정리 |
| 2026-01-16 | `5b6b0e0` | chore: P2/P3 코드 정리 작업 완료 |
| 2026-01-16 | `5116ea3` | feat(design-checker): YOLO + eDOCr2 통합 |

---

*마지막 업데이트: 2026-01-22*
