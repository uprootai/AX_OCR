# S02: 이중 UI 브라우저 QA 실행 기반 통합

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 2d

---

## 설명

`gstack`의 핵심 가치 중 하나인 브라우저 기반 확인 흐름을 AX 프로젝트의 실제 UI 구조에 맞게 붙인다.
AX는 단일 앱이 아니라 `web-ui`와 `blueprint-ai-bom/frontend`가 함께 동작하는 구조이므로, `browse`/`qa`는 `5173/5174`와 `3000/5020`을 모두 이해해야 한다.

출발점은 이미 존재하는 `web-ui/playwright.config.ts`, `web-ui/e2e/fixtures/api-fixtures.ts`, `web-ui/src/App.tsx`의 `/bom/*` 리다이렉트 로직이다. 여기에 `blueprint-ai-bom/frontend`용 브라우저 실행 표면을 추가하거나, 최소한 명시적인 제외 사유를 문서화해야 한다.

구축 대상은 다음과 같다.

- 공통 브라우저 실행 규약
- headless / headed / trace / screenshot 정책
- 테스트 대상 서버 기동 방식
- 로그인 상태 저장 방식
- 실패 시 수집할 아티팩트 규격

## 완료 조건

- [x] `web-ui` 기준 브라우저 QA 실행 명령이 정리된다.
- [x] `blueprint-ai-bom/frontend`에도 동일한 실행 기반을 추가하거나, `web-ui` 러너에서 `:3000`을 다루는 방식이 문서화된다.
- [x] trace, screenshot, video 또는 동등한 실패 아티팩트 수집 정책이 정의된다.
- [x] Bun 없이 `npm` 기준으로 실행 가능한 구조가 확정된다.
- [x] `web-ui`의 기존 E2E와 충돌하지 않는 디렉터리/fixture/포트 전략이 정리된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `web-ui/playwright.config.ts` | 수정 |
| `web-ui/package.json` | 수정 |
| `web-ui/e2e/` | 신규 또는 확장 |
| `web-ui/e2e/fixtures/api-fixtures.ts` | 재사용 또는 보강 |
| `web-ui/src/App.tsx` | 브라우저 진입 경로 문서화 근거 |
| `blueprint-ai-bom/frontend/playwright.config.ts` | 신규 검토 |
| `blueprint-ai-bom/frontend/package.json` | 수정 검토 |
| `scripts/browser/` | 신규 검토 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: AX UI를 실제로 눌러보고 검증하는 공통 브라우저 실행 기반 확보
- 우선순위: web-ui 1순위, blueprint-ai-bom/frontend 2순위
- 필수 고려: web-ui는 /bom/*를 localhost:3000으로 리다이렉트한다. 따라서 QA는 단일 포트 전제가 아님
- 주의: gstack의 browse UX는 참고하되 현재 저장소의 Playwright 표준과 fixture 자산을 깨지 말 것
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- `web-ui`는 이미 Playwright 의존성을 포함하고 있다.
- `web-ui/e2e`는 이미 API fixture와 대규모 시나리오 초안을 보유하고 있다.
- `blueprint-ai-bom/frontend`는 현재 Playwright 설정이 없으므로 추가 여부를 판단해야 한다.
- Playwright 실행 표면은 `web-ui` 하나로 유지하고, `blueprint-ai-bom/frontend`는 두 번째 `webServer`로 기동한다.
- dev 기준 포트는 `web-ui :5174`, `blueprint-ai-bom/frontend :5021/bom`, API는 `:5020`으로 고정했다.
- `web-ui/src/App.tsx`의 `/bom/*` 리다이렉트는 env 우선 + dev/docker 포트 폴백으로 재작성했다.
- 실패 아티팩트는 `.gstack/reports/playwright/` 아래 `html`, `test-results`, `trace`, `video`, `screenshot`에 저장한다.
- 실행 명령은 `cd web-ui && npm run test:e2e:dual-ui`와 `cd web-ui && npm run test:e2e:bom`으로 정리했다.
- 검증은 `cd web-ui && npx playwright test e2e/dual-ui-smoke.spec.ts` 기준 `2 passed`를 확인했다.
