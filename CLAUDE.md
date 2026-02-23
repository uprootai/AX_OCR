# AX POC - Claude Code Project Guide

> **LLM 최적화 프로젝트 가이드** | 마지막 업데이트: 2026-02-06
> **컨텍스트 효율화**: 상세 가이드는 `.claude/skills/`에서 온디맨드 로드

---

## 프로젝트 개요

**기계 도면 자동 분석 및 제조 견적 생성 시스템**

```
도면 이미지 → VLM 분류 → YOLO 검출 → OCR 추출 → 공차 분석 → 리비전 비교 → 견적 PDF
```

| 항목 | 값 |
|------|-----|
| **기술 스택** | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker |
| **프론트엔드** | http://localhost:5173 |
| **백엔드** | http://localhost:8000 |
| **Blueprint AI BOM** | http://localhost:5020 (v10.5) |
| **Docs Site** | http://localhost:3001 (Docusaurus) |
| **상태** | ✅ 전체 정상 (18/18 API healthy) |
| **테스트** | 549개 통과 (gateway 364, web-ui 185) |
| **디자인 점수** | 100/100 (모듈화 완료) |

---

## 컨텍스트 관리 규칙

### 60% 규칙
- `/context` 명령으로 사용률 확인
- **60% 초과 시** → `/compact` 또는 `/handoff` 실행

### 탐색 패턴
| 상황 | 도구 |
|------|------|
| 대규모 코드베이스 검색 | `Explore` 에이전트 |
| 특정 파일 읽기 | `Read` 도구 |
| 클래스/함수 정의 검색 | `Glob` 도구 |
| 2-3개 파일 내 검색 | `Read` 도구 |

### 복잡한 작업
- `/ultrathink` 활용 (변경 검토 시 필수)
- 신선한 컨텍스트에서 시작

---

## 작업 추적 (.todo/)

**Claude가 자동으로 관리해야 하는 작업 추적 시스템**

```
.todo/
├── ACTIVE.md                      # 현재 진행 중인 작업
├── BACKLOG.md                     # 향후 작업 목록
├── COMPLETED.md                   # 완료 아카이브
├── PENDING_PATTERN_PROPAGATION.md # 패턴 확산 추적
└── CLAUDE_CODE_STRATEGIES.md      # 보리스 체니 13가지 전략
```

### 핵심 규칙

| 시점 | 행동 |
|------|------|
| **세션 시작** | `ACTIVE.md` 읽고 현재 작업 파악 |
| **작업 완료** | `ACTIVE.md` 갱신, 필요시 `COMPLETED.md`에 기록 |
| **새 작업 발견** | `BACKLOG.md`에 추가 |
| **장기 작업 완료** | `archive/`에 상세 문서 보관 |

### 자동 동기화 항목

- **테스트 수**: 변경 시 `ACTIVE.md` 업데이트
- **노드/API 수**: 추가/제거 시 갱신
- **archive 정리**: 완료된 문서 삭제 후 개수 업데이트

### 참조 파일 경로
```
.todo/ACTIVE.md      # 항상 최신 상태 유지 필수
.todo/BACKLOG.md     # P2, P3 작업 목록
.todo/COMPLETED.md   # 날짜별 완료 기록
```

---

## API 테스트 규칙

### 핵심: Multipart 필수 (base64 금지)

```bash
# ❌ 금지 - 쉘 인자 제한, +33% 용량
curl -d '{"image": "base64..."}'

# ✅ 필수 - 빠르고 안정적
curl -F "file=@image.png" http://localhost:5005/api/v1/detect
```

### 금지 사항

| 금지 | 이유 |
|------|------|
| base64 인코딩 이미지 전송 | 쉘 인자 제한 초과, 33% 용량 증가 |
| `curl`로 ML API 직접 호출 | 응답 시간 예측 불가, 세션 블로킹 |
| 백그라운드 테스트 (`nohup`, `&`) | 진행상황 확인 불가 |

### 권장 방법 (우선순위)

| 순위 | 방법 | 설명 |
|------|------|------|
| 1️⃣ | **Playwright 브라우저 테스트** | web-ui를 통한 E2E 테스트 (권장) |
| 2️⃣ | **Playwright HTTP** | `playwright_post`, `playwright_get` 사용 |
| 3️⃣ | **사용자 직접 실행** | 명령어 제공 후 사용자가 터미널에서 실행 |

### Playwright 브라우저 테스트 패턴

```javascript
// 1. 브라우저 열기
playwright_navigate({ url: "http://localhost:5173/blueprintflow/builder" })

// 2. 파일 업로드 (hidden input 처리)
playwright_evaluate({ script: "document.querySelector('input[type=file]').style.display='block'" })
playwright_upload_file({ selector: "input[type=file]", filePath: "/path/to/image.png" })

// 3. 노드 추가 (드래그 이벤트 시뮬레이션)
playwright_evaluate({ script: "/* drag event code */" })

// 4. 스크린샷으로 결과 확인
playwright_screenshot({ name: "result" })
```

### 예외 (Claude가 직접 실행 가능)

```bash
# 허용: 빠른 헬스체크 (< 1초)
curl -s http://localhost:5005/health
```

---

## 온디맨드 스킬 (상세 가이드)

필요할 때만 로드되어 컨텍스트 효율 극대화:

| 스킬 | 용도 | 트리거 |
|------|------|--------|
| `modularization-guide` | 1000줄 제한, 분리 패턴 | "리팩토링", "분리", "모듈화" |
| `api-creation-guide` | 새 API 스캐폴딩 전체 가이드 | "새 API", "/add-feature" |
| `project-reference` | R&D 논문, API 스펙, 문서 구조 | "논문", "스펙", "R&D" |
| `version-history` | 버전 히스토리, BOM, Design Checker | "버전", "BOM", "Design Checker" |
| `devops-guide` | CI/CD, Docker, 배포, 환경설정 | "CI", "CD", "배포", "Docker" |
| `docs-site-guide` | 문서 사이트 관리, 페이지 추가 | "문서", "docs-site" |

**위치**: `.claude/skills/`

---

## 핵심 파일 위치

### 프론트엔드 (web-ui/)

| 목적 | 파일 경로 |
|------|----------|
| **API 레지스트리** | `src/config/apiRegistry.ts` ⭐ |
| **노드 정의** | `src/config/nodeDefinitions.ts` |
| **스펙 서비스** | `src/services/specService.ts` |
| **API 클라이언트** | `src/lib/api.ts` |
| **스토어** | `src/store/workflowStore.ts`, `apiConfigStore.ts` |
| **BlueprintFlow** | `src/pages/blueprintflow/BlueprintFlowBuilder.tsx` |
| **Dashboard** | `src/components/monitoring/APIStatusMonitor.tsx` |

### 백엔드 (gateway-api/)

| 목적 | 파일 경로 |
|------|----------|
| **API 서버** | `api_server.py` |
| **API 스펙** | `api_specs/*.yaml` |
| **Executor 레지스트리** | `blueprintflow/executors/executor_registry.py` |
| **서비스 레이어** | `services/yolo_service.py`, `services/edocr2_service.py` |

### API 소스코드 (models/)

| 목적 | 파일 경로 |
|------|----------|
| **YOLO API** | `models/yolo-api/api_server.py` |
| **eDOCr2 API** | `models/edocr2-v2-api/api_server.py` |
| **기타 API** | `models/{api-id}-api/api_server.py` |
| **스캐폴딩** | `scripts/create_api.py` |

---

## API 서비스 (21개)

| 카테고리 | 서비스 | 포트 | 용도 |
|----------|--------|------|------|
| **Detection** | YOLO | 5005 | 객체 검출 |
| **Detection** | Table Detector | 5022 | 테이블 검출 및 추출 |
| **OCR** | eDOCr2 | 5002 | 한국어 치수 인식 |
| **OCR** | PaddleOCR | 5006 | 다국어 OCR |
| **OCR** | Tesseract | 5008 | 문서 OCR |
| **OCR** | TrOCR | 5009 | 필기체 OCR |
| **OCR** | OCR Ensemble | 5011 | 4엔진 가중 투표 |
| **OCR** | Surya OCR | 5013 | 90+ 언어 |
| **OCR** | DocTR | 5014 | 2단계 파이프라인 |
| **OCR** | EasyOCR | 5015 | 80+ 언어 |
| **Segmentation** | EDGNet | 5012 | 엣지 세그멘테이션 |
| **Segmentation** | Line Detector | 5016 | P&ID 라인 검출 |
| **Preprocessing** | ESRGAN | 5010 | 4x 업스케일링 |
| **Analysis** | SkinModel | 5003 | 공차 분석 |
| **Analysis** | PID Analyzer | 5018 | P&ID 연결 분석 |
| **Analysis** | Design Checker | 5019 | P&ID 설계 검증 |
| **Analysis** | Blueprint AI BOM | 5020 | Human-in-the-Loop BOM |
| **Visualization** | PID Composer | 5021 | SVG 오버레이 |
| **Knowledge** | Knowledge | 5007 | Neo4j + GraphRAG |
| **AI** | VL | 5004 | Vision-Language |
| **Orchestrator** | Gateway | 8000 | 파이프라인 조정 |

---

## 개발 명령어

```bash
# 프론트엔드
cd web-ui
npm run dev          # 개발 서버
npm run build        # 프로덕션 빌드
npm run lint         # ESLint 검사
npm run test:run     # 테스트 실행

# 백엔드
cd gateway-api
pytest tests/ -v     # 테스트 실행

# Docker
docker-compose up -d          # 전체 서비스 시작
docker logs gateway-api -f    # 로그 확인
```

---

## CI/CD 파이프라인

| 워크플로우 | 파일 | 트리거 |
|------------|------|--------|
| CI | `.github/workflows/ci.yml` | Push, PR (main, develop) |
| CD | `.github/workflows/cd.yml` | CI 성공 후 또는 수동 |

```
CI: Frontend (lint/build/test) + Backend (ruff/pytest) → Summary
CD: Pre-check → Build Images (6개) → Staging → Production (수동) → Rollback
```

**상세 가이드**: `.claude/skills/devops-guide.md`

---

## 코드 품질 기준

| 항목 | 상태 | 기준 |
|------|------|------|
| TypeScript 빌드 | ✅ | 에러 0개 |
| ESLint | ✅ | 에러 0개 |
| 테스트 | ✅ | 505개 통과 |
| 파일 크기 | ✅ | 모든 파일 < 1000줄 |

### 카테고리 타입

```typescript
type NodeCategory =
  | 'input' | 'detection' | 'ocr' | 'segmentation'
  | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
```

**주의**: `'api'` 타입은 사용하지 않음

---

## 파일 크기 규칙 (요약)

| 라인 수 | 상태 | 조치 |
|---------|------|------|
| < 500줄 | ✅ 양호 | 유지 |
| 500-1000줄 | ⚠️ 주의 | 리팩토링 고려 |
| > 1000줄 | ❌ 위반 | **즉시 분리** |

**상세 가이드**: `.claude/skills/modularization-guide.md`

---

## BlueprintFlow

### 노드 타입 (29개)

| 카테고리 | 노드 |
|----------|------|
| Input | ImageInput, TextInput |
| Detection | YOLO, Table Detector |
| OCR | eDOCr2, PaddleOCR, Tesseract, TrOCR, OCR Ensemble, SuryaOCR, DocTR, EasyOCR |
| Segmentation | EDGNet, Line Detector |
| Preprocessing | ESRGAN |
| Analysis | SkinModel, PID Analyzer, Design Checker |
| Analysis (신규) | GT Comparison, PDF Export, PID Features, Verification Queue, Dimension Updater |
| BOM | Blueprint AI BOM |
| Knowledge | Knowledge |
| AI | VL |
| Control | IF, Loop, Merge |

### 파라미터 커버리지

총 70개+ 파라미터가 `nodeDefinitions.ts`에 정의됨

### 템플릿 작성 규칙

**필수 준수사항:**
1. **API 스펙 동기화**: 템플릿 파라미터는 반드시 `gateway-api/api_specs/*.yaml`에 정의된 파라미터만 사용
2. **유효 파라미터만 사용**: 추측이나 희망사항으로 파라미터 추가 금지

**주요 API 유효 파라미터:**

| API | 유효 파라미터 |
|-----|--------------|
| **eDOCr2** | `language`, `extract_dimensions`, `extract_gdt`, `extract_text`, `extract_tables`, `cluster_threshold`, `visualize`, `enable_crop_upscale`, `crop_preset`, `upscale_scale`, `upscale_denoise` |
| **SkinModel** | `material_type`, `manufacturing_process`, `correlation_length`, `task` |
| **YOLO** | `model_type`, `confidence`, `iou`, `imgsz`, `use_sahi`, `slice_height`, `slice_width`, `overlap_ratio`, `visualize`, `task` |
| **Table Detector** | `mode`, `ocr_engine`, `borderless`, `confidence_threshold`, `min_confidence`, `output_format` |
| **Blueprint AI BOM** | `features` (array: `verification`, `gt_comparison`, `bom_generation`, `dimension_extraction`) |

**금지 파라미터 예시 (API 스펙에 없음):**
- ❌ `extract_tolerances`, `extract_bom`, `extract_title_block`, `extract_part_number`
- ❌ `analyze_gdt`, `tolerance_stack`, `analyze_clearance`, `machining_difficulty`

**검증 방법:**
```bash
# API 스펙 확인
cat gateway-api/api_specs/edocr2.yaml | grep -A 100 "parameters:"
cat gateway-api/api_specs/skinmodel.yaml | grep -A 50 "parameters:"
```

---

## 빠른 참조

### 새 API 추가
```bash
python scripts/create_api.py my-api --port 5025 --category detection
```
**상세 가이드**: `.claude/skills/api-creation-guide.md`

### GPU 설정
- Dashboard에서 동적 설정 가능
- `docker-compose.override.yml` 사용

### 테스트 실행
```bash
# 전체
npm run test:run && pytest tests/ -v

# 특정
npm run test:run -- --grep "TestName"
pytest tests/test_specific.py -v
```

---

## 서브시스템 레퍼런스

| 시스템 | 버전 | 상세 정보 |
|--------|------|----------|
| Blueprint AI BOM | v10.5 | `.claude/skills/version-history.md` |
| Design Checker | v1.0 | `.claude/skills/version-history.md` |
| R&D 논문 | 35개 | `.claude/skills/project-reference.md` |

---

## 자주 하는 실수 (금지 목록)

> 보리스 체니 전략 #4: 실수를 CLAUDE.md에 기록하여 반복 방지

### 절대 금지

| 실수 | 이유 | 대안 |
|------|------|------|
| base64 이미지 전송 | 쉘 인자 제한 초과, +33% 용량 | multipart/form-data 사용 |
| `curl`로 ML API 직접 호출 | 응답 시간 예측 불가, 블로킹 | Playwright HTTP 사용 |
| 1000줄 이상 파일 생성 | 유지보수 불가 | 즉시 분리 |
| 존재하지 않는 파라미터 사용 | API 에러 | `api_specs/*.yaml` 확인 |
| 기능 추가 시 과도한 추상화 | 복잡성 증가 | 최소한의 코드만 작성 |
| 커밋 전 빌드 미확인 | CI 실패 | `/verify` 실행 |

### 주의 사항

- **confidence_threshold**: 기본값 0.4 사용 (0.5 아님)
- **Docker 서비스명**: `blueprint-ai-bom-backend` (backend 아님)
- **Gateway 헬스체크**: `/api/v1/health` (루트 아님)

---

## 문서 사이트 동기화 규칙

### 필수: 코드 변경 시 문서 사이트도 업데이트

| 변경 유형 | 업데이트 대상 |
|----------|-------------|
| 새 API 서비스 추가 | `docs-site/docs/system-overview/` + `devops/` |
| 새 노드 타입 추가 | `docs-site/docs/blueprintflow/node-catalog.md` |
| 파이프라인 흐름 변경 | `docs-site/docs/analysis-pipeline/` 다이어그램 |
| 새 검증 레벨 추가 | `docs-site/docs/agent-verification/` |
| Docker 서비스 변경 | `docs-site/docs/devops/docker-compose.md` |
| 프론트엔드 라우트 추가 | `docs-site/docs/frontend/routing.md` |

### 문서 사이트 빌드 확인

```bash
cd docs-site && npm run build
```

### 상세 가이드: `.claude/skills/docs-site-guide.md`

---

## 자가 검증 방법

> 보리스 체니 전략 #13: 자가 검증 방법 제공

### 코드 변경 후 필수 검증

```bash
# 1. TypeScript 빌드
cd web-ui && npm run build
cd blueprint-ai-bom/frontend && npm run build

# 2. Python 문법
python -m py_compile gateway-api/api_server.py

# 3. API 헬스체크
curl -s http://localhost:5020/health
curl -s http://localhost:8000/api/v1/health
```

### Playwright E2E 검증

```javascript
// 브라우저 테스트
playwright_navigate({ url: "http://localhost:3000/workflow" })
playwright_screenshot({ name: "verification" })
```

### 자동 검증 커맨드

```
/verify   # 빌드 + 린트 + 타입체크 + 헬스체크
```

---

## 슬래시 커맨드

| 커맨드 | 용도 |
|--------|------|
| `/verify` | 자가 검증 (빌드+린트+헬스체크) |
| `/simplify` | 코드 정리 (중복 제거, 단순화) |
| `/handoff` | 세션 핸드오프 (컨텍스트 60% 초과 시) |
| `/add-feature` | 새 기능 추가 가이드 |
| `/debug-issue` | 이슈 디버깅 워크플로우 |
| `/rebuild-service` | Docker 서비스 재빌드 |
| `/test-api` | API 엔드포인트 테스트 |
| `/track-issue` | 이슈 추적 (KNOWN_ISSUES.md) |

---

## Hooks 설정

> 보리스 체니 전략 #9: Post-tool Hooks로 포매팅

### 활성화된 Hooks

| Hook | 시점 | 기능 |
|------|------|------|
| `pre-edit-check.sh` | Edit/Write 전 | 1000줄 이상 파일 경고 |
| `post-edit-format.sh` | Edit/Write 후 | 자동 포매팅 (prettier, eslint, ruff) |
| `post-bash-log.sh` | Bash 후 | 실패 명령 로깅 |
| `on-stop.sh` | 응답 완료 | 작업 완료 알림 |

### 설정 파일

- `.claude/settings.json` - 팀 공유 권한 설정
- `.claude/settings.local.json` - 로컬 전용 설정

---

**Managed By**: Claude Code (Opus 4.5)
