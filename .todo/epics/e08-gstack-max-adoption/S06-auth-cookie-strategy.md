# S06: 인증/쿠키/아티팩트 저장 정책 수립

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 1.5d

---

## 설명

브라우저 QA를 실전 운영으로 끌고 가려면 로그인 상태를 어떻게 다룰지 먼저 정해야 한다.
`gstack`의 `setup-browser-cookies`는 참고할 수 있지만 macOS Chromium 계열 전제이므로 AX 표준으로 바로 채택할 수는 없다.
또한 AX 저장소는 `.gitignore`에 `.gstack/`가 없으므로 storage state, trace, screenshot, benchmark report를 어디에 두고 어떻게 무시할지도 이 Story 범위에 포함한다.

이 Story에서는 다음을 결정한다.

- 지원 OS / 브라우저 매트릭스
- 기본 인증 방식
- 선택적 쿠키 임포트 방식
- Playwright storage state 관리 정책
- 비밀정보 저장 금지 규칙
- `.gstack` 또는 동등 아티팩트 디렉터리 정책

## 완료 조건

- [x] AX 팀 기준 지원 OS/브라우저 매트릭스가 문서화된다.
- [x] 기본 경로가 수동 로그인인지 storage state인지 명시된다.
- [x] macOS 한정 쿠키 임포트는 선택 기능으로 격리되거나 제외 사유가 기록된다.
- [x] 세션 파일, 쿠키 파일, 비밀정보 취급 규칙이 정의된다.
- [x] trace/report/storage-state 저장 위치와 `.gitignore` 정책이 정의된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `.todo/epics/e08-gstack-max-adoption/auth-matrix.md` | 신규 |
| `scripts/browser-auth/` | 신규 검토 |
| `.gitignore` | 수정 검토 |
| `.claude/commands/verify.md` | 인증 전제조건 보강 검토 |
| `.claude/hooks/README.md` | 보안 규칙 보강 검토 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: 브라우저 QA 운영 시 인증/세션 관리에서 혼선이 없도록 기본 정책 확정
- 기준: 팀 전체가 재현 가능해야 하며, 특정 OS 전용 기능은 보조 경로로만 인정
- 필수 포함: trace/screenshot/storage-state/report 저장 위치와 ignore 규칙
- 주의: 쿠키 파일을 저장소에 커밋하는 흐름은 금지
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- 핵심 경로는 범용 재현성이다.
- 개인 브라우저 쿠키를 팀 공용 표준으로 삼지 않는다.
- `.gstack` 경로를 유지할지, `test-results/` 등 기존 무시 경로로 흡수할지도 이 Story에서 결정한다.
- source of truth는 `.todo/epics/e08-gstack-max-adoption/auth-matrix.md`로 정리했다.
- Playwright는 `PLAYWRIGHT_STORAGE_STATE` 환경변수가 있을 때만 storage state를 사용하도록 `web-ui/playwright.config.ts`에 연결했다.
- 운영 가이드는 `scripts/browser-auth/README.md`에 기록했다.
- `.gstack/auth/`는 민감 경로로 분류하고, `.claude/hooks/README.md`와 `.claude/commands/verify.md`에 규칙을 반영했다.
