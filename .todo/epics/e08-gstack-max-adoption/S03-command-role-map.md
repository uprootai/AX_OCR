# S03 Command Role Map

> 기준일: 2026-03-23
> 목적: Claude/Codex가 모두 참조할 수 있는 AX 명령 체계 역할 매트릭스

## 1. gstack → AX 매핑

| gstack | AX 표면 | 상태 | 비고 |
|--------|---------|------|------|
| `/review` | `.claude/commands/review.md` | Adopt | 읽기 전용 리뷰로 도입 |
| `/investigate` | `.claude/commands/investigate.md` | Adopt | `/debug-issue`와 역할 분리 |
| `/plan-eng-review` | `.claude/commands/plan-eng-review.md` | Adopt | `/plan-epic`과 분리 |
| `/qa-only` | `.claude/commands/qa-only.md` | Adopt | S02 dual-ui Playwright 실행 기반과 연결 |
| `/codex` | `.claude/commands/codex-cross-check.md` | Adapt | Codex 단일 턴 교차검증 유지 |

## 2. 기존 명령과의 역할 분리

| 명령 | 새 역할 |
|------|---------|
| `/review` | diff와 인접 코드 경로를 읽기 전용으로 검토 |
| `/verify` | 변경 후 최소 검증 실행 |
| `/investigate` | root cause 중심 조사 |
| `/debug-issue` | 빠른 트리아지, legacy shortcut |
| `/qa-only` | 브라우저 read-only QA 보고 |
| `/plan-eng-review` | 구현 전 기술 타당성 점검 |
| `/plan-epic` | BMAD-Lite Epic/Story 분해 |
| `/codex-cross-check` | 단일 턴 2차 검증 패킷 생성 |

## 3. 구현 결정

- 새 command는 `.claude/commands/`에 추가하고, source of truth는 이 저장소 문서로 둔다.
- agent는 새로 늘리지 않고 `.claude/agents/README.md`로 command 연결만 문서화한다.
- handoff는 기존 `/handoff`를 유지하고, S03에서는 `Curated Context`가 command 이름과 결과를 포함하도록만 유도한다.
- QA evidence는 `.gstack/reports/playwright/` 경로를 공통 참조 경로로 사용한다.

## 4. Claude에게 넘길 때 핵심 파일

- `.claude/commands/README.md`
- `.claude/commands/review.md`
- `.claude/commands/investigate.md`
- `.claude/commands/plan-eng-review.md`
- `.claude/commands/qa-only.md`
- `.claude/commands/verify.md`
- `.claude/commands/debug-issue.md`
- `.claude/agents/README.md`
- `.todo/epics/e08-gstack-max-adoption/S03-ax-skills-commands.md`
