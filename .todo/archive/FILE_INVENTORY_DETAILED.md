# 전체 파일 상세 인벤토리

> **생성일**: 2026-01-17
> **목적**: /home/uproot/ax/poc 하위 모든 파일의 상세 용도 기술
> **총 파일 수**: ~2,048개 (node_modules, .git, __pycache__ 제외)

---

## 1. 루트 디렉토리 (33개 파일)

### 1.1 설정 파일 (6개)

| 파일명 | 용도 | 수정 빈도 |
|--------|------|-----------|
| `.editorconfig` | 에디터 공통 설정 (들여쓰기 2/4칸, UTF-8, LF) | 거의 없음 |
| `.env.example` | 환경변수 템플릿 (API URL, 포트, DB 설정, API 키) | 월 1회 |
| `.gitattributes` | Git 파일 처리 규칙 (LF 강제, binary 파일 지정) | 거의 없음 |
| `.gitignore` | Git 추적 제외 패턴 (node_modules, .env, uploads 등) | 필요 시 |
| `.mcp.json` | MCP 서버 설정 (playwright, repomix, context7 등) | 필요 시 |
| `.pre-commit-config.yaml` | pre-commit 훅 (ruff, prettier, eslint) | 필요 시 |

### 1.2 문서 파일 (16개)

| 파일명 | 용도 | 대상 독자 |
|--------|------|-----------|
| `CLAUDE.md` | Claude Code 프로젝트 가이드, LLM 컨텍스트 | AI/개발자 |
| `README.md` | 프로젝트 개요, 설치법, 사용법 | 신규 개발자 |
| `ARCHITECTURE.md` | 시스템 아키텍처 설계 (마이크로서비스 구조) | 아키텍트 |
| `ROADMAP.md` | 개발 로드맵, 마일스톤, 계획 | PM/개발자 |
| `WORKFLOWS.md` | BlueprintFlow 워크플로우 사용 가이드 | 사용자 |
| `QUICK_START.md` | 5분 안에 시작하기 가이드 | 신규 사용자 |
| `DEPLOYMENT_GUIDE.md` | Docker/K8s 배포 가이드 | DevOps |
| `KNOWN_ISSUES.md` | 알려진 이슈 목록 및 해결 방법 | 개발자 |
| `SKILL.md` | Claude Code 스킬 정의 파일 | AI |
| `API_AUTOMATION_COMPLETE_GUIDE.md` | API 자동화 구현 완료 문서 | 개발자 |
| `BLUEPRINTFLOW_FRONTEND_EXECUTE_COMPLETE.md` | BlueprintFlow 프론트 실행 구현 문서 | 개발자 |
| `BLUEPRINTFLOW_PHASE4_COMPLETION.md` | BlueprintFlow Phase4 완료 보고서 | PM |
| `DOCUMENTATION_UPDATE_SUMMARY.md` | 문서 업데이트 이력 요약 | 개발자 |
| `DYNAMIC_API_SYSTEM_GUIDE.md` | 동적 API 시스템 가이드 | 개발자 |
| `PROJECT_FILE_INVENTORY_REPORT.md` | 프로젝트 파일 인벤토리 보고서 | 관리자 |

### 1.3 Docker 설정 (5개)

| 파일명 | 용도 | 사용 시나리오 |
|--------|------|---------------|
| `docker-compose.yml` | 메인 Docker Compose (20개 서비스 정의) | 운영/개발 |
| `docker-compose.override.yml` | 로컬 개발용 오버라이드 (볼륨 마운트, 포트) | 로컬 개발 |
| `docker-compose.override.yml.example` | 오버라이드 템플릿 | 신규 환경 설정 |
| `docker-compose.monitoring.yml` | Grafana/Prometheus/Loki 스택 | 모니터링 |
| `docker-compose.offline.yml` | 오프라인 환경 배포 (네트워크 격리) | 폐쇄망 |

### 1.4 빌드/자동화 (1개)

| 파일명 | 용도 | 주요 타겟 |
|--------|------|-----------|
| `Makefile` | 빌드/테스트/배포 자동화 | dev, test, build, deploy |

### 1.5 테스트 파일 (3개)

| 파일명 | 용도 |
|--------|------|
| `test_blueprintflow_scenarios.py` | BlueprintFlow 시나리오 통합 테스트 |
| `test_control_flow.py` | IF/Loop/Merge 제어 노드 단위 테스트 |
| `test_workflow_order.py` | 워크플로우 실행 순서 검증 테스트 |

### 1.6 데이터 파일 (2개)

| 파일명 | 용도 |
|--------|------|
| `TECHCROSS_BWMS_Analysis_Report.xlsx` | BWMS 분석 보고서 v1 |
| `TECHCROSS_BWMS_Analysis_Report_v2.xlsx` | BWMS 분석 보고서 v2 (개선) |

### 1.7 심볼릭 링크 (1개)

| 파일명 | 대상 | 용도 |
|--------|------|------|
| `api-guide-sample` | /home/uproot/ax/ax-api-sample | API 가이드 샘플 참조 |

---

## 2. .claude/ 디렉토리 (25개 파일)

### 2.1 commands/ (7개) - 커스텀 슬래시 명령어

| 파일명 | 명령어 | 용도 |
|--------|--------|------|
| `README.md` | - | 커스텀 명령어 사용 가이드 |
| `add-feature.md` | `/add-feature` | 새 API 기능 추가 워크플로우 |
| `debug-issue.md` | `/debug-issue` | 이슈 디버깅 체계적 워크플로우 |
| `handoff.md` | `/handoff` | 세션 핸드오프 (컨텍스트 인계) |
| `rebuild-service.md` | `/rebuild-service` | Docker 서비스 안전 재빌드 |
| `test-api.md` | `/test-api` | API 엔드포인트 테스트 |
| `track-issue.md` | `/track-issue` | KNOWN_ISSUES.md에 이슈 추적 |

### 2.2 skills/ (12개) - 온디맨드 스킬 가이드

| 파일명 | 트리거 | 용도 |
|--------|--------|------|
| `README.md` | - | 스킬 시스템 사용 가이드 |
| `api-creation-guide.md` | "새 API" | 새 API 생성 6단계 체크리스트 |
| `code-janitor.md` | "정리" | 코드 정리/리팩토링 가이드 |
| `context-engineering-guide.md` | "컨텍스트" | 컨텍스트 효율화 가이드 |
| `devops-guide.md` | "CI", "배포" | CI/CD 파이프라인 가이드 |
| `doc-updater.md` | "문서" | 문서 업데이트 가이드 |
| `feature-implementer.md` | "기능" | 기능 구현 워크플로우 |
| `modularization-guide.md` | "모듈화" | 1000줄 규칙, 분리 패턴 |
| `project-reference.md` | "참조" | R&D 논문, API 스펙 참조 |
| `ux-enhancer.md` | "UX" | UX 개선 가이드 |
| `version-history.md` | "버전" | BOM/Design Checker 버전 히스토리 |
| `workflow-optimizer.md` | "최적화" | 워크플로우 최적화 가이드 |

### 2.3 hooks/ (4개) - 자동화 훅

| 파일명 | 트리거 | 용도 |
|--------|--------|------|
| `README.md` | - | 훅 시스템 설명 |
| `on-stop.sh` | 세션 종료 시 | 정리 작업 |
| `post-bash-log.sh` | Bash 실행 후 | 명령 로깅 |
| `pre-edit-check.sh` | 파일 편집 전 | 파일 크기 검증 (1000줄) |

### 2.4 templates/ (1개)

| 파일명 | 용도 |
|--------|------|
| `change-summary-template.md` | 변경 요약 템플릿 |

### 2.5 설정 (1개)

| 파일명 | 용도 |
|--------|------|
| `settings.local.json` | 로컬 개인 설정 (gitignore됨) |

---

## 3. .github/ 디렉토리 (4개 파일)

| 파일명 | 용도 |
|--------|------|
| `CODEOWNERS` | 코드 소유자 정의 (PR 리뷰어 자동 지정) |
| `dependabot.yml` | 의존성 자동 업데이트 설정 (주 1회) |
| `workflows/ci.yml` | CI 파이프라인 (lint, test, build on push/PR) |
| `workflows/cd.yml` | CD 파이프라인 (deploy on CI success) |

---

## 4. .todo/ 디렉토리 (24개 파일)

### 4.1 활성 문서 (11개)

| 파일명 | 용도 |
|--------|------|
| `ACTIVE.md` | 현재 진행 중인 작업 목록 |
| `BACKLOG.md` | 백로그 및 향후 작업 |
| `COMPLETED.md` | 완료된 작업 아카이브 |
| `DIRECTORY_AUDIT_PLAN.md` | 디렉토리 감사 계획 및 결과 |
| `AUDIT_PHASE1_CORE.md` | 핵심 코드 감사 (web-ui, gateway-api, models) |
| `AUDIT_PHASE2_INFRA.md` | 인프라 감사 (.claude, .github, scripts) |
| `AUDIT_PHASE3_DOCS.md` | 문서 감사 (docs, rnd, notion) |
| `AUDIT_PHASE4_DATA.md` | 데이터 감사 (offline_models, data) |
| `AUDIT_PHASE5_TEMP.md` | 임시 파일 감사 (experiments, backend) |
| `AUDIT_PHASE6_MISC.md` | 기타 감사 (.todo, apply-company) |
| `FILE_INVENTORY.md` | 전체 파일 인벤토리 요약 |

### 4.2 아카이브 (13개) - archive/

| 파일명 | 내용 |
|--------|------|
| `00_SUMMARY.md` | 프로젝트 요약 |
| `01_NEW_API_CHECKLIST.md` | 새 API 추가 체크리스트 |
| `02_VISUALIZATION_EXTENSION.md` | 시각화 확장 계획 |
| `03_MODEL_CONFIG_PATTERN.md` | MODEL_DEFAULTS 패턴 문서 |
| `04_GATEWAY_SERVICE_SEPARATION.md` | Gateway 서비스 분리 계획 |
| `05_CLEANUP_TASKS.md` | 정리 작업 목록 |
| `06_TEST_COVERAGE.md` | 테스트 커버리지 계획 |
| `07_DESIGN_CHECKER_PIPELINE_INTEGRATION.md` | Design Checker 통합 |
| `08_FEATURE_IMPLICATION_SYSTEM.md` | Feature Implication 시스템 |
| `09_NODE_DEFINITIONS_SYNC.md` | 노드 정의 동기화 |
| `10_BLUEPRINT_BOM_GT_SYSTEM.md` | BOM GT 시스템 |
| `E2E_TESTS_ORGANIZATION.md` | E2E 테스트 조직화 |
| `TOAST_MIGRATION_ANALYSIS.md` | Toast 마이그레이션 분석 |
| `UX_IMPROVEMENT_TOAST_LOADING.md` | UX Toast/로딩 개선 |

---

## 5. .vscode/ 디렉토리 (2개 파일)

| 파일명 | 용도 |
|--------|------|
| `settings.json` | VSCode 프로젝트 설정 (포매터, 린터, 경로) |
| `extensions.json` | 권장 확장 프로그램 목록 |

---

## 6. gateway-api/ 디렉토리 (148개 파일)

### 6.1 루트 파일 (11개)

| 파일명 | 용도 |
|--------|------|
| `api_server.py` | FastAPI 메인 서버 진입점 |
| `api_registry.py` | 동적 API 레지스트리 관리 |
| `cost_estimator.py` | 비용/시간 추정기 |
| `pdf_generator.py` | PDF 보고서 생성기 |
| `requirements.txt` | Python 의존성 (fastapi, httpx, pydantic 등) |
| `Dockerfile` | Docker 이미지 빌드 |
| `docker-compose.yml` | 단독 실행용 compose |
| `pytest.ini` | pytest 설정 |
| `README.md` | Gateway API 문서 |
| `IMPLEMENTATION_SUMMARY.md` | 구현 요약 |
| `REFACTORING_PLAN.md` | 리팩토링 계획 |

### 6.2 api_specs/ (24개) - OpenAPI 스펙

| 파일명 | API | profiles |
|--------|-----|----------|
| `yolo.yaml` | YOLO 검출 | ✅ 3개 |
| `edocr2.yaml` | eDOCr2 OCR | ✅ 7개 |
| `edgnet.yaml` | EDGNet 세그멘테이션 | ✅ 5개 |
| `line-detector.yaml` | Line Detector | ✅ 4개 |
| `design-checker.yaml` | Design Checker | - |
| `paddleocr.yaml` | PaddleOCR | - |
| `tesseract.yaml` | Tesseract OCR | - |
| `trocr.yaml` | TrOCR | - |
| `ocr-ensemble.yaml` | OCR Ensemble | - |
| `suryaocr.yaml` | Surya OCR | - |
| `doctr.yaml` | DocTR | - |
| `easyocr.yaml` | EasyOCR | - |
| `esrgan.yaml` | ESRGAN | - |
| `skinmodel.yaml` | SkinModel | - |
| `vl.yaml` | Vision-Language | - |
| `knowledge.yaml` | Knowledge | - |
| `pidanalyzer.yaml` | PID Analyzer | - |
| `blueprint-ai-bom.yaml` | Blueprint AI BOM | - |
| `pid-composer.yaml` | PID Composer | - |
| `gtcomparison.yaml` | GT Comparison | - |
| `pdfexport.yaml` | PDF Export | - |
| `excelexport.yaml` | Excel Export | - |
| `pidfeatures.yaml` | PID Features | - |
| `verificationqueue.yaml` | Verification Queue | - |
| `CONVENTIONS.md` | 스펙 작성 규칙 |
| `api_spec_schema.json` | 스펙 JSON 스키마 |

### 6.3 routers/ (14개) - API 라우터

| 파일명 | 엔드포인트 |
|--------|------------|
| `__init__.py` | 라우터 패키지 초기화 |
| `admin_router.py` | /api/admin/* (관리 기능) |
| `api_key_router.py` | /api/keys/* (API 키 관리) |
| `config_router.py` | /api/config/* (설정 조회) |
| `container_router.py` | /api/containers/* (Docker 관리) |
| `docker_router.py` | /api/docker/* (Docker 상태) |
| `download_router.py` | /api/download/* (파일 다운로드) |
| `gpu_config_router.py` | /api/gpu/* (GPU 설정) |
| `process_router.py` | /api/process/* (이미지 처리) |
| `quote_router.py` | /api/quote/* (견적 생성) |
| `registry_router.py` | /api/registry/* (API 레지스트리) |
| `results_router.py` | /api/results/* (결과 조회) |
| `spec_router.py` | /api/specs/* (API 스펙 제공) |
| `workflow_router.py` | /api/workflow/* (워크플로우 실행) |

### 6.4 services/ (9개) - 비즈니스 로직

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 서비스 패키지 초기화 |
| `api_key_service.py` | API 키 생성/검증 |
| `ensemble_service.py` | OCR 앙상블 투표 |
| `ocr_service.py` | OCR API 호출 통합 |
| `quote_service.py` | 견적 계산 로직 |
| `segmentation_service.py` | 세그멘테이션 처리 |
| `tolerance_service.py` | 공차 분석 |
| `vl_service.py` | Vision-Language 호출 |
| `yolo_service.py` | YOLO API 호출 |

### 6.5 blueprintflow/ (34개) - 워크플로우 엔진

#### blueprintflow/engine/ (4개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 엔진 패키지 초기화 |
| `execution_context.py` | 실행 컨텍스트 관리 |
| `input_collector.py` | 입력 수집/검증 |
| `pipeline_engine.py` | DAG 파이프라인 실행 엔진 |

#### blueprintflow/executors/ (28개) - 노드 실행기

| 파일명 | 노드 타입 |
|--------|----------|
| `__init__.py` | Executor 패키지 초기화 |
| `base_executor.py` | 기본 Executor 추상 클래스 |
| `executor_registry.py` | Executor 등록/조회 |
| `generic_api_executor.py` | 범용 API Executor |
| `image_utils.py` | 이미지 처리 유틸리티 |
| `yolo_executor.py` | YOLO 노드 (검출) |
| `edocr2_executor.py` | eDOCr2 노드 (OCR) |
| `edgnet_executor.py` | EDGNet 노드 (세그멘테이션) |
| `paddleocr_executor.py` | PaddleOCR 노드 |
| `tesseract_executor.py` | Tesseract 노드 |
| `trocr_executor.py` | TrOCR 노드 |
| `ocr_ensemble_executor.py` | OCR Ensemble 노드 |
| `suryaocr_executor.py` | Surya OCR 노드 |
| `doctr_executor.py` | DocTR 노드 |
| `easyocr_executor.py` | EasyOCR 노드 |
| `esrgan_executor.py` | ESRGAN 노드 (업스케일링) |
| `skinmodel_executor.py` | SkinModel 노드 (공차) |
| `vl_executor.py` | VL 노드 (Vision-Language) |
| `knowledge_executor.py` | Knowledge 노드 (GraphRAG) |
| `linedetector_executor.py` | Line Detector 노드 |
| `pidanalyzer_executor.py` | PID Analyzer 노드 |
| `designchecker_executor.py` | Design Checker 노드 |
| `bom_executor.py` | Blueprint AI BOM 노드 |
| `if_executor.py` | IF 제어 노드 |
| `loop_executor.py` | Loop 제어 노드 |
| `merge_executor.py` | Merge 제어 노드 |
| `imageinput_executor.py` | ImageInput 노드 |
| `textinput_executor.py` | TextInput 노드 |
| `gtcomparison_executor.py` | GT Comparison 노드 |
| `pdfexport_executor.py` | PDF Export 노드 |
| `excelexport_executor.py` | Excel Export 노드 |
| `pidfeatures_executor.py` | PID Features 노드 |
| `verificationqueue_executor.py` | Verification Queue 노드 |
| `test_executor.py` | 테스트용 Executor |

#### blueprintflow/schemas/ (2개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 스키마 패키지 초기화 |
| `workflow.py` | 워크플로우 Pydantic 모델 |

#### blueprintflow/validators/ (3개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 검증기 패키지 초기화 |
| `dag_algorithms.py` | DAG 알고리즘 (토폴로지 정렬, 사이클 검출) |
| `dag_validator.py` | DAG 유효성 검증 |

### 6.6 adapters/ (3개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 어댑터 패키지 초기화 |
| `base_adapter.py` | 기본 어댑터 클래스 |
| `ocr_adapter.py` | OCR 결과 어댑터 |

### 6.7 config/ (2개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 설정 패키지 초기화 |
| `ocr_defaults.py` | OCR 기본 설정 |

### 6.8 constants/ (3개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 상수 패키지 초기화 |
| `directories.py` | 디렉토리 경로 상수 |
| `docker_services.py` | Docker 서비스 이름/포트 매핑 |

### 6.9 models/ (3개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 모델 패키지 초기화 |
| `request.py` | 요청 Pydantic 모델 |
| `response.py` | 응답 Pydantic 모델 |

### 6.10 utils/ (14개)

| 파일명 | 기능 |
|--------|------|
| `__init__.py` | 유틸리티 패키지 초기화 |
| `alerting.py` | 알림 발송 |
| `file_validator.py` | 파일 유효성 검증 |
| `filters.py` | 데이터 필터링 |
| `helpers.py` | 범용 헬퍼 함수 |
| `image_utils.py` | 이미지 처리 |
| `log_manager.py` | 로그 관리 |
| `logger.py` | 로깅 설정 |
| `logging_middleware.py` | 로깅 미들웨어 |
| `progress.py` | 진행률 추적 |
| `result_manager.py` | 결과 저장/조회 |
| `spec_loader.py` | API 스펙 로드 |
| `subprocess_utils.py` | 서브프로세스 실행 |
| `visualization.py` | 시각화 유틸리티 |

### 6.11 tests/ (15개)

| 파일명 | 테스트 대상 |
|--------|-------------|
| `__init__.py` | 테스트 패키지 초기화 |
| `conftest.py` | pytest fixture 설정 |
| `test_admin_router.py` | 관리 API 테스트 |
| `test_api_registry.py` | API 레지스트리 테스트 |
| `test_dag_validator.py` | DAG 검증 테스트 |
| `test_docker_router.py` | Docker API 테스트 |
| `test_download_router.py` | 다운로드 API 테스트 |
| `test_executor_registry.py` | Executor 레지스트리 테스트 |
| `test_executors.py` | Executor 통합 테스트 |
| `test_executors_unit.py` | Executor 단위 테스트 |
| `test_file_validator.py` | 파일 검증 테스트 |
| `test_gpu_config_router.py` | GPU 설정 API 테스트 |
| `test_process_router.py` | 처리 API 테스트 |
| `test_quote_router.py` | 견적 API 테스트 |
| `test_registry_endpoints.py` | 레지스트리 엔드포인트 테스트 |
| `test_results_router.py` | 결과 API 테스트 |
| `test_workflow_schemas.py` | 워크플로우 스키마 테스트 |

### 6.12 기타 (3개)

| 파일명 | 기능 |
|--------|------|
| `docs/openapi.json` | 생성된 OpenAPI 스펙 |
| `scripts/export_openapi.py` | OpenAPI 내보내기 스크립트 |
| `TESTING_LOGGING_GUIDE.md` | 테스트/로깅 가이드 |

---

## 7. web-ui/ 디렉토리 (163개 파일)

### 7.1 루트 설정 파일 (15개)

| 파일명 | 용도 |
|--------|------|
| `package.json` | npm 패키지 및 스크립트 정의 |
| `package-lock.json` | 의존성 잠금 파일 |
| `vite.config.ts` | Vite 빌드 설정 |
| `tsconfig.json` | TypeScript 메인 설정 |
| `tsconfig.app.json` | 앱용 TypeScript 설정 |
| `tsconfig.node.json` | Node용 TypeScript 설정 |
| `tailwind.config.js` | Tailwind CSS 설정 |
| `postcss.config.js` | PostCSS 설정 |
| `eslint.config.js` | ESLint 설정 |
| `playwright.config.ts` | Playwright E2E 테스트 설정 |
| `index.html` | HTML 진입점 |
| `Dockerfile` | 프로덕션 Docker 빌드 |
| `Dockerfile.dev` | 개발 Docker 빌드 |
| `nginx.conf` | Nginx 설정 (프로덕션) |
| `README.md` | 프론트엔드 문서 |

### 7.2 src/ 루트 (5개)

| 파일명 | 용도 |
|--------|------|
| `main.tsx` | React 앱 진입점 |
| `App.tsx` | 메인 앱 컴포넌트 (라우팅) |
| `index.css` | 전역 CSS (Tailwind) |
| `vite-env.d.ts` | Vite 타입 정의 |
| `i18n.ts` | i18n 설정 |

### 7.3 src/components/ (55개)

#### blueprintflow/ (18개)

| 파일명 | 기능 |
|--------|------|
| `NodeDetailPanel.tsx` | 노드 상세/파라미터 패널 (프로파일 선택 포함) |
| `NodePalette.tsx` | 노드 팔레트 메인 |
| `DebugPanel.tsx` | 디버그 패널 |
| `DataTableView.tsx` | 데이터 테이블 뷰 |
| `PipelineConclusionCard.tsx` | 파이프라인 결과 카드 |
| `ResultSummaryCard.tsx` | 결과 요약 카드 |
| `VisualizationImage.tsx` | 시각화 이미지 |
| `outputExtractors.ts` | 출력 추출 함수 |
| `node-palette/index.ts` | 노드 팔레트 내보내기 |
| `node-palette/constants.ts` | 팔레트 상수 |
| `node-palette/types.ts` | 팔레트 타입 |
| `node-palette/components/` | 컴포넌트 (NodeItem, NodeCategory 등) |
| `node-palette/hooks/` | 훅 (useNodePalette, useContainerStatus) |
| `nodes/BaseNode.tsx` | 기본 노드 렌더링 |
| `nodes/DynamicNode.tsx` | 동적 노드 렌더링 |
| `nodes/ApiNodes.tsx` | API 노드 정의 |
| `nodes/ControlNodes.tsx` | 제어 노드 정의 |
| `nodes/index.ts` | 노드 내보내기 |

#### monitoring/ (8개)

| 파일명 | 기능 |
|--------|------|
| `APIStatusMonitor.tsx` | API 상태 모니터링 대시보드 |
| `ServiceHealthCard.tsx` | 서비스 헬스 카드 |
| `constants.ts` | 모니터링 상수 |
| `types.ts` | 모니터링 타입 |
| `components/QuickStats.tsx` | 빠른 통계 |
| `components/ResourcePanel.tsx` | 리소스 패널 |
| `components/index.ts` | 컴포넌트 내보내기 |
| `hooks/useResourceStats.ts` | 리소스 통계 훅 |

#### debug/ (9개)

| 파일명 | 기능 |
|--------|------|
| `YOLOVisualization.tsx` | YOLO 검출 시각화 |
| `OCRVisualization.tsx` | OCR 결과 시각화 |
| `SegmentationVisualization.tsx` | 세그멘테이션 시각화 |
| `ToleranceVisualization.tsx` | 공차 시각화 |
| `PipelineStepsVisualization.tsx` | 파이프라인 단계 시각화 |
| `FileUploader.tsx` | 파일 업로드 |
| `JSONViewer.tsx` | JSON 뷰어 |
| `RequestInspector.tsx` | 요청 검사기 |
| `RequestTimeline.tsx` | 요청 타임라인 |
| `ErrorPanel.tsx` | 에러 패널 |

#### ui/ (13개) - 공통 UI

| 파일명 | 컴포넌트 |
|--------|----------|
| `Button.tsx` | 버튼 |
| `Card.tsx` | 카드 |
| `Badge.tsx` | 배지 |
| `Toast.tsx` | 토스트 알림 |
| `Tooltip.tsx` | 툴팁 |
| `ImageZoom.tsx` | 이미지 줌 |
| `Mermaid.tsx` | Mermaid 다이어그램 |
| `PipelineProgress.tsx` | 파이프라인 진행률 |

#### 기타 (7개)

| 파일명 | 기능 |
|--------|------|
| `ErrorBoundary.tsx` | 에러 바운더리 |
| `layout/Header.tsx` | 헤더 |
| `layout/Sidebar.tsx` | 사이드바 |
| `layout/Layout.tsx` | 레이아웃 |
| `pid/PIDOverlayViewer.tsx` | P&ID SVG 오버레이 |
| `upload/FileDropzone.tsx` | 파일 드롭존 |
| `upload/SampleFileGrid.tsx` | 샘플 파일 그리드 |

### 7.4 src/config/ (15개)

| 파일명 | 기능 |
|--------|------|
| `api.ts` | API 엔드포인트 설정 |
| `apiRegistry.ts` | API 레지스트리 |
| `nodeDefinitions.ts` | 노드 정의 메인 (28개 노드) |
| `nodeDefinitions.test.ts` | 노드 정의 테스트 |
| `nodes/types.ts` | 노드 타입 정의 |
| `nodes/index.ts` | 노드 내보내기 |
| `nodes/inputNodes.ts` | Input 노드 |
| `nodes/detectionNodes.ts` | Detection 노드 |
| `nodes/ocrNodes.ts` | OCR 노드 |
| `nodes/segmentationNodes.ts` | Segmentation 노드 |
| `nodes/preprocessingNodes.ts` | Preprocessing 노드 |
| `nodes/analysisNodes.ts` | Analysis 노드 |
| `nodes/bomNodes.ts` | BOM 노드 |
| `nodes/knowledgeNodes.ts` | Knowledge 노드 |
| `nodes/aiNodes.ts` | AI 노드 |
| `nodes/controlNodes.ts` | Control 노드 |
| `features/index.ts` | 피처 플래그 |
| `features/featureDefinitions.ts` | 피처 정의 |
| `features/featureConverters.ts` | 피처 변환기 |

### 7.5 src/hooks/ (6개)

| 파일명 | 기능 |
|--------|------|
| `useNodeDefinitions.ts` | 노드 정의 로드 (정적+동적 병합) |
| `useAPIRegistry.ts` | API 레지스트리 훅 |
| `useEstimatedTime.ts` | 예상 시간 훅 |
| `useHyperParameters.ts` | 하이퍼파라미터 훅 |
| `useToast.tsx` | 토스트 알림 훅 |

### 7.6 src/pages/ (25개)

| 파일명 | 페이지 |
|--------|--------|
| `Landing.tsx` | 랜딩 페이지 |
| `dashboard/Dashboard.tsx` | 대시보드 메인 |
| `dashboard/Guide.tsx` | 가이드 페이지 |
| `dashboard/guide/sections/*` | 가이드 섹션 (10개) |
| `admin/Admin.tsx` | 관리자 메인 |
| `admin/APIDetail.tsx` | API 상세 |
| `admin/api-detail/*` | API 상세 컴포넌트 |
| `blueprintflow/BlueprintFlowBuilder.tsx` | 워크플로우 빌더 |
| `blueprintflow/BlueprintFlowList.tsx` | 워크플로우 목록 |
| `blueprintflow/BlueprintFlowTemplates.tsx` | 템플릿 갤러리 |
| `blueprintflow/components/*` | 빌더 컴포넌트 |
| `blueprintflow/hooks/*` | 빌더 훅 |
| `docs/Docs.tsx` | 문서 페이지 |
| `pid-overlay/PIDOverlayPage.tsx` | P&ID 오버레이 페이지 |

### 7.7 src/services/ (3개)

| 파일명 | 기능 |
|--------|------|
| `specService.ts` | API 스펙 로드 (profiles 파싱 포함) |
| `specService.test.ts` | 스펙 서비스 테스트 |
| `apiRegistryService.ts` | API 레지스트리 서비스 |

### 7.8 src/store/ (5개)

| 파일명 | Zustand 스토어 |
|--------|---------------|
| `workflowStore.ts` | 워크플로우 상태 |
| `workflowStore.test.ts` | 워크플로우 스토어 테스트 |
| `apiConfigStore.ts` | API 설정 상태 |
| `apiConfigStore.test.ts` | API 설정 스토어 테스트 |
| `monitoringStore.ts` | 모니터링 상태 |
| `uiStore.ts` | UI 상태 |

### 7.9 src/types/ (2개)

| 파일명 | 타입 정의 |
|--------|----------|
| `api.ts` | API 응답 타입 |
| `common.ts` | 공통 타입 |

### 7.10 src/utils/ (3개)

| 파일명 | 기능 |
|--------|------|
| `specToHyperparams.ts` | 스펙→하이퍼파라미터 변환 |
| `svgOverlay.ts` | SVG 오버레이 유틸리티 |
| `svgOverlay.test.ts` | SVG 오버레이 테스트 |

### 7.11 src/locales/ (2개)

| 파일명 | 언어 |
|--------|------|
| `ko.json` | 한국어 번역 |
| `en.json` | 영어 번역 |

### 7.12 e2e/ (45개) - E2E 테스트

| 파일명 | 테스트 대상 |
|--------|-------------|
| `navigation.spec.ts` | 네비게이션 테스트 |
| `dashboard.spec.ts` | 대시보드 테스트 |
| `api-settings.spec.ts` | API 설정 테스트 |
| `blueprint-ai-bom.spec.ts` | BOM 기본 테스트 |
| `blueprint-ai-bom-comprehensive.spec.ts` | BOM 상세 테스트 |
| `blueprintflow.spec.ts` | 워크플로우 테스트 |
| `hyperparameter-*.spec.ts` | 하이퍼파라미터 테스트 |
| `node-comprehensive.spec.ts` | 노드 통합 테스트 |
| `pid-analysis.spec.ts` | P&ID 분석 테스트 |
| `templates.spec.ts` | 템플릿 테스트 |
| `ui/workflow.spec.ts` | 워크플로우 UI 테스트 |
| `api/*.spec.ts` | API 테스트 (15개) |
| `fixtures/api-fixtures.ts` | API 테스트 fixture |
| `fixtures/images/*` | 테스트 이미지 (3개) |
| `plan/*.md` | 테스트 계획 (9개) |

---

## 8. models/ 디렉토리 (20개 API, 각 15-40개 파일)

### 8.1 공통 구조 (각 API별)

```
models/{api-name}-api/
├── api_server.py          # FastAPI 서버 진입점
├── Dockerfile             # Docker 빌드
├── requirements.txt       # Python 의존성
├── README.md              # API 문서
├── routers/               # API 라우터
│   └── {feature}_router.py
├── services/              # 비즈니스 로직
│   ├── defaults.py        # MODEL_DEFAULTS (일부)
│   └── {feature}_service.py
├── models/                # AI 모델/스키마
│   └── schemas.py
├── utils/                 # 유틸리티
├── config/                # 설정
│   └── defaults.py
└── tests/                 # 테스트
```

### 8.2 개별 API 상세

#### yolo-api/ (YOLO 검출)

| 파일명 | 기능 |
|--------|------|
| `api_server.py` | YOLO v11 FastAPI 서버 |
| `routers/detection_router.py` | /detect 엔드포인트 |
| `services/detection_service.py` | YOLO 추론 |
| `services/defaults.py` | MODEL_DEFAULTS (3 profiles) |
| `models/*.pt` | YOLO 가중치 (bom_detector, pid_detector) |
| `training/` | 학습 스크립트 |

#### edocr2-v2-api/ (eDOCr2 OCR)

| 파일명 | 기능 |
|--------|------|
| `api_server.py` | eDOCr2 v2 FastAPI 서버 |
| `edocr2_src/` | eDOCr2 소스 코드 |
| `edocr_v1/` | eDOCr v1 호환 레이어 |
| `enhancers/` | 전처리 향상기 |
| `services/defaults.py` | MODEL_DEFAULTS (7 profiles) |
| `models/*.keras` | Keras 모델 |

#### edgnet-api/ (EDGNet 세그멘테이션)

| 파일명 | 기능 |
|--------|------|
| `api_server.py` | EDGNet FastAPI 서버 |
| `edgnet_src/` | EDGNet 소스 (그래프, 벡터화) |
| `services/inference.py` | 추론 서비스 |
| `services/unet_inference.py` | UNet 추론 |
| `config/defaults.py` | MODEL_DEFAULTS (5 profiles) |

#### line-detector-api/ (라인 검출)

| 파일명 | 기능 |
|--------|------|
| `api_server.py` | Line Detector FastAPI 서버 |
| `services/svg_generator.py` | SVG 생성기 |
| `config/defaults.py` | MODEL_DEFAULTS (4 profiles) |

#### design-checker-api/ (설계 검증)

| 파일명 | 기능 |
|--------|------|
| `api_server.py` | Design Checker FastAPI 서버 |
| `bwms/` | BWMS 체커 모듈 |
| `config/*.yaml` | 규칙 설정 (ECS, HYCHLOR) |
| `routers/pipeline_router.py` | 파이프라인 라우터 |
| `services/yolo_service.py` | YOLO 연동 |
| `services/edocr2_service.py` | eDOCr2 연동 |

#### pid-analyzer-api/ (P&ID 분석)

| 파일명 | 기능 |
|--------|------|
| `api_server.py` | PID Analyzer FastAPI 서버 |
| `routers/analysis_router.py` | 분석 라우터 |
| `routers/dwg_router.py` | DWG 변환 라우터 |
| `services/analysis_service.py` | 연결 분석 |
| `services/dwg_service.py` | DWG→PNG 변환 |

#### 기타 OCR API (8개)

| API | 특징 |
|-----|------|
| `paddleocr-api` | 다국어 OCR (PP-OCR) |
| `tesseract-api` | Google Tesseract LSTM |
| `trocr-api` | Transformer OCR (필기체) |
| `ocr-ensemble-api` | 4엔진 가중 투표 |
| `surya-ocr-api` | 90+ 언어 지원 |
| `doctr-api` | 2단계 파이프라인 |
| `easyocr-api` | 80+ 언어 지원 |

#### 기타 API

| API | 특징 |
|-----|------|
| `esrgan-api` | 4x 이미지 업스케일링 |
| `skinmodel-api` | 공차 스택업 분석 |
| `vl-api` | Qwen2-VL Vision-Language |
| `knowledge-api` | Neo4j + GraphRAG |
| `pid-composer-api` | SVG 오버레이 생성 |

### 8.3 models/shared/ (공유 모듈)

| 파일명 | 기능 |
|--------|------|
| `utils.py` | 공유 유틸리티 |

---

## 9. 기타 디렉토리

### 9.1 blueprint-ai-bom/ (Human-in-the-Loop BOM)

```
blueprint-ai-bom/
├── README.md
├── ROADMAP.md
├── backend/
│   ├── api_server.py
│   ├── routers/
│   │   ├── analysis/      # 분석 라우터
│   │   ├── pid_features/  # P&ID 피처 라우터
│   │   ├── bom_router.py
│   │   ├── detection_router.py
│   │   └── ...
│   └── schemas/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── config/
└── models/
    └── *.pt               # AI 웨이트 (988MB)
```

### 9.2 docs/ (88개 문서)

| 디렉토리 | 내용 |
|----------|------|
| `docs/` | 설치/배포/트러블슈팅 가이드 |
| `docs/api/` | 각 API 파라미터 문서 (14개) |
| `docs/blueprintflow/` | 워크플로우 가이드 (10개) |
| `docs/developer/` | 개발자 가이드 (7개) |
| `docs/dockerization/` | Docker화 가이드 (5개) |
| `docs/insights/` | 벤치마크/분석 보고서 (15개) |
| `docs/papers/` | R&D 논문 요약 (15개) |
| `docs/references/` | 참조 문서 (PDF) |
| `docs/technical/` | 기술 문서 |
| `docs/user/` | 사용자 가이드 (3개) |

### 9.3 scripts/ (43개 스크립트)

| 카테고리 | 스크립트 |
|----------|----------|
| **API 생성** | `create_api.py` |
| **학습** | `train_yolo.py`, `train_edgnet_*.py`, `retrain_edgnet_gpu.py` |
| **데이터** | `augment_edgnet_*.py`, `merge_datasets.py`, `prepare_dataset.py` |
| **평가** | `evaluate_yolo.py`, `inference_yolo.py` |
| **배포** | `deployment/export_images.sh`, `deployment/install.sh` |
| **관리** | `management/backup.sh`, `management/health_check.sh` |
| **테스트** | `tests/test_*.py` (7개) |

### 9.4 monitoring/ (7개)

| 파일명 | 기능 |
|--------|------|
| `README.md` | 모니터링 설정 가이드 |
| `prometheus/prometheus.yml` | Prometheus 스크랩 설정 |
| `grafana/provisioning/dashboards/` | Grafana 대시보드 |
| `grafana/provisioning/datasources/` | 데이터소스 설정 |
| `loki/loki-config.yml` | Loki 로그 수집 설정 |
| `promtail/promtail-config.yml` | Promtail 설정 |

### 9.5 data/ (Neo4j 데이터)

| 디렉토리 | 내용 |
|----------|------|
| `data/neo4j/data/` | Neo4j 데이터베이스 |
| `data/neo4j/logs/` | Neo4j 로그 |
| `data/neo4j/plugins/` | APOC 플러그인 |

### 9.6 rnd/ (R&D 자료)

| 디렉토리 | 내용 |
|----------|------|
| `rnd/README.md` | R&D 개요 |
| `rnd/IMPLEMENTATION_DETAILS.md` | 구현 상세 |
| `rnd/SOTA_GAP_ANALYSIS.md` | SOTA 갭 분석 |
| `rnd/TRAINING_GUIDES.md` | 학습 가이드 |
| `rnd/experiments/` | 실험 코드/결과 |
| `rnd/papers/` | 논문 참조 |

### 9.7 idea-thinking/ (아이디어)

| 파일명 | 내용 |
|--------|------|
| `README.md` | 아이디어 정리 개요 |
| `main/001_doclayout_yolo_integration.md` | DocLayout YOLO 통합 아이디어 |
| `sub/001_doclayout_yolo_finetuning.md` | 파인튜닝 세부 계획 |

### 9.8 apply-company/ (362개)

회사 지원 관련 자료 (techloss 분석, 테스트 데이터)

---

## 10. 요약 통계

| 디렉토리 | 파일 수 | 주요 내용 |
|----------|---------|----------|
| 루트 | 33 | 설정, 문서, Docker |
| .claude | 25 | 커맨드, 스킬, 훅 |
| .github | 4 | CI/CD 워크플로우 |
| .todo | 24 | 작업 관리, 감사 문서 |
| .vscode | 2 | 에디터 설정 |
| gateway-api | 148 | FastAPI 게이트웨이 |
| web-ui | 163 | React 프론트엔드 |
| models | ~450 | 20개 API 서비스 |
| blueprint-ai-bom | ~100 | BOM 시스템 |
| docs | 88 | 문서 |
| scripts | 43 | 스크립트 |
| monitoring | 7 | 모니터링 설정 |
| rnd | 53 | R&D 자료 |
| **총계** | **~2,000** | - |

---

**작성자**: Claude Code (Opus 4.5)
**완료일**: 2026-01-17
