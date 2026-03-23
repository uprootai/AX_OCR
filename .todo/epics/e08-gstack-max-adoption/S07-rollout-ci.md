# S07: smoke/full CI + 배포 가드 롤아웃

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 1.5d

---

## 설명

최대 도입안은 "도구를 깔아두는 것"으로 끝나면 실패다.
실제 사용 흐름에 녹이기 위해 검증 명령, CI, 온보딩, 팀 운영 가이드를 묶어 정착시켜야 한다.
현재 CI는 lint/build/unit 중심이고, CD는 placeholder 단계가 남아 있으므로, 이 Story는 `qa` 전체 자동화보다 `smoke/full 분리`와 `deploy 계열 비활성 가드`를 먼저 다룬다.

이 Story의 목적은 다음을 AX 표준 절차로 엮는 것이다.

- 브라우저 QA 실행 명령
- skill/command 사용 순서
- 훅 동작과 예외 처리
- `/verify` 또는 동등 명령과의 연결
- 팀 온보딩 문서
- Playwright smoke/full 전략
- deploy 계열 스킬의 활성/비활성 조건

## 완료 조건

- [x] 브라우저 QA와 skill/command 사용 흐름이 운영 문서에 반영된다.
- [x] CI 또는 로컬 verify 체크리스트에 새 검증 단계가 연결된다.
- [x] 신규 팀원이 따라 할 수 있는 온보딩 가이드가 정리된다.
- [x] 파일 경로, 실행 명령, 실패 시 확인 지점이 모두 문서에 포함된다.
- [x] Playwright smoke와 full 실행 경로가 분리된다.
- [x] `ship`/`land-and-deploy`/`canary`의 활성 조건 또는 보류 조건이 문서화된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `.claude/commands/verify.md` | 수정 |
| `.claude/commands/README.md` | 수정 검토 |
| `.claude/skills/README.md` 또는 동등 문서 | 수정 검토 |
| `.github/workflows/ci.yml` | 수정 |
| `.github/workflows/cd.yml` | 수정 검토 |
| `.todo/ACTIVE.md` | 수정 검토 |
| `.todo/epics/e08-gstack-max-adoption/rollout-guide.md` | 신규 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: gstack 최대 도입 결과를 AX 팀의 기본 운영 루틴으로 정착
- 기준: 새 팀원도 문서만 보고 브라우저 QA와 review/verify 흐름을 재현 가능해야 함
- 필수 분리: 로컬 full QA와 CI smoke QA를 분리하고, deploy 계열은 조건 충족 전까지 guard 문서로 남길 것
- 주의: 명령 이름, 실행 순서, 실패 시 대응을 실제 저장소 기준으로 작성
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- 이 Story는 앞선 S02~S06의 결정이 선행되어야 한다.
- 현재 `cd.yml`은 placeholder가 있으므로 deploy 계열은 "즉시 자동화"보다 "언제 활성화 가능한지"를 문서화하는 것이 우선이다.
- CI에는 `frontend-smoke` job을 추가해 `npm run test:e2e:dual-ui`를 기본 smoke로 고정했다.
- full BOM Playwright는 backend 및 인증 조건이 얽히므로 로컬 수동 검증으로 유지하고, `/verify`와 `rollout-guide.md`에 순서를 반영했다.
- deploy 계열은 `cd.yml` placeholder, `example.com` URL, 실제 롤백 절차 부재를 이유로 guard-only 상태로 기록했다.
- source of truth는 `.todo/epics/e08-gstack-max-adoption/rollout-guide.md`다.
