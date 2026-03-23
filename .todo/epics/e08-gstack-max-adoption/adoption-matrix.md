# E08 AX 저장소 기준 gstack 채택 매트릭스

> 기준일: 2026-03-23
> 범위: `/home/uproot/ax/poc` 현재 저장소 구조 기준
> upstream pin: `https://github.com/garrytan/gstack.git@9eb74debd50b9fdc83b7b9f2061339cb54ed2210`

## 1. 현재 저장소 베이스라인

| 표면 | 현재 상태 | 채택 시 영향 |
|------|-----------|--------------|
| 명령 체계 | `.claude/commands` 10개가 이미 운영 중 | `gstack` 커맨드는 별도 추가가 아니라 병합/대체 설계가 필요 |
| 훅 체계 | `.claude/settings.local.json`에 훅이 이미 연결돼 있음 | `careful`/`freeze`는 독립 설치가 아니라 기존 훅 체인 삽입으로 구현해야 함 |
| 브라우저 자동화 | `web-ui`는 `playwright.config.ts`, `test:e2e`, `e2e/fixtures` 보유 | `browse`/`qa`는 여기를 감싸는 래퍼로 두는 것이 자연스러움 |
| BOM UI 자동화 | `blueprint-ai-bom/frontend`는 독립 Playwright는 없지만 `web-ui` dual-ui runner에 편입됨 | 두 번째 UI 테스트 표면을 별도 러너 없이 다룰 수 있음 |
| 앱 연결 방식 | `web-ui/src/App.tsx`가 `/bom/*`를 env 우선 + dev `:5021/bom` / docker `:3000` 폴백으로 리다이렉트 | 브라우저 QA는 `web-ui` + `BOM frontend` 이중 구조를 명시적으로 알아야 함 |
| E2E 자산 | `web-ui/e2e/plan`과 API fixture가 이미 큼 | `qa-only`/`qa`는 새 플랜 파일을 만들기보다 기존 자산을 정리해서 재사용해야 함 |
| CI | `.github/workflows/ci.yml`은 lint/build/unit 중심, Playwright 미포함 | `qa` 도입 시 smoke/full 분리 필요 |
| CD | `.github/workflows/cd.yml`은 staging/production placeholder가 남아 있음 | `ship`/`land-and-deploy`는 현 상태로는 자동화보다 가드 문서가 우선 |
| 문서 기준 | 루트 `CLAUDE.md`가 없고 `AGENTS.md`, `.claude/*`, `.todo/*`가 source | `setup-deploy`, `document-release`는 저장 위치를 바꿔야 함 |
| ignore 정책 | `.gstack/`를 repo-local ignored artifact 루트로 사용 | report, trace, storage state, freeze state를 한 위치에 모을 수 있음 |

## 2. 스킬별 채택 액션

### 기획/설계

| 스킬 | 액션 | AX 표면 | 메모 |
|------|------|---------|------|
| `/office-hours` | Adapt | `.claude/commands/office-hours.md`, `.todo/epics/` | 설계 산출물은 `~/.gstack/projects`가 아니라 repo 문서 또는 ignored local dir로 재배치 |
| `/plan-ceo-review` | Adapt | `.claude/commands/plan-ceo-review.md`, `.todo/decisions/` | CEO plan 저장 위치와 TODO 반영 방식을 AX 문서 체계에 맞춤 |
| `/plan-eng-review` | Adopt | `.claude/commands/plan-eng-review.md` | 현재 `/plan-epic`, `/verify`, `web-ui/e2e/plan`과 결합 가치가 가장 큼 |
| `/plan-design-review` | Adapt | `.claude/commands/plan-design-review.md` | `DESIGN.md` 강제 대신 현재 UI 기준 문서와 선택자 정책 반영 |
| `/design-consultation` | Adapt | `.claude/skills/design-consultation.md` | design-system 생성은 선택 기능으로 두고 기존 UI 패턴 보존 |
| `/autoplan` | Adapt | `.claude/commands/autoplan.md` | `office-hours`/`plan-eng-review`/`plan-design-review`를 기존 `.todo` 흐름에 연결 |

### 개발/리뷰

| 스킬 | 액션 | AX 표면 | 메모 |
|------|------|---------|------|
| `/review` | Adopt | `.claude/commands/review.md` | 기존 `/verify` 전 단계 리뷰 명령으로 바로 가치 있음 |
| `/codex` | Adapt | `.claude/commands/codex-cross-check.md` | 이미 Codex 교차검증 명령이 있으므로 독립 커맨드보다 확장형이 맞음 |
| `/investigate` | Adopt | `.claude/commands/investigate.md`, 기존 `/debug-issue` | root-cause 규율은 유지하고 현재 Debug Contract와 병합 |
| `/design-review` | Rewrite | `.claude/commands/design-review.md`, `web-ui/e2e/` | auto-commit, clean-tree 강제, `CLAUDE.md` 수정 전제를 제거해야 함 |

### 테스트/보안

| 스킬 | 액션 | AX 표면 | 메모 |
|------|------|---------|------|
| `/qa` | Rewrite | `.claude/commands/qa.md`, `web-ui/e2e/`, `blueprint-ai-bom/frontend` | bug별 atomic commit, bootstrap, `CLAUDE.md` 수정 전제를 제거하고 `/verify`를 종료 게이트로 사용 |
| `/qa-only` | Adopt | `.claude/commands/qa-only.md`, `web-ui/e2e/` | read-only 보고서 모드는 현재 저장소와 충돌이 가장 적음 |
| `/cso` | Adapt | `.claude/commands/cso.md` | 실제 스캔 범위를 `npm audit`/`pip-audit`/grep/secret 검출로 AX 기준 재정의 |
| `/benchmark` | Adapt | `.claude/commands/benchmark.md`, `web-ui/e2e/` | Playwright 기반 측정으로 바꾸고 `.gstack/benchmark-reports` 저장 정책을 정해야 함 |
| `/browse` | Adapt | `web-ui/playwright.config.ts`, `scripts/browser/`, 선택적 `blueprint-ai-bom/frontend/playwright.config.ts` | `bun` daemon 대신 기존 Playwright 실행기로 감쌈 |

### 배포

| 스킬 | 액션 | AX 표면 | 메모 |
|------|------|---------|------|
| `/ship` | Rewrite | `.claude/commands/ship.md`, `.github/workflows/ci.yml` | VERSION/CHANGELOG/PR 자동화는 현재 저장소 표준이 없어 재설계 필요 |
| `/land-and-deploy` | Rewrite | `.claude/commands/land-and-deploy.md`, `.github/workflows/cd.yml` | CD가 placeholder라 실제 merge/deploy 가드 설계부터 필요 |
| `/canary` | Adapt | `.claude/commands/canary.md`, staging URL 정책 | 실제 서비스 URL과 baseline 위치가 정해진 뒤에만 활성화 가능 |
| `/setup-deploy` | Rewrite | `.claude/deploy.md` 또는 `.todo/decisions/` | 루트 `CLAUDE.md` 저장 전제를 버리고 AX 문서 위치로 옮겨야 함 |

### 안전/유틸

| 스킬 | 액션 | AX 표면 | 메모 |
|------|------|---------|------|
| `/careful` | Rewrite | `.claude/hooks/` | quoted command 우회 수정 필수 |
| `/freeze` | Rewrite | `.claude/hooks/` | `realpath` 기준 경계 판정으로 재작성 필요 |
| `/guard` | Rewrite | `.claude/hooks/` | `careful` + `freeze` 재작성 이후에만 의미 있음 |
| `/unfreeze` | Rewrite | `.claude/commands/unfreeze.md` | 새 freeze state 위치와 함께 다시 정의 |
| `/gstack-upgrade` | Rewrite | `third_party/gstack/`, `.todo/epics/e08-gstack-max-adoption/` | upstream self-upgrade 대신 vendor/pin 갱신 절차로 변경 |

### 문서/회고

| 스킬 | 액션 | AX 표면 | 메모 |
|------|------|---------|------|
| `/document-release` | Rewrite | `.claude/commands/document-release.md`, docs 경로 | `git push`, PR body 수정, `CLAUDE.md` 전제를 AX docs-site/README 흐름에 맞춰 변경 |
| `/retro` | Adapt | `.claude/commands/retro.md`, `.todo/COMPLETED.md` | 개인 analytics 대신 Epic/Story 회고 포맷으로 재해석 |
| `/setup-browser-cookies` | Rewrite | `scripts/browser-auth/`, `.gitignore`, 문서 | macOS Chromium 한정 기능을 보조 경로로 격리하거나 storage state 우선 정책으로 대체 |

## 3. AX 우선 구현 순서

1. S01: 기준 커밋 + 채택 매트릭스 + `.gstack`/artifact 위치 정책 고정
2. S05: 기존 `.claude/hooks` 체인 안에서 안전 훅 재작성
3. S02: `web-ui` Playwright를 중심으로 `browse`/`qa-only` 실행 기반 통합
4. S03: `/review`, `/investigate`, `/plan-eng-review`, `/qa-only`를 먼저 `.claude` 명령으로 흡수
5. S04: BOM 업로드, 도면 매칭, 세션 생성, 검증, overlay 흐름 시나리오 정리
6. S06: storage state, 로그인, trace/report 저장 규칙 고정
7. S07: CI smoke와 수동 full 실행 경로 분리, deploy 계열은 가드 문서부터 활성화

## 4. 현재 기준 핵심 판단

- `gstack` 전면 도입은 가능하지만, AX 기준으로는 "upstream 설치"가 아니라 "내부 fork 운영"이다.
- `web-ui`는 이미 Playwright 자산이 많으므로 `browse`를 새로 만드는 것보다 기존 러너를 표준 인터페이스로 삼는 편이 낫다.
- `blueprint-ai-bom/frontend`는 브라우저 QA가 비어 있으므로, E08의 실질 난이도는 `browse`보다 이 두 번째 UI 표면을 붙이는 데 있다.
- deploy 계열 스킬은 현재 CI/CD와 문서 구조를 보면 가장 늦게 활성화해야 한다.

## 5. 현재 고정된 아티팩트 정책

| 경로 | 용도 | 메모 |
|------|------|------|
| `.gstack/state/` | freeze 상태, hook runtime state | `pre-write-safety.sh`가 `freeze-dir.txt`를 읽음 |
| `.gstack/reports/` | QA/benchmark/canary 로컬 보고서 | 팀 공유 산출물이 아니라 로컬 작업 산출물 |
| `.gstack/auth/` | storage state, cookie/session 파일 | 민감 정보 가능성이 있어 commit 금지 |
