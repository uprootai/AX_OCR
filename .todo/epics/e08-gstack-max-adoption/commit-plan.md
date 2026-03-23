# E08 Commit Plan

> dirty worktree에서 `E08` 관련 변경만 안전하게 분리하기 위한 커밋 계획

---

## 전제

- 현재 worktree에는 E08 외의 사용자 변경이 이미 많이 섞여 있다.
- 따라서 `git add -A` 또는 상위 디렉터리 단위 staging은 금지한다.
- 아래 계획은 `E08에서 실제로 수정/생성한 파일만` path 단위로 고정해서 stage 하는 방식이다.

## 제외 대상

아래 영역은 현재 dirty 상태지만 `E08 커밋`에 넣지 않는다.

- `blueprint-ai-bom/backend/**`
- `blueprint-ai-bom/frontend/src/**`
- `docs-site-starlight/**`
- `apply-company/**`
- `.mcp.json`
- `.claude/rules/development.md`

이 파일들은 다른 작업 문맥일 가능성이 높으므로 E08와 같이 커밋하면 안 된다.

## 권장 커밋 구조

### Commit 1

**목적**: `.claude` 운영체계와 safety hook 흡수

**권장 메시지**

```bash
git commit -m "feat(claude): absorb gstack-style commands and safety hooks"
```

**stage 목록**

```bash
git add \
  .gitignore \
  .claude/settings.local.json \
  .claude/hooks/README.md \
  .claude/hooks/pre-bash-safety.sh \
  .claude/hooks/pre-write-safety.sh \
  .claude/agents/README.md \
  .claude/commands/README.md \
  .claude/commands/debug-issue.md \
  .claude/commands/handoff.md \
  .claude/commands/investigate.md \
  .claude/commands/plan-eng-review.md \
  .claude/commands/qa-only.md \
  .claude/commands/review.md \
  .claude/commands/verify.md \
  tests/hooks/test_ax_safety_hooks.py
```

**포함 이유**

- `.claude` command 역할 분리와 `gstack` 흡수형 절차가 한 묶음이다.
- safety hook 및 `.gstack` ignore 정책이 이 레이어에 속한다.
- `tests/hooks/test_ax_safety_hooks.py`는 hook 변경의 회귀 증거라 같은 커밋에 둔다.

**검증**

```bash
pytest -q tests/hooks/test_ax_safety_hooks.py
```

### Commit 2

**목적**: dual-ui Playwright 실행 표면과 web-ui QA 시나리오 통합

**권장 메시지**

```bash
git commit -m "feat(web-ui): add dual-ui playwright smoke and bom qa flows"
```

**stage 목록**

```bash
git add \
  web-ui/.env.example \
  web-ui/package.json \
  web-ui/playwright.config.ts \
  web-ui/src/App.tsx \
  web-ui/src/lib/blueprintBomFrontend.ts \
  web-ui/e2e/fixtures/runtime.ts \
  web-ui/e2e/dual-ui-smoke.spec.ts \
  web-ui/e2e/blueprint-ai-bom.spec.ts \
  web-ui/e2e/blueprint-ai-bom-comprehensive.spec.ts \
  web-ui/e2e/ui/workflow.spec.ts \
  web-ui/e2e/plan/README.md \
  web-ui/e2e/plan/08-test-matrix.md \
  web-ui/e2e/plan/09-ax-scenario-pack.md \
  web-ui/src/pages/project/components/BOMWorkflowSection.tsx \
  web-ui/src/pages/project/components/DrawingMatchTable.tsx \
  scripts/browser-auth/README.md
```

**포함 이유**

- `/bom/*` redirect, Playwright config, smoke/full 시나리오, test id 보강이 모두 같은 실행 표면이다.
- `scripts/browser-auth/README.md`는 Playwright storage state 사용법이라 이 흐름과 붙여 두는 편이 낫다.

**검증**

```bash
cd web-ui && npx tsc --noEmit
cd web-ui && npx playwright test e2e/dual-ui-smoke.spec.ts
```

### Commit 3

**목적**: E08 운영 기록, CI smoke, rollout 문서 정리

**권장 메시지**

```bash
git commit -m "docs(todo): finalize e08 rollout, ci smoke, and handoff records"
```

**stage 목록**

```bash
git add \
  .github/workflows/ci.yml \
  .todo/ACTIVE.md \
  .todo/BACKLOG.md \
  .todo/COMPLETED.md \
  .todo/epics/e08-gstack-max-adoption/EPIC.md \
  .todo/epics/e08-gstack-max-adoption/S01-vendoring-matrix.md \
  .todo/epics/e08-gstack-max-adoption/S02-browser-integration.md \
  .todo/epics/e08-gstack-max-adoption/S03-ax-skills-commands.md \
  .todo/epics/e08-gstack-max-adoption/S03-command-role-map.md \
  .todo/epics/e08-gstack-max-adoption/S04-qa-scenario-pack.md \
  .todo/epics/e08-gstack-max-adoption/S05-safe-hooks-rewrite.md \
  .todo/epics/e08-gstack-max-adoption/S06-auth-cookie-strategy.md \
  .todo/epics/e08-gstack-max-adoption/S07-rollout-ci.md \
  .todo/epics/e08-gstack-max-adoption/adoption-matrix.md \
  .todo/epics/e08-gstack-max-adoption/auth-matrix.md \
  .todo/epics/e08-gstack-max-adoption/rollout-guide.md \
  .todo/epics/e08-gstack-max-adoption/commit-plan.md
```

**선택적 포함**

```bash
git add .claude/handoff/handoff_2026-03-23_145743.md
```

기본 권장은 `handoff` 문서는 커밋하지 않고 로컬 참조로만 두는 것이다.
다만 팀이 세션 기록을 저장소에 남기는 규칙이면 마지막 커밋에 포함해도 된다.

**포함 이유**

- CI smoke job과 E08 story/epic 상태 정리가 문서/운영 계층에 속한다.
- rollout/source-of-truth 문서가 모두 `.todo/epics/e08-gstack-max-adoption/` 아래에 모여 있다.

**검증**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"
git diff --check -- .github/workflows/ci.yml .todo/ACTIVE.md .todo/BACKLOG.md .todo/COMPLETED.md .todo/epics/e08-gstack-max-adoption
```

## Stage 전 확인

각 커밋 전에는 아래처럼 `staged` 범위를 확인한다.

```bash
git diff --cached --name-only
git diff --cached --stat
```

예상과 다른 파일이 들어가 있으면 바로 `git reset HEAD <path>`로 빼고 다시 stage 한다.

## 최종 확인 순서

1. Commit 1 stage + hook test 확인
2. Commit 2 stage + `tsc` + dual-ui smoke 확인
3. Commit 3 stage + YAML/diff check 확인
4. 마지막에 `git status --short`로 E08 외 dirty 파일이 남아 있는지 다시 확인

## Source Of Truth

- `.todo/epics/e08-gstack-max-adoption/EPIC.md`
- `.todo/epics/e08-gstack-max-adoption/rollout-guide.md`
- `.claude/handoff/handoff_2026-03-23_145743.md`
