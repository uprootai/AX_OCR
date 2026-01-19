# 전체 파일 목적 인벤토리

> **생성일**: 2026-01-17
> **목적**: /home/uproot/ax/poc 하위 모든 파일의 용도 기술
> **총 파일 수**: ~2,000개 (node_modules, .git 등 제외)

---

## 1. 루트 디렉토리 파일 (33개)

### 설정 파일

| 파일명 | 용도 |
|--------|------|
| `.editorconfig` | 에디터 공통 설정 (들여쓰기, 인코딩 등) |
| `.env.example` | 환경변수 템플릿 (API 키, 포트, DB 설정 등) |
| `.gitattributes` | Git 파일 처리 규칙 (LF/CRLF, binary 등) |
| `.gitignore` | Git 추적 제외 파일 패턴 |
| `.mcp.json` | MCP (Model Context Protocol) 서버 설정 |
| `.pre-commit-config.yaml` | pre-commit 훅 설정 (lint, format 등) |

### 문서 파일

| 파일명 | 용도 |
|--------|------|
| `CLAUDE.md` | Claude Code 프로젝트 가이드 (LLM용 컨텍스트) |
| `README.md` | 프로젝트 메인 문서 (설치, 사용법) |
| `ARCHITECTURE.md` | 시스템 아키텍처 설계 문서 |
| `ROADMAP.md` | 개발 로드맵 및 마일스톤 |
| `WORKFLOWS.md` | BlueprintFlow 워크플로우 사용 가이드 |
| `QUICK_START.md` | 빠른 시작 가이드 |
| `DEPLOYMENT_GUIDE.md` | 배포 가이드 (Docker, K8s) |
| `KNOWN_ISSUES.md` | 알려진 이슈 및 해결 방법 |
| `SKILL.md` | Claude Code 스킬 정의 |
| `API_AUTOMATION_COMPLETE_GUIDE.md` | API 자동화 완성 가이드 |
| `BLUEPRINTFLOW_FRONTEND_EXECUTE_COMPLETE.md` | BlueprintFlow 프론트엔드 실행 완료 문서 |
| `BLUEPRINTFLOW_PHASE4_COMPLETION.md` | BlueprintFlow Phase4 완료 보고서 |
| `DOCUMENTATION_UPDATE_SUMMARY.md` | 문서 업데이트 요약 |
| `DYNAMIC_API_SYSTEM_GUIDE.md` | 동적 API 시스템 가이드 |
| `PROJECT_FILE_INVENTORY_REPORT.md` | 프로젝트 파일 인벤토리 보고서 |

### Docker 설정

| 파일명 | 용도 |
|--------|------|
| `docker-compose.yml` | 메인 Docker Compose 설정 (20개 서비스) |
| `docker-compose.override.yml` | 로컬 개발용 오버라이드 설정 |
| `docker-compose.override.yml.example` | 오버라이드 템플릿 |
| `docker-compose.monitoring.yml` | Grafana/Prometheus 모니터링 스택 |
| `docker-compose.offline.yml` | 오프라인 배포용 설정 |

### 빌드/자동화

| 파일명 | 용도 |
|--------|------|
| `Makefile` | 빌드/테스트/배포 자동화 명령어 |

### 테스트 파일

| 파일명 | 용도 |
|--------|------|
| `test_blueprintflow_scenarios.py` | BlueprintFlow 시나리오 테스트 |
| `test_control_flow.py` | 제어 흐름 노드 테스트 |
| `test_workflow_order.py` | 워크플로우 실행 순서 테스트 |

### 데이터 파일

| 파일명 | 용도 |
|--------|------|
| `TECHCROSS_BWMS_Analysis_Report.xlsx` | BWMS 분석 보고서 v1 |
| `TECHCROSS_BWMS_Analysis_Report_v2.xlsx` | BWMS 분석 보고서 v2 |

### 심볼릭 링크

| 파일명 | 용도 |
|--------|------|
| `api-guide-sample` | → /home/uproot/ax/ax-api-sample (API 가이드 샘플) |

---

## 2. .claude/ 디렉토리 (25개)

### .claude/commands/ (커스텀 명령어)

| 파일명 | 용도 |
|--------|------|
| `README.md` | 커스텀 명령어 사용 가이드 |
| `add-feature.md` | `/add-feature` - 새 기능 추가 스킬 |
| `debug-issue.md` | `/debug-issue` - 이슈 디버깅 스킬 |
| `handoff.md` | `/handoff` - 세션 핸드오프 스킬 |
| `rebuild-service.md` | `/rebuild-service` - Docker 서비스 재빌드 |
| `test-api.md` | `/test-api` - API 테스트 스킬 |
| `track-issue.md` | `/track-issue` - 이슈 추적 스킬 |

### .claude/skills/ (스킬 가이드)

| 파일명 | 용도 |
|--------|------|
| `README.md` | 스킬 사용 가이드 |
| `api-creation-guide.md` | 새 API 생성 상세 가이드 |
| `context-engineering-guide.md` | 컨텍스트 엔지니어링 가이드 |
| `modularization-guide.md` | 모듈화/리팩토링 가이드 (1000줄 규칙) |
| `project-reference.md` | 프로젝트 참조 문서 (R&D, 스펙) |
| `version-history.md` | 버전 히스토리 (BOM, Design Checker) |

### .claude/hooks/ (훅 스크립트)

| 파일명 | 용도 |
|--------|------|
| (설정 파일들) | pre/post 훅 스크립트 |

### .claude/ 설정

| 파일명 | 용도 |
|--------|------|
| `settings.json` | Claude Code 프로젝트 설정 |
| `settings.local.json` | 로컬 개인 설정 (gitignore) |

---

## 3. .github/ 디렉토리 (4개)

### .github/workflows/

| 파일명 | 용도 |
|--------|------|
| `ci.yml` | CI 파이프라인 (lint, test, build) |
| `cd.yml` | CD 파이프라인 (deploy) |

### .github/

| 파일명 | 용도 |
|--------|------|
| `dependabot.yml` | 의존성 자동 업데이트 설정 |
| `CODEOWNERS` | 코드 소유자 정의 |

---

## 4. .todo/ 디렉토리 (24개)

| 파일명 | 용도 |
|--------|------|
| `ACTIVE.md` | 현재 진행 중인 작업 목록 |
| `BACKLOG.md` | 백로그 및 향후 작업 |
| `COMPLETED.md` | 완료된 작업 아카이브 |
| `DIRECTORY_AUDIT_PLAN.md` | 디렉토리 감사 계획 및 결과 |
| `AUDIT_PHASE1_CORE.md` | Phase 1 감사 결과 (핵심 코드) |
| `AUDIT_PHASE2_INFRA.md` | Phase 2 감사 결과 (인프라) |
| `AUDIT_PHASE3_DOCS.md` | Phase 3 감사 결과 (문서) |
| `AUDIT_PHASE4_DATA.md` | Phase 4 감사 결과 (데이터) |
| `AUDIT_PHASE5_TEMP.md` | Phase 5 감사 결과 (임시) |
| `AUDIT_PHASE6_MISC.md` | Phase 6 감사 결과 (기타) |
| `FILE_INVENTORY.md` | 전체 파일 목적 인벤토리 (현재 파일) |
| `02_VISUALIZATION_EXTENSION.md` | 시각화 기능 확장 계획 |
| `03_MODEL_CONFIG_PATTERN.md` | MODEL_DEFAULTS 패턴 문서 |
| `05_CLEANUP_TASKS.md` | 정리 작업 목록 |
| `07_DESIGN_CHECKER_PIPELINE_INTEGRATION.md` | Design Checker 통합 계획 |
| `08_FEATURE_IMPLICATION_SYSTEM.md` | Feature Implication 시스템 |
| `09_NODE_DEFINITIONS_SYNC.md` | 노드 정의 동기화 |
| `10_BLUEPRINT_BOM_GT_SYSTEM.md` | Blueprint BOM GT 시스템 |

---

## 5. .vscode/ 디렉토리 (2개)

| 파일명 | 용도 |
|--------|------|
| `settings.json` | VSCode 프로젝트 설정 |
| `extensions.json` | 권장 확장 프로그램 목록 |

---

## 6. gateway-api/ 디렉토리 (177개)

### gateway-api/ 루트

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | FastAPI 메인 서버 진입점 |
| `requirements.txt` | Python 의존성 목록 |
| `Dockerfile` | Docker 이미지 빌드 설정 |
| `pytest.ini` | pytest 설정 |
| `pyproject.toml` | Python 프로젝트 설정 |
| `.env.example` | 환경변수 템플릿 |

### gateway-api/api_specs/ (API 스펙)

| 파일명 | 용도 |
|--------|------|
| `yolo.yaml` | YOLO API OpenAPI 스펙 + profiles |
| `edocr2.yaml` | eDOCr2 API OpenAPI 스펙 + profiles |
| `edgnet.yaml` | EDGNet API OpenAPI 스펙 + profiles |
| `line-detector.yaml` | Line Detector API 스펙 + profiles |
| `design-checker.yaml` | Design Checker API 스펙 |
| `paddleocr.yaml` | PaddleOCR API 스펙 |
| `tesseract.yaml` | Tesseract API 스펙 |
| `trocr.yaml` | TrOCR API 스펙 |
| `ocr-ensemble.yaml` | OCR Ensemble API 스펙 |
| `surya-ocr.yaml` | Surya OCR API 스펙 |
| `doctr.yaml` | DocTR API 스펙 |
| `easyocr.yaml` | EasyOCR API 스펙 |
| `esrgan.yaml` | ESRGAN API 스펙 |
| `skinmodel.yaml` | SkinModel API 스펙 |
| `vl.yaml` | Vision-Language API 스펙 |
| `knowledge.yaml` | Knowledge API 스펙 |
| `pid-analyzer.yaml` | PID Analyzer API 스펙 |
| `blueprint-ai-bom.yaml` | Blueprint AI BOM API 스펙 |

### gateway-api/routers/ (라우터)

| 파일명 | 용도 |
|--------|------|
| `__init__.py` | 라우터 패키지 초기화 |
| `yolo_router.py` | YOLO 엔드포인트 라우터 |
| `ocr_router.py` | OCR 통합 라우터 |
| `analysis_router.py` | 분석 API 라우터 |
| `workflow_router.py` | 워크플로우 API 라우터 |
| `health_router.py` | 헬스체크 라우터 |
| `spec_router.py` | API 스펙 제공 라우터 |

### gateway-api/services/ (서비스 레이어)

| 파일명 | 용도 |
|--------|------|
| `__init__.py` | 서비스 패키지 초기화 |
| `yolo_service.py` | YOLO API 호출 서비스 |
| `edocr2_service.py` | eDOCr2 API 호출 서비스 |
| `ocr_service.py` | OCR 통합 서비스 |
| `workflow_service.py` | 워크플로우 실행 서비스 |

### gateway-api/blueprintflow/ (워크플로우 엔진)

| 파일명 | 용도 |
|--------|------|
| `__init__.py` | 패키지 초기화 |
| `engine.py` | 워크플로우 실행 엔진 |
| `models.py` | 워크플로우 데이터 모델 |
| `graph.py` | DAG 그래프 처리 |

### gateway-api/blueprintflow/executors/ (노드 실행기)

| 파일명 | 용도 |
|--------|------|
| `__init__.py` | Executor 패키지 초기화 |
| `executor_registry.py` | Executor 등록 및 관리 |
| `base_executor.py` | 기본 Executor 추상 클래스 |
| `yolo_executor.py` | YOLO 노드 실행기 |
| `edocr2_executor.py` | eDOCr2 노드 실행기 |
| `edgnet_executor.py` | EDGNet 노드 실행기 |
| `paddleocr_executor.py` | PaddleOCR 노드 실행기 |
| `tesseract_executor.py` | Tesseract 노드 실행기 |
| `trocr_executor.py` | TrOCR 노드 실행기 |
| `ocr_ensemble_executor.py` | OCR Ensemble 노드 실행기 |
| `surya_ocr_executor.py` | Surya OCR 노드 실행기 |
| `doctr_executor.py` | DocTR 노드 실행기 |
| `easyocr_executor.py` | EasyOCR 노드 실행기 |
| `esrgan_executor.py` | ESRGAN 노드 실행기 |
| `skinmodel_executor.py` | SkinModel 노드 실행기 |
| `vl_executor.py` | VL 노드 실행기 |
| `knowledge_executor.py` | Knowledge 노드 실행기 |
| `control_executor.py` | IF/Loop/Merge 제어 노드 실행기 |
| `line_detector_executor.py` | Line Detector 노드 실행기 |
| `pid_analyzer_executor.py` | PID Analyzer 노드 실행기 |
| `design_checker_executor.py` | Design Checker 노드 실행기 |
| `blueprint_ai_bom_executor.py` | Blueprint AI BOM 노드 실행기 |

### gateway-api/tests/ (테스트)

| 파일명 | 용도 |
|--------|------|
| `__init__.py` | 테스트 패키지 초기화 |
| `conftest.py` | pytest fixture 설정 |
| `test_api_server.py` | API 서버 통합 테스트 |
| `test_yolo.py` | YOLO 서비스 테스트 |
| `test_ocr.py` | OCR 서비스 테스트 |
| `test_workflow.py` | 워크플로우 테스트 |
| `test_blueprintflow.py` | BlueprintFlow 엔진 테스트 |
| `test_executors.py` | Executor 단위 테스트 |

### gateway-api/utils/ (유틸리티)

| 파일명 | 용도 |
|--------|------|
| `__init__.py` | 유틸리티 패키지 초기화 |
| `image_utils.py` | 이미지 처리 유틸리티 |
| `file_utils.py` | 파일 처리 유틸리티 |
| `response_utils.py` | API 응답 포맷 유틸리티 |

---

## 7. web-ui/ 디렉토리 (347개)

### web-ui/ 루트

| 파일명 | 용도 |
|--------|------|
| `package.json` | npm 패키지 설정 및 스크립트 |
| `package-lock.json` | 의존성 잠금 파일 |
| `vite.config.ts` | Vite 빌드 설정 |
| `tsconfig.json` | TypeScript 컴파일러 설정 |
| `tsconfig.node.json` | Node용 TypeScript 설정 |
| `tailwind.config.js` | Tailwind CSS 설정 |
| `postcss.config.js` | PostCSS 설정 |
| `eslint.config.js` | ESLint 설정 |
| `playwright.config.ts` | Playwright E2E 테스트 설정 |
| `vitest.config.ts` | Vitest 단위 테스트 설정 |
| `index.html` | HTML 진입점 |
| `Dockerfile` | Docker 이미지 빌드 |

### web-ui/src/ 루트

| 파일명 | 용도 |
|--------|------|
| `main.tsx` | React 앱 진입점 |
| `App.tsx` | 메인 앱 컴포넌트 (라우팅) |
| `index.css` | 전역 CSS 스타일 |
| `vite-env.d.ts` | Vite 타입 정의 |

### web-ui/src/components/ (컴포넌트)

#### blueprintflow/ (워크플로우 빌더)

| 파일명 | 용도 |
|--------|------|
| `BlueprintFlowCanvas.tsx` | React Flow 캔버스 컴포넌트 |
| `CustomNode.tsx` | 커스텀 노드 렌더링 |
| `NodeDetailPanel.tsx` | 노드 상세/파라미터 패널 |
| `NodePalette.tsx` | 노드 팔레트 (드래그 소스) |
| `WorkflowToolbar.tsx` | 워크플로우 툴바 |
| `ExecutionPanel.tsx` | 실행 결과 패널 |

#### blueprintflow/node-palette/

| 파일명 | 용도 |
|--------|------|
| `index.tsx` | 노드 팔레트 메인 |
| `NodeCard.tsx` | 개별 노드 카드 |
| `CategorySection.tsx` | 카테고리 섹션 |
| `constants.ts` | 팔레트 상수 |

#### monitoring/ (모니터링)

| 파일명 | 용도 |
|--------|------|
| `APIStatusMonitor.tsx` | API 상태 모니터링 대시보드 |
| `ServiceCard.tsx` | 서비스 상태 카드 |
| `HealthIndicator.tsx` | 헬스 상태 표시 |

#### debug/ (디버깅)

| 파일명 | 용도 |
|--------|------|
| `YOLOVisualization.tsx` | YOLO 검출 결과 시각화 |
| `OCRVisualization.tsx` | OCR 결과 시각화 |
| `DebugPanel.tsx` | 디버그 패널 |

#### pid/ (P&ID)

| 파일명 | 용도 |
|--------|------|
| `PIDOverlayViewer.tsx` | P&ID SVG 오버레이 뷰어 |
| `PIDSymbolList.tsx` | P&ID 심볼 목록 |

#### ui/ (공통 UI)

| 파일명 | 용도 |
|--------|------|
| `button.tsx` | 버튼 컴포넌트 |
| `input.tsx` | 입력 컴포넌트 |
| `select.tsx` | 선택 컴포넌트 |
| `card.tsx` | 카드 컴포넌트 |
| `dialog.tsx` | 다이얼로그 컴포넌트 |
| `toast.tsx` | 토스트 알림 컴포넌트 |
| `toaster.tsx` | 토스터 컨테이너 |
| `tabs.tsx` | 탭 컴포넌트 |
| `table.tsx` | 테이블 컴포넌트 |
| `badge.tsx` | 배지 컴포넌트 |
| `skeleton.tsx` | 로딩 스켈레톤 |
| `spinner.tsx` | 로딩 스피너 |

### web-ui/src/config/ (설정)

| 파일명 | 용도 |
|--------|------|
| `apiRegistry.ts` | API 엔드포인트 레지스트리 |
| `nodeDefinitions.ts` | 노드 타입 정의 (28개 노드) |
| `index.ts` | 설정 내보내기 |

#### config/nodes/ (노드 정의 분리)

| 파일명 | 용도 |
|--------|------|
| `inputNodes.ts` | Input 노드 정의 |
| `detectionNodes.ts` | Detection 노드 정의 |
| `ocrNodes.ts` | OCR 노드 정의 |
| `segmentationNodes.ts` | Segmentation 노드 정의 |
| `analysisNodes.ts` | Analysis 노드 정의 |
| `controlNodes.ts` | Control 노드 정의 |
| `types.ts` | 노드 타입 정의 |

#### config/features/ (피처 플래그)

| 파일명 | 용도 |
|--------|------|
| `index.ts` | 피처 플래그 내보내기 |
| `featureDefinitions.ts` | 피처 정의 |

### web-ui/src/hooks/ (커스텀 훅)

| 파일명 | 용도 |
|--------|------|
| `useNodeDefinitions.ts` | 노드 정의 로드 훅 |
| `useAPIDetail.ts` | API 상세 정보 훅 |
| `useContainerStatus.ts` | Docker 컨테이너 상태 훅 |
| `useImageUpload.ts` | 이미지 업로드 훅 |
| `useWorkflowExecution.ts` | 워크플로우 실행 훅 |
| `useToast.ts` | 토스트 알림 훅 |

### web-ui/src/lib/ (라이브러리)

| 파일명 | 용도 |
|--------|------|
| `api.ts` | API 클라이언트 (axios) |
| `utils.ts` | 유틸리티 함수 (cn 등) |

### web-ui/src/pages/ (페이지)

| 파일명 | 용도 |
|--------|------|
| `Dashboard.tsx` | 대시보드 메인 페이지 |
| `Admin.tsx` | 관리자 페이지 |
| `Guide.tsx` | 가이드 페이지 |
| `Docs.tsx` | 문서 페이지 |

#### pages/blueprintflow/

| 파일명 | 용도 |
|--------|------|
| `BlueprintFlowBuilder.tsx` | 워크플로우 빌더 메인 |
| `BlueprintFlowList.tsx` | 워크플로우 목록 |
| `BlueprintFlowTemplates.tsx` | 워크플로우 템플릿 |

#### pages/pid-overlay/

| 파일명 | 용도 |
|--------|------|
| `PIDOverlayPage.tsx` | P&ID 오버레이 페이지 |

### web-ui/src/services/ (서비스)

| 파일명 | 용도 |
|--------|------|
| `specService.ts` | API 스펙 로드 서비스 |
| `workflowService.ts` | 워크플로우 API 서비스 |

### web-ui/src/store/ (상태 관리)

| 파일명 | 용도 |
|--------|------|
| `workflowStore.ts` | 워크플로우 Zustand 스토어 |
| `apiConfigStore.ts` | API 설정 스토어 |

### web-ui/src/types/ (타입)

| 파일명 | 용도 |
|--------|------|
| `workflow.ts` | 워크플로우 타입 정의 |
| `api.ts` | API 응답 타입 정의 |
| `node.ts` | 노드 타입 정의 |

### web-ui/src/i18n/ (다국어)

| 파일명 | 용도 |
|--------|------|
| `index.ts` | i18n 설정 |
| `ko.json` | 한국어 번역 |
| `en.json` | 영어 번역 |

### web-ui/e2e/ (E2E 테스트)

| 파일명 | 용도 |
|--------|------|
| `navigation.spec.ts` | 네비게이션 테스트 |
| `dashboard.spec.ts` | 대시보드 테스트 |
| `api-settings.spec.ts` | API 설정 테스트 |
| `blueprint-ai-bom.spec.ts` | BOM 기본 테스트 |
| `blueprint-ai-bom-comprehensive.spec.ts` | BOM 상세 테스트 |

#### e2e/ui/

| 파일명 | 용도 |
|--------|------|
| `workflow.spec.ts` | 워크플로우 UI 테스트 |

#### e2e/fixtures/

| 파일명 | 용도 |
|--------|------|
| `api-fixtures.ts` | API 테스트 fixture |

### web-ui/public/ (정적 파일)

| 파일명 | 용도 |
|--------|------|
| `vite.svg` | Vite 로고 |
| `samples/` | 샘플 이미지 디렉토리 |

---

## 8. models/ 디렉토리 (451개)

### 공통 구조 (각 API별)

각 `models/{api-name}-api/` 디렉토리는 동일한 구조:

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | FastAPI 서버 진입점 |
| `Dockerfile` | Docker 이미지 빌드 |
| `requirements.txt` | Python 의존성 |
| `routers/` | API 라우터 |
| `services/` | 비즈니스 로직 |
| `models/` | AI 모델 파일 (가중치) |
| `utils/` | 유틸리티 함수 |
| `tests/` | 단위 테스트 |
| `uploads/` | 업로드 임시 저장 |
| `results/` | 처리 결과 저장 |
| `config/` | 설정 파일 |

### models/yolo-api/ (YOLO 검출)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | YOLO API 서버 |
| `routers/detection_router.py` | 검출 엔드포인트 |
| `services/detection_service.py` | YOLO 추론 서비스 |
| `services/defaults.py` | MODEL_DEFAULTS 프로파일 |
| `models/*.pt` | YOLO 가중치 파일 |
| `training/` | 학습 스크립트/데이터 |

### models/edocr2-v2-api/ (eDOCr2 OCR)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | eDOCr2 API 서버 |
| `routers/ocr_router.py` | OCR 엔드포인트 |
| `services/ocr_service.py` | eDOCr2 추론 서비스 |
| `services/defaults.py` | MODEL_DEFAULTS 프로파일 |

### models/edgnet-api/ (EDGNet 세그멘테이션)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | EDGNet API 서버 |
| `services/defaults.py` | MODEL_DEFAULTS 프로파일 |

### models/line-detector-api/ (라인 검출)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | Line Detector API 서버 |
| `services/defaults.py` | MODEL_DEFAULTS 프로파일 |
| `services/svg_generator.py` | SVG 생성기 |

### models/design-checker-api/ (설계 검증)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | Design Checker API 서버 |
| `routers/pipeline_router.py` | 파이프라인 라우터 |
| `services/yolo_service.py` | YOLO 연동 |
| `services/edocr2_service.py` | eDOCr2 연동 |

### models/pid-analyzer-api/ (P&ID 분석)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | PID Analyzer API 서버 |
| `routers/analysis_router.py` | 분석 라우터 |
| `routers/dwg_router.py` | DWG 파일 처리 |
| `services/analysis_service.py` | 연결 분석 서비스 |
| `services/dwg_service.py` | DWG 변환 서비스 |

### models/paddleocr-api/ (PaddleOCR)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | PaddleOCR API 서버 |

### models/tesseract-api/ (Tesseract)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | Tesseract API 서버 |

### models/trocr-api/ (TrOCR)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | TrOCR API 서버 |

### models/ocr-ensemble-api/ (OCR 앙상블)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | OCR Ensemble API 서버 |
| `services/voting_service.py` | 가중 투표 서비스 |

### models/surya-ocr-api/ (Surya OCR)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | Surya OCR API 서버 |

### models/doctr-api/ (DocTR)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | DocTR API 서버 |

### models/easyocr-api/ (EasyOCR)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | EasyOCR API 서버 |

### models/esrgan-api/ (ESRGAN 업스케일링)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | ESRGAN API 서버 |

### models/skinmodel-api/ (공차 분석)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | SkinModel API 서버 |

### models/vl-api/ (Vision-Language)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | VL API 서버 |

### models/knowledge-api/ (지식 그래프)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | Knowledge API 서버 |
| `services/neo4j_service.py` | Neo4j 연동 |
| `services/graphrag_service.py` | GraphRAG 서비스 |

---

## 9. blueprint-ai-bom/ 디렉토리 (365개)

### blueprint-ai-bom/ 루트

| 파일명 | 용도 |
|--------|------|
| `README.md` | BOM 시스템 문서 |

### blueprint-ai-bom/backend/

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | BOM 백엔드 API 서버 |
| `requirements.txt` | Python 의존성 |
| `Dockerfile` | Docker 빌드 |

### blueprint-ai-bom/frontend/

| 파일명 | 용도 |
|--------|------|
| `package.json` | npm 패키지 설정 |
| `vite.config.ts` | Vite 빌드 설정 |
| `src/` | React 소스 코드 |

### blueprint-ai-bom/models/

| 파일명 | 용도 |
|--------|------|
| `*.pt` | AI 모델 가중치 (988MB) |

---

## 10. docs/ 디렉토리 (88개)

| 파일명 | 용도 |
|--------|------|
| `INSTALLATION.md` | 설치 가이드 |
| `DEPLOYMENT.md` | 배포 가이드 |
| `API_REFERENCE.md` | API 레퍼런스 |
| `TROUBLESHOOTING.md` | 문제 해결 가이드 |
| `BLUEPRINTFLOW.md` | BlueprintFlow 사용 가이드 |
| `DEVELOPMENT.md` | 개발 가이드 |
| `TESTING.md` | 테스트 가이드 |
| `images/` | 문서 이미지 |

---

## 11. scripts/ 디렉토리 (43개)

| 파일명 | 용도 |
|--------|------|
| `create_api.py` | 새 API 스캐폴딩 스크립트 |
| `health_check.py` | 헬스체크 스크립트 |
| `backup.sh` | 백업 스크립트 |
| `deploy.sh` | 배포 스크립트 |
| `test_all.sh` | 전체 테스트 실행 |
| `cleanup.sh` | 정리 스크립트 |
| `docker_utils.sh` | Docker 유틸리티 |

---

## 12. monitoring/ 디렉토리 (7개)

| 파일명 | 용도 |
|--------|------|
| `prometheus.yml` | Prometheus 설정 |
| `grafana/` | Grafana 대시보드 설정 |
| `alertmanager.yml` | 알림 설정 |

---

## 13. data/ 디렉토리 (96개)

| 파일명 | 용도 |
|--------|------|
| `neo4j/` | Neo4j 데이터베이스 파일 |
| `samples/` | 샘플 데이터 |

---

## 14. rnd/ 디렉토리 (53개)

| 파일명 | 용도 |
|--------|------|
| `papers/` | R&D 논문 (35개) |
| `experiments/` | 실험 코드 |
| `models/` | 실험 모델 |

---

## 15. idea-thinking/ 디렉토리 (3개)

| 파일명 | 용도 |
|--------|------|
| `*.md` | 아이디어 정리 문서 |

---

## 16. apply-company/ 디렉토리 (362개)

| 파일명 | 용도 |
|--------|------|
| `techloss/` | 기술 손실 분석 자료 |
| `*.md` | 회사 지원 관련 문서 |

---

## 17. test-results/ 디렉토리 (1개)

| 파일명 | 용도 |
|--------|------|
| `.last-run.json` | Playwright 마지막 실행 정보 |

---

## 18. offline_models/ 디렉토리 (4.5GB)

| 파일명 | 용도 |
|--------|------|
| `*.pt`, `*.onnx` | 오프라인 배포용 AI 모델 가중치 |
| `yolo/` | YOLO 모델 |
| `ocr/` | OCR 모델 |
| `segmentation/` | 세그멘테이션 모델 |

---

**문서 끝**

> **작성자**: Claude Code (Opus 4.5)
> **총 파일**: ~2,000개 (주요 파일 기술)
