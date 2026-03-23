# E08 Rollout Guide

> AX 저장소 기준 `review -> verify -> qa-only` 운영 순서와 smoke/full/deploy guard 정책

---

## 현재 운영 상태

| 영역 | 상태 | 기준 경로 |
|------|------|-----------|
| Dual UI smoke | 활성 | `.github/workflows/ci.yml`, `web-ui/e2e/dual-ui-smoke.spec.ts` |
| BOM full 브라우저 QA | 로컬 수동 실행 | `web-ui/package.json`, `web-ui/e2e/blueprint-ai-bom*.spec.ts` |
| 인증 storage state | 선택 경로 | `.gstack/auth/`, `scripts/browser-auth/README.md` |
| deploy 계열 command | guard-only | `.github/workflows/cd.yml`, `.todo/epics/e08-gstack-max-adoption/S07-rollout-ci.md` |

## 기본 운영 순서

1. 설계 또는 범위 변경 전에는 `/plan-eng-review`로 touched surface와 검증 범위를 좁힌다.
2. 구현 후에는 `/review`로 결함과 회귀 위험을 먼저 찾는다.
3. 실행 검증은 `/verify`로 진행하고, 변경 범위에 맞춰 최소 검증부터 수행한다.
4. UI 흐름 근거가 필요하면 `/qa-only`로 브라우저 artifact를 남긴다.
5. 원인이 불명확한 실패는 `/investigate`로 root cause를 좁힌다.
6. 세션 전환 또는 Claude handoff가 필요하면 `/handoff`에 `.gstack/reports/...`와 남은 blocker를 함께 남긴다.

## Smoke / Full 분리

| 구분 | 명령 | 목적 | 필수 서비스 | 실행 위치 | CI 포함 여부 |
|------|------|------|-------------|-----------|--------------|
| Smoke | `cd web-ui && npm run test:e2e:dual-ui` | `web-ui` shell, `/bom/*` redirect, BOM frontend 진입 확인 | `web-ui`, `blueprint-ai-bom/frontend`는 Playwright가 자동 기동 | 로컬, CI | 포함 |
| Full | `cd web-ui && npm run test:e2e:bom` | BOM workflow 상세 시나리오와 UI 상호작용 검증 | 위 2개 프론트 + 필요 시 `blueprint-ai-bom/backend:5020` | 로컬 우선 | 제외 |
| Targeted | `cd web-ui && npx playwright test ... --grep "..."` | 특정 회귀만 재현 | 시나리오별 상이 | 로컬 | 제외 |

운영 규칙:
- PR 또는 커밋 전 기본 브라우저 검증은 `smoke`다.
- `full`은 BOM workflow, 업로드, 세션, 매칭, overlay에 손댔을 때만 추가한다.
- smoke가 부팅 단계에서 실패하면 full로 넘어가지 않는다.
- 인증이 필요한 시나리오만 `PLAYWRIGHT_STORAGE_STATE=.gstack/auth/playwright.storage-state.json`를 사용한다.

## 로컬 실행 체크리스트

### 1. 일반 코드 변경

```bash
/review
/verify
```

### 2. UI 또는 라우팅 변경

```bash
/review
/verify
cd web-ui && npm run test:e2e:dual-ui
```

### 3. BOM workflow / 세션 / 매칭 변경

```bash
/review
/verify
cd web-ui && npm run test:e2e:dual-ui
cd web-ui && npm run test:e2e:bom
```

### 4. 인증이 필요한 브라우저 흐름

```bash
cd web-ui && \
  PLAYWRIGHT_STORAGE_STATE=../.gstack/auth/playwright.storage-state.json npm run test:e2e:bom
```

참고:
- 셸 문법상 `PLAYWRIGHT_STORAGE_STATE=... npm run ...` 형태로 같은 줄에서 실행해야 환경변수가 전달된다.
- artifact는 `.gstack/reports/playwright/` 아래에 남는다.

## 실패 시 확인 지점

| 증상 | 우선 확인 | 경로 / 명령 |
|------|-----------|-------------|
| `/bom/*` redirect 실패 | `VITE_BLUEPRINT_AI_BOM_FRONTEND_URL`, Playwright webServer 기동 | `web-ui/src/lib/blueprintBomFrontend.ts`, `web-ui/playwright.config.ts` |
| BOM frontend 진입 실패 | `blueprint-ai-bom/frontend` 의존성 또는 Vite 기동 실패 | `cd blueprint-ai-bom/frontend && npm ci && npm run dev` |
| workflow 화면 요소 누락 | test id와 시나리오 정의 확인 | `web-ui/src/pages/project/components/BOMWorkflowSection.tsx`, `web-ui/src/pages/project/components/DrawingMatchTable.tsx`, `web-ui/e2e/plan/09-ax-scenario-pack.md` |
| full 테스트에서 API 관련 실패 | `blueprint-ai-bom/backend` 5020, 인증 storage state | `curl -s http://localhost:5020/health`, `.gstack/auth/` |
| artifact 위치 확인 필요 | Playwright report root | `.gstack/reports/playwright/html/`, `.gstack/reports/playwright/test-results/` |

## CI 정책

현재 `.github/workflows/ci.yml` 기준:
- `frontend` job은 lint/build/unit을 담당한다.
- `frontend-smoke` job은 `npm run test:e2e:dual-ui`만 실행한다.
- `frontend-smoke`는 `web-ui`와 `blueprint-ai-bom/frontend` 의존성을 각각 설치한 뒤 Playwright Chromium을 설치한다.
- full BOM 브라우저 테스트는 backend 의존성과 인증 상태가 엮이므로 CI에 올리지 않고 로컬 수동 검증으로 유지한다.

즉, CI는 `dual-ui smoke parity`, 로컬은 `full workflow confidence`를 담당한다.

## Deploy Guard

다음 3개는 아직 활성화하지 않는다.

| 항목 | 현재 상태 | 활성 조건 |
|------|-----------|-----------|
| `/ship` | 보류 | CHANGELOG/VERSION 자동화와 현재 PR 규칙 정합성 확정 |
| `/land-and-deploy` | 보류 | `.github/workflows/cd.yml`의 placeholder deploy/health step 제거 후 |
| `/canary` | 보류 | 실제 staging/prod URL, post-deploy metric source, 에러 수집 채널 확정 후 |

배포 자동화 활성 조건:
1. `cd.yml`의 `example.com` URL이 실제 환경 값으로 교체될 것
2. `Deploy via SSH (placeholder)`와 echo 기반 health check가 실제 명령으로 바뀔 것
3. post-deploy health endpoint가 `http://localhost:5050/api/v1/health`, `http://localhost:5020/health`에 대응하는 실제 환경 URL로 문서화될 것
4. 롤백 절차와 필요한 secrets 목록이 `.todo` 또는 `.claude` 문서에 고정될 것

## 신규 팀원 온보딩

1. `web-ui`와 `blueprint-ai-bom/frontend`에서 `npm ci`를 한 번씩 실행한다.
2. `/review`, `/verify`, `/qa-only`의 역할 차이를 [`.claude/commands/README.md`](/home/uproot/ax/poc/.claude/commands/README.md)에서 읽는다.
3. UI 변경이 있으면 `cd web-ui && npm run test:e2e:dual-ui`를 먼저 돌린다.
4. BOM workflow 변경이면 `cd web-ui && npm run test:e2e:bom`을 추가한다.
5. artifact는 `.gstack/reports/playwright/`에서 확인하고, 민감한 storage state는 `.gstack/auth/`에만 둔다.
6. 배포 자동화는 아직 열지 않는다. 관련 요구가 생기면 먼저 `S07` 문서와 `cd.yml` placeholder 제거 여부를 확인한다.

## Source Of Truth

- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `.claude/commands/README.md`
- `.claude/commands/verify.md`
- `.claude/commands/qa-only.md`
- `web-ui/package.json`
- `web-ui/playwright.config.ts`
- `web-ui/e2e/plan/09-ax-scenario-pack.md`
- `.todo/epics/e08-gstack-max-adoption/S07-rollout-ci.md`
