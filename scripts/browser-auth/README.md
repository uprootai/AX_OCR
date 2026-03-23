# Browser Auth Runtime

AX의 브라우저 인증 상태는 저장소가 아니라 로컬 `.gstack/auth/` 아래에 둡니다.

## 기본 원칙

- 기본 경로는 **비인증 또는 URL token 기반 흐름**이다.
- 팀 공용 표준은 **Playwright storage state**다.
- 개인 브라우저 쿠키 덤프는 팀 표준이 아니다.
- `.gstack/auth/` 아래 파일은 **민감 정보**로 취급하고 커밋/공유하지 않는다.

## 권장 경로

| 용도 | 경로 |
|------|------|
| Playwright storage state | `.gstack/auth/playwright.storage-state.json` |
| 임시 cookie export | `.gstack/auth/tmp/` |
| 수동 메모/토큰 기록 금지 | 저장소 내부 금지 |

## Playwright 사용

```bash
cd web-ui
PLAYWRIGHT_STORAGE_STATE=../.gstack/auth/playwright.storage-state.json \
  npx playwright test e2e/dual-ui-smoke.spec.ts
```

## 수동 로그인 캡처

공용 표준 capture 스크립트는 아직 없습니다. 필요하면 아래 중 하나를 사용합니다.

1. 브라우저에서 직접 로그인
2. Playwright/Codegen으로 storage state 저장

예시:

```bash
cd web-ui
npx playwright codegen http://localhost:5174 \
  --save-storage=../.gstack/auth/playwright.storage-state.json
```

## 비권장 경로

- 개인 Chrome/Arc/Brave 쿠키를 그대로 저장소 경로에 복사
- OS 전용 쿠키 추출 도구를 팀 표준으로 가정
- access token을 `.md`, `.json`, `.env` 문서에 평문으로 기록
