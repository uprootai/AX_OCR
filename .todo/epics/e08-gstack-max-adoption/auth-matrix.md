# E08 Auth / Artifact Matrix

> 기준일: 2026-03-23
> 범위: AX dual-ui Playwright, `.gstack` 로컬 아티팩트, customer share-token 흐름

## 1. 지원 매트릭스

| 항목 | 표준 지원 | 메모 |
|------|-----------|------|
| OS | Linux, macOS, WSL2 | 팀 공용 재현 기준 |
| 브라우저 | Playwright Chromium | 기본 표면 |
| Firefox/WebKit | 보류 | S07 이후 필요 시 |
| 개인 브라우저 쿠키 임포트 | 비표준 | macOS Chromium 전용 구현은 참고만 가능 |

## 2. 인증 방식 우선순위

| 우선순위 | 방식 | 사용 조건 |
|----------|------|-----------|
| 1 | 비인증 local flow | 대부분의 AX 개발/QA 기본값 |
| 2 | URL token (`?token=`) | Customer session 공유 링크 검증 |
| 3 | Playwright storage state | 로그인 세션이 필요한 내부 화면 검증 |
| 4 | 개인 브라우저 쿠키 임포트 | 보조/예외 경로, 팀 표준 아님 |

## 3. 민감도 분류

| 데이터 | 민감도 | 정책 |
|--------|--------|------|
| Playwright storage state JSON | 높음 | `.gstack/auth/`에만 저장, commit 금지 |
| customer session access token | 높음 | 링크 공유 시에만 사용, 문서/코드에 기록 금지 |
| localStorage UI 설정 (`theme`, `hyperParameters`) | 중간 | 테스트 중 생성 가능하나 팀 공유 산출물 아님 |
| trace / screenshot / video | 중간 | 민감 화면이 있을 수 있으므로 `.gstack/reports/`에만 저장 |

## 4. 저장 경로 정책

| 경로 | 용도 | 정책 |
|------|------|------|
| `.gstack/auth/` | storage state, 임시 auth 파일 | ignore, 민감 |
| `.gstack/reports/playwright/` | trace, video, screenshot, HTML report | ignore |
| `.gstack/state/` | freeze state, hook runtime state | ignore |

## 5. 실행 정책

### 기본 경로

- 대부분의 AX 흐름은 비인증 또는 local API 세션으로 검증한다.
- `dual-ui-smoke`, `BOM workflow`, `Dimension Lab`은 로그인 없는 경로를 우선 사용한다.

### storage state 경로

- 로그인 세션이 필요하면 `PLAYWRIGHT_STORAGE_STATE`로 명시적으로 전달한다.
- 표준 파일명:
  - `.gstack/auth/playwright.storage-state.json`

예시:

```bash
cd web-ui
PLAYWRIGHT_STORAGE_STATE=../.gstack/auth/playwright.storage-state.json \
  npm run test:e2e:dual-ui
```

### customer share-token 경로

- `blueprint-ai-bom/frontend/src/pages/customer/CustomerSessionPage.tsx`는 `?token=` 쿼리로 접근한다.
- 이 토큰은 문서화/커밋하지 않고, 재현 시마다 새로 발급된 URL을 사용한다.

## 6. 비표준 경로

- macOS Chromium 쿠키 추출은 실험적/개인용 경로로만 인정한다.
- 팀 표준 문서와 CI에서는 cookie import를 전제하지 않는다.
- 필요 시 `.gstack/auth/tmp/` 아래에서 개인 로컬 작업으로만 사용하고, handoff에는 "사용 여부"만 기록한다.

## 7. handoff / verify 기록 규칙

- handoff에는 auth 파일 **내용**이 아니라 **경로와 사용 여부**만 남긴다.
- 예시:
  - `PLAYWRIGHT_STORAGE_STATE=../.gstack/auth/playwright.storage-state.json 사용`
  - `customer share-token flow 검증, 토큰 값은 기록하지 않음`

## 8. Claude에게 공유할 핵심 파일

- `.todo/epics/e08-gstack-max-adoption/auth-matrix.md`
- `scripts/browser-auth/README.md`
- `web-ui/playwright.config.ts`
