---
description: 읽기 전용 브라우저 QA 보고서 생성. 수정 없이 재현 단계와 아티팩트만 남김
---

# /qa-only - 읽기 전용 브라우저 QA

브라우저를 실제로 띄워 시나리오를 점검하되, 코드는 고치지 않습니다.
`/verify`가 빌드/테스트 중심이라면, `/qa-only`는 사용자 흐름과 화면 증거 중심입니다.

## 목적

- UI/워크플로우 이상 여부를 read-only로 확인
- 재현 단계, 실패 위치, trace/screenshot/video를 한 번에 남기기
- 수정보다 먼저 무엇이 실제로 깨졌는지 고정하기

## 실행 표면

### 1. Dual UI smoke

```bash
cd web-ui && npm run test:e2e:dual-ui
```

확인 범위:
- `web-ui` dashboard shell
- `/bom/*` redirect
- `blueprint-ai-bom/frontend` workflow 진입

### 2. BOM workflow 시나리오

```bash
cd web-ui && npm run test:e2e:bom
```

### 3. 특정 시나리오 grep

```bash
cd web-ui && npx playwright test e2e/blueprint-ai-bom.spec.ts --grep "TECHCROSS"
cd web-ui && npx playwright test e2e/dual-ui-smoke.spec.ts --grep "redirects /bom routes"
```

## 아티팩트 정책

실패 아티팩트는 `.gstack` 아래에 남깁니다.

| 경로 | 내용 |
|------|------|
| `.gstack/reports/playwright/html/` | HTML report |
| `.gstack/reports/playwright/test-results/` | trace, screenshot, video, error context |

Playwright 기본 정책:
- trace: `retain-on-failure`
- screenshot: `only-on-failure`
- video: `retain-on-failure`

## 출력 형식

```markdown
## QA Report
- Surface: dual-ui / bom / specific scenario
- Result: pass / fail / blocked

### Scenarios
1. [name] — PASS
2. [name] — FAIL
   - Repro: ...
   - Expected: ...
   - Actual: ...
   - Artifact: .gstack/reports/playwright/test-results/...

### Notes
- blocked by missing backend
- env mismatch
```

## 역할 분담

- `/qa-only`: 읽기 전용 브라우저 검증, 보고서만
- `/verify`: 빌드/타입/pytest 같은 코드 검증
- `/review`: 코드/리스크 검토

UI 이슈를 수정까지 자동으로 밀어붙이지 말고, 먼저 `/qa-only`로 증거를 남긴 뒤 구현 작업으로 넘어갑니다.

## 연결 에이전트

- `.claude/agents/test-runner.md`

## 관련 문서

- `web-ui/playwright.config.ts`
- `web-ui/e2e/plan/README.md`
- `.todo/epics/e08-gstack-max-adoption/S02-browser-integration.md`
- `.todo/epics/e08-gstack-max-adoption/rollout-guide.md`
