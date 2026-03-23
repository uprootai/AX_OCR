# S03: 기존 `.claude` 체계 기준 skill/command/agent 재배치

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 2d

---

## 설명

`gstack`의 역할형 작업 방식은 유용하지만, AX 도메인에 맞는 스킬과 커맨드가 필요하다.
이 Story의 핵심은 "새 커맨드를 많이 추가"하는 것이 아니라, 이미 있는 `/verify`, `/debug-issue`, `/codex-cross-check`, `/handoff`, `/plan-epic`과 충돌하지 않게 `gstack`의 고가치 절차를 재배치하는 것이다.

최소 구성은 다음을 포함한다.

- `review`
- `investigate`
- `plan-eng-review`
- `qa-only`
- 필요 시 `qa`, `cso`, `office-hours`, `autoplan`

그리고 이를 호출하는 커맨드/에이전트 문서를 추가하거나, 기존 명령을 확장한다.

## 완료 조건

- [x] `gstack` 고가치 스킬이 현재 `.claude/commands`와 중복 없이 재배치된다.
- [x] 기존 `/verify`, `/debug-issue`, `/codex-cross-check`, `/handoff`와의 역할 분담이 문서화된다.
- [x] 필요한 skill/command/agent 문서가 추가되거나 기존 문서가 확장된다.
- [x] Codex와 Claude가 모두 참조 가능한 수준으로 저장소 문서가 정리된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `.claude/skills/` | 신규 또는 수정 |
| `.claude/commands/` | 신규 또는 수정 |
| `.claude/agents/` | 신규 또는 수정 |
| `.claude/handoff/` | 신규 또는 수정 |
| `AGENTS.md` | 필요 시 보강 |
| `.claude/commands/README.md` | 역할 재배치 반영 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: AX 팀이 반복적으로 쓰는 리뷰/QA/조사 작업을 skill과 command로 표준화
- 기준: gstack의 역할형 구성은 참고하되 현재 .claude 명령과 중복되지 않게 재배치
- 필수 비교: /verify vs /qa-only, /debug-issue vs /investigate, /codex-cross-check vs /codex
- 주의: 모호한 범용 문구 대신 실제 경로, 실제 명령, 실제 검증 조건을 넣을 것
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- 현재 `.claude/skills`, `.claude/commands`, `.claude/agents` 구조는 이미 존재한다.
- 새 스킬은 `web-ui`, `gateway-api`, `blueprint-ai-bom/backend` 경로를 직접 참조해야 한다.
- 기존 명령을 유지하면서 alias 또는 supersede 관계를 명시하는 방식이 우선이다.
- 실제 도입 command는 `.claude/commands/review.md`, `.claude/commands/investigate.md`, `.claude/commands/plan-eng-review.md`, `.claude/commands/qa-only.md`로 추가했다.
- 기존 `.claude/commands/verify.md`, `.claude/commands/debug-issue.md`, `.claude/commands/handoff.md`, `.claude/commands/README.md`에 역할 경계와 handoff 규칙을 반영했다.
- agent는 새로 늘리지 않고 `.claude/agents/README.md`에 command 연결 관계만 문서화했다.
- Claude/Codex 공용 참조용 매트릭스는 `.todo/epics/e08-gstack-max-adoption/S03-command-role-map.md`에 정리했다.
