# E08: Gstack 운영체계 최대 도입

> **ID**: E08
> **상태**: ✅ Done
> **기간**: 2026-03-23 ~ 2026-04-17
> **고객**: 내부

---

## 목적

`gstack`의 브라우저 QA, 역할형 스킬, 작업 프로토콜, 운영 보조 도구를 AX POC에 최대 범위로 이식한다.
단, 이 Epic의 "최대 도입"은 upstream을 그대로 복사하는 뜻이 아니라, AX 저장소의 기존 `.claude`, Playwright, GitHub Actions, Docker, `.todo` 운영체계와 충돌하지 않게 내부 fork 수준으로 흡수하는 것을 의미한다.

## 기준 소스

| 항목 | 값 |
|------|----|
| Repo | `https://github.com/garrytan/gstack.git` |
| Pinned commit | `9eb74debd50b9fdc83b7b9f2061339cb54ed2210` |
| Short SHA | `9eb74de` |
| Commit date | `2026-03-22` |
| Commit subject | `feat: inline /office-hours — no more "another window" (v0.11.3.1) (#352)` |
| Local clone | `/home/uproot/ax/git-source/gstack` |

## 현재 저장소 적합성 요약

| 표면 | 현재 상태 | E08에 주는 의미 |
|------|-----------|------------------|
| 작업 규칙 | `AGENTS.md` + `.claude/commands` + `.claude/skills` + `.todo`가 이미 운영 중 | `gstack`을 별도 체계로 추가하면 중복. 기존 명령을 대체/병합하는 방식으로 가져와야 함 |
| 훅 체계 | `.claude/settings.local.json`에 `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop`가 이미 연결됨 | `careful`/`freeze`류는 기존 훅 체인 안으로 병합해야 함 |
| 브라우저 자동화 | `web-ui/playwright.config.ts`가 `web-ui`와 `blueprint-ai-bom/frontend`를 함께 띄우는 dual-ui 실행 표면으로 확장됨 | `browse`/`qa`는 기존 Playwright 표면을 감싸는 방식으로 정착 가능 |
| BOM 프론트엔드 | `blueprint-ai-bom/frontend` 자체 Playwright는 없지만 `web-ui` 러너의 두 번째 `webServer`로 편입됨 | 별도 러너 없이도 BOM workflow smoke를 검증할 수 있음 |
| 앱 토폴로지 | `web-ui`는 `/bom/*`를 env 우선 + dev `:5021/bom` / docker `:3000` 폴백으로 리다이렉트함 | QA 시나리오는 `5174 + 5021/bom + 5020` dev 구성을 기본으로 삼는다 |
| CI/CD | `.github/workflows/ci.yml`은 lint/build/unit + dual-ui Playwright smoke를 수행하고, `cd.yml`은 placeholder 단계가 남아 있음 | CI는 `smoke`, 로컬 verify는 `full`, deploy 계열은 가드 문서 기준으로 유지 |
| 아티팩트 정책 | `.gstack/`를 repo-local ignored artifact 루트로 사용 | freeze state, browser trace, local report 저장 위치를 일관되게 둘 수 있음 |
| 문서 기준 | 루트 `CLAUDE.md`가 없고, 설정은 `AGENTS.md`와 `.claude/*`에 분산 | `setup-deploy`, `ship`, `document-release`는 `CLAUDE.md` 전제를 버리고 AX 문서 위치로 옮겨야 함 |

## 채택 원칙

| 영역 | 방침 | 메모 |
|------|------|------|
| `browse` | Adapt | `bun` daemon 대신 기존 Playwright 러너와 `web-ui/e2e` 자산 재사용 |
| 역할형 `skills/commands/agents` | Adapt | 기존 `/verify`, `/debug-issue`, `/codex-cross-check`, `/handoff`와 병합 |
| `careful`, `freeze`, `guard` | Rewrite | 기존 `.claude/hooks` 체인 안에서 재구현 |
| `setup-browser-cookies` | Rewrite or Defer | macOS Chromium 한정 구현이라 팀 표준으로는 부적합 |
| `ship`, `setup-deploy`, `land-and-deploy` | Rewrite | 루트 `CLAUDE.md` 부재 + placeholder CD 파이프라인과 충돌 |
| Bun 의존 실행 흐름 | Reject | 현재 저장소는 `npm`/`pytest`/`playwright`/GitHub Actions 기준 유지 |

## 현재 결정된 저장 정책

| 경로 | 용도 | Git 정책 |
|------|------|-----------|
| `.gstack/state/` | freeze 상태, 로컬 훅 상태 | ignore |
| `.gstack/reports/` | QA/benchmark/canary 로컬 결과물 | ignore |
| `.gstack/auth/` | Playwright storage state, 세션 파일 | ignore |

## 성공 기준 (Definition of Done)

- [x] `gstack` 27개 스킬 전체에 대해 AX 저장소 기준 `Adopt / Adapt / Rewrite / Defer` 매트릭스가 작성되고, 기존 `.claude`/Playwright/CI 표면과의 연결 위치가 명시된다.
- [x] `web-ui`와 `blueprint-ai-bom/frontend`를 모두 포함하는 브라우저 QA 실행 체계가 정리되고, `5173/5174`와 `3000/5020` 이중 앱 구성이 문서화된다.
- [x] AX 전용 `skills`, `commands`, `agents`, `handoff` 문서가 기존 `.claude` 체계와 중복 없이 정리된다.
- [x] `careful`/`freeze` 대체 훅이 기존 `.claude/hooks` 체계에 맞춰 재구현되고, 인용부호 우회와 prefix 경로 우회 재현 케이스가 회귀 테스트로 막힌다.
- [x] `.gstack`류 아티팩트, 인증/쿠키/세션, smoke/full CI, deploy 가드 정책이 모두 AX 저장소 기준으로 문서화된다.

## Story 목록

| ID | Story | 예상 | 상태 |
|----|-------|------|------|
| S01 | gstack 소스 기준점 + AX 채택 매트릭스 고정 | 1.5d | ✅ |
| S02 | 이중 UI 브라우저 QA 실행 기반 통합 | 2d | ✅ |
| S03 | 기존 `.claude` 체계 기준 skill/command/agent 재배치 | 2d | ✅ |
| S04 | AX 핵심 흐름 QA 시나리오 팩 재편 | 2.5d | ✅ |
| S05 | 기존 훅 체인 위 안전 훅 재설계 | 2d | ✅ |
| S06 | 인증/쿠키/아티팩트 저장 정책 수립 | 1.5d | ✅ |
| S07 | smoke/full CI + 배포 가드 롤아웃 | 1.5d | ✅ |

## 기술 결정

- `third_party/gstack/` 벤더링은 보류하고 `/home/uproot/ax/git-source/gstack` 커밋 pin 문서를 현재 기준 소스로 사용한다.
- 브라우저 자동화는 `bun`이 아니라 기존 `Playwright + npm` 실행 체계를 사용한다.
- 안전 훅은 `.claude/settings.local.json`에 이미 연결된 훅 체계에 맞춰 재구현하며, 외부 쉘 스크립트를 그대로 복사하지 않는다.
- AX 통합 표면은 `.claude/skills`, `.claude/commands`, `.claude/agents`, `.claude/hooks`, `.github/workflows`, `web-ui/e2e`를 우선 사용한다.
- deploy 계열 스킬은 루트 `CLAUDE.md` 대신 `.claude` 또는 `.todo/decisions`를 source of truth로 쓰도록 재배치한다.
- 쿠키 임포트는 핵심 경로가 아니라 보조 경로다. 기본 인증 흐름은 수동 로그인 또는 Playwright storage state다.
- smoke/full 및 deploy guard 운영 기준 문서는 `.todo/epics/e08-gstack-max-adoption/rollout-guide.md`다.

## 참조

- `https://github.com/garrytan/gstack`
- `/tmp/gstack-review`
- `.todo/epics/e08-gstack-max-adoption/adoption-matrix.md`
- `.claude/skills/`
- `.claude/commands/`
- `.claude/hooks/`
- `.claude/settings.local.json`
- `web-ui/playwright.config.ts`
- `web-ui/e2e/`
- `web-ui/src/App.tsx`
- `web-ui/src/pages/project/components/BOMWorkflowSection.tsx`
- `web-ui/src/pages/project/components/DrawingMatchTable.tsx`
- `blueprint-ai-bom/frontend/src/App.tsx`
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `.todo/epics/e08-gstack-max-adoption/rollout-guide.md`
