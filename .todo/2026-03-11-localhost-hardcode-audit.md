# localhost 하드코딩 감사 결과 (2026-03-11)

> **배경**: 외부 IP(211.197.137.4:9000)로 접속 시 localhost 참조로 인해 기능이 깨지는 문제 발견
> **ngrok-proxy 경로 매핑**: `/` → web-ui, `/bom/` → blueprint-ai-bom, `/docs/` → docs-site, `/api/` → BOM 백엔드, `/svc/gateway/` → Gateway API

---

## 이미 수정 완료

| 파일 | 수정 내용 | 커밋 |
|------|-----------|------|
| `web-ui/src/pages/project/components/PIDWorkflowSection.tsx` | `localhost:3000` → `/bom/` | 미커밋 |
| `web-ui/src/pages/project/ProjectDetailPage.tsx` | `localhost:3000` → `/bom/` | 미커밋 |
| `web-ui/src/pages/dashboard/Dashboard.tsx` (3곳) | `localhost:3000` → `/bom/` | 미커밋 |
| `web-ui/src/pages/docs/Docs.tsx` | `localhost:3001` → `/docs/` | 미커밋 |
| `web-ui/src/components/layout/Sidebar.tsx` | `localhost:3001` → `/docs/` | 미커밋 |
| `web-ui/src/components/dashboard/ExportToBuiltinDialog.tsx` (4곳) | `localhost:3001/docs` → `/docs/docs` | 미커밋 |
| `web-ui/src/pages/dashboard/guide/sections/DocsSection.tsx` | `localhost:3001` → `/docs/` | 미커밋 |
| `web-ui/src/locales/en.json` (2곳) | `localhost:3000` → `AI BOM UI` | 미커밋 |
| `web-ui/src/locales/ko.json` (2곳) | `localhost:3000` → `AI BOM UI` | 미커밋 |
| `web-ui/src/config/nodes/bomNodes.ts` | `localhost:3000` → `/bom/` | 미커밋 |
| `web-ui/src/pages/blueprintflow/components/FinalResultView.tsx` | 런타임 치환 추가 | 미커밋 |
| `blueprint-ai-bom/frontend/vite.config.ts` | `base: '/'` → `base: '/bom/'` | 미커밋 |
| `blueprint-ai-bom/frontend/src/App.tsx` | `BrowserRouter`에 `basename` 추가 | 미커밋 |

---

## 🔴 즉시 수정 필요 (외부 접속 시 기능 깨짐)

### A. Gateway API 호출 — `localhost:8000`

#### A-1. `web-ui/src/store/apiConfigStore.ts`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 76 | `http://localhost:8000/api/v1/api-configs` | API 설정 목록 조회 |
| 104 | `http://localhost:8000/api/v1/api-configs/{id}` | API 설정 삭제 |
| 123 | `http://localhost:8000/api/v1/api-configs/{id}` | API 설정 업데이트 |
| 146 | `http://localhost:8000/api/v1/api-configs/{id}/toggle` | API 토글 |

**수정 방향**: `VITE_GATEWAY_URL` 환경변수 참조 또는 `/svc/gateway` 상대경로

#### A-2. `web-ui/src/lib/apiServices.ts`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 32 | `http://localhost:8000` | Gateway API 로컬 폴백 |
| 34~58 | `http://localhost:500{1-22}` (16개+) | 각 ML API 서비스 직접 URL 폴백 |

**수정 방향**: 모든 서비스 URL을 `/svc/{서비스명}/` 상대경로로 전환

#### A-3. `web-ui/src/components/monitoring/constants.ts`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 14~43 | `http://localhost:8000`, `http://localhost:500{1-22}` | 21개 API 서비스 모니터링 상수 |

**수정 방향**: `/svc/{서비스명}/` 상대경로로 전환. ngrok-proxy가 이미 모든 서비스에 대한 `/svc/` 라우팅을 가지고 있음

#### A-4. `web-ui/src/pages/admin/api-detail/hooks/useAPIDetail.ts`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 147 | `http://localhost:8000/api/v1/registry/list` | Gateway 레지스트리 조회 |

#### A-5. `web-ui/src/components/blueprintflow/node-palette/hooks/useContainerStatus.ts`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 38 | `http://localhost:8000/api/v1/containers/status` | 컨테이너 상태 확인 |
| 76 | `http://localhost:8000/api/v1/containers/{name}/start` | 컨테이너 시작 |

#### A-6. `web-ui/src/pages/blueprintflow/hooks/useContainerStatus.ts`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 38 | `http://localhost:8000/api/v1/containers/status` | 컨테이너 상태 확인 (중복 파일) |
| 76 | `http://localhost:8000/api/v1/containers/{name}/start` | 컨테이너 시작 (중복 파일) |

#### A-7. `web-ui/src/components/ui/PipelineProgress.tsx`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 45 | `http://localhost:8000/api/v1/progress/{jobId}` | SSE 진행률 스트리밍 |

### B. BOM 백엔드 — `localhost:5020`

#### B-1. `gateway-api/routers/workflow_router.py`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 31 | `http://localhost:5020` | BOM API URL 환경변수 기본값 |

**비고**: Docker 내부에서는 `blueprint-ai-bom-backend:5020`을 사용하지만, 환경변수 미설정 시 폴백

### C. BOM 프론트엔드 — `localhost:3000`

#### C-1. `gateway-api/blueprintflow/executors/bom_executor.py`

| 줄 | 하드코딩 | 용도 |
|----|----------|------|
| 30 | `http://localhost:3000` | FRONTEND_URL (verification_url 생성) |

**비고**: 프론트엔드(`FinalResultView.tsx`)에서 런타임 치환으로 임시 해결됨. 근본적으로는 환경변수화 필요

---

## ⚠️ 검토 필요 (문서/가이드용 — 기능은 안 깨지나 혼동 가능)

| 파일 | 줄 | 하드코딩 | 용도 |
|------|-----|----------|------|
| `web-ui/src/pages/dashboard/guide/sections/TestingSection.tsx` | 13 | `http://localhost:5020` | 테스트 가이드 코드 예시 |
| `web-ui/src/components/dashboard/ExportToBuiltinDialog.tsx` | 268~269 | `http://localhost:${port}`, `http://localhost:8000` | 테스트 코드 생성 템플릿 |
| `docs-site/docusaurus.config.ts` | 61 | `http://localhost:5173` | Web UI 네비게이션 링크 |
| `docs-site/docusaurus.config.ts` | 66 | `http://localhost:3000` | BOM UI 네비게이션 링크 |
| `gateway-api/api_specs/blueprint-ai-bom.yaml` | 38 | `http://localhost:3000` | API 스펙 메타데이터 |
| `blueprint-ai-bom/frontend/.env` | 5~6 | `http://localhost:5020` | 개발 API URL |

---

## ❌ 수정 불필요

| 파일 | 이유 |
|------|------|
| `.env.example`, `.env.production` | 환경변수 정의/예시 |
| `web-ui/e2e/*.spec.ts` | E2E 테스트 전용 |
| `blueprint-ai-bom/exports/dsebearing-delivery/setup.sh` | 독립형 납품 패키지 |
| `blueprint-ai-bom/exports/dsebearing-delivery/setup.ps1` | 독립형 납품 패키지 |
| `docker-compose.monitoring.yml` | 모니터링 인프라 |
| Docker 내부 통신 (`blueprint-ai-bom-backend:5020` 등) | 컨테이너 간 네트워크 |

---

## 권장 수정 전략

### 단기 (외부 공유 즉시 필요할 때)

각 파일의 `http://localhost:포트`를 ngrok-proxy 상대 경로로 치환:

| localhost 포트 | 상대 경로 | ngrok-proxy 라우팅 |
|---------------|-----------|-------------------|
| `localhost:8000` | `/svc/gateway` | → `gateway-api:8000` |
| `localhost:3000` | `/bom` | → `blueprint-ai-bom-frontend:80` |
| `localhost:3001` | `/docs` | → `docs-site:80` |
| `localhost:5020` | `/api` 또는 `/svc/bom` | → `blueprint-ai-bom-backend:5020` |
| `localhost:5005` | `/svc/yolo` | → `yolo-api:5005` |
| `localhost:500X` | `/svc/{서비스명}` | → `{서비스명}-api:500X` |

### 중기 (근본적 해결)

1. `VITE_GATEWAY_URL` 환경변수를 빈 문자열로 설정 (상대경로 모드)
2. 모든 API 호출을 `VITE_GATEWAY_URL` + 상대경로로 통일
3. 개별 서비스 직접 호출을 Gateway 경유로 전환 (이미 Gateway가 프록시 역할)
4. `.env.production`에 환경별 설정 분리

---

## 작업량 추정

| 영역 | 파일 수 | 수정 포인트 | 난이도 |
|------|---------|-------------|--------|
| Gateway API 호출 (A-1~A-7) | 6개 | ~30곳 | 중 (패턴 반복) |
| ML 서비스 URL (A-2, A-3) | 2개 | ~40곳 | 중 (매핑 테이블 필요) |
| BOM 백엔드 (B-1) | 1개 | 1곳 | 하 |
| BOM 프론트엔드 (C-1) | 1개 | 1곳 | 하 (이미 임시 해결) |
| 문서/가이드 (검토) | 4개 | ~6곳 | 하 |
| **합계** | **~14개** | **~78곳** | |
