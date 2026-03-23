# Custom Claude Code Commands

이 디렉토리에는 Claude Code 운영에 쓰는 커스텀 커맨드가 들어 있습니다.

---

## 사용 가능한 Commands (14개)

| 커맨드 | 용도 | 추천 시점 |
|--------|------|-----------|
| `/verify` | 변경 범위 기반 자가 검증 | 코드 수정 후, 커밋 전 |
| `/review` | 읽기 전용 코드 리뷰 | 구현 후, PR 전 |
| `/investigate` | root cause 중심 조사 | 원인 미확정 버그, 재현 실패 |
| `/plan-eng-review` | 구현 전 엔지니어링 리뷰 | 아키텍처/범위 변경 전 |
| `/qa-only` | 읽기 전용 브라우저 QA 보고 | UI 흐름 확인, 수정 전 증거 수집 |
| `/simplify` | 중복 제거, 구조 단순화 | 리팩터링, 복잡도 감소 |
| `/handoff` | 세션 전환용 압축 문서 생성 | 컨텍스트 60%+, 작업 전환 |
| `/plan-epic` | Epic 기획과 Story 분해 | 큰 작업 시작 전 |
| `/add-feature` | 새 기능 추가 워크플로우 | API/기능 확장 |
| `/debug-issue` | 계약형 디버깅 + Reflector/Curator | 실패 원인 추적 |
| `/codex-cross-check` | Codex 단일 턴 검증 패킷 생성 | 고위험 판단, 반복 실패 |
| `/rebuild-service` | Docker 서비스 재빌드 | 컨테이너 문제, 설정 반영 |
| `/test-api` | API 엔드포인트 테스트 | 서비스 상태 점검 |
| `/track-issue` | KNOWN_ISSUES 기반 이슈 추적 | 버그 접수, 조사 기록 |

---

## 핵심 운영 포인트

### `/verify`
- 변경 범위에 맞는 최소 검증을 우선
- 첫 차단 실패가 나오면 무거운 후속 검증 중지
- 실패는 raw 로그 대신 Reflector 요약으로 남김

### `/review`
- findings first 원칙으로 버그, 리스크, 회귀 가능성을 먼저 보고
- `/verify` 전체를 중복 실행하지 않고 필요한 증거만 좁게 수집
- `code-reviewer` agent와 가장 잘 맞음

### `/investigate`
- 새 조사 작업의 기본 명령
- 증상 1개, 가설 최대 2개, root cause 후보 1개로 수렴
- 길어지면 Curator 패킷으로 `/handoff` 또는 `/codex-cross-check`로 전환

### `/plan-eng-review`
- 구현 전에 touched surface, API contract, test matrix, rollout risk를 검토
- `/plan-epic`과 달리 Story 분해가 아니라 기술 타당성 평가가 목적

### `/qa-only`
- 수정 없이 브라우저를 눌러보고 증거만 남김
- `.gstack/reports/playwright` 경로를 공통 artifact root로 사용
- `/verify`와 달리 빌드/pytest보다 사용자 흐름과 화면 근거가 중심

## 브라우저 QA 롤아웃

- CI smoke: `.github/workflows/ci.yml`의 `frontend-smoke` job이 `cd web-ui && npm run test:e2e:dual-ui`를 실행
- 로컬 full: BOM workflow 변경 시 `cd web-ui && npm run test:e2e:bom`을 추가 실행
- deploy 계열 command는 아직 guard-only이며, 기준 문서는 `.todo/epics/e08-gstack-max-adoption/rollout-guide.md`

### `/debug-issue`
- 먼저 `Debug Contract`를 좁게 정의
- 로그를 무한히 붙이지 않고 원인 후보 1개로 수렴
- 실패가 길어지면 Curator 패킷으로 `/handoff` 또는 Codex 검증 전환

### `/codex-cross-check`
- Codex를 장기 대화 상대가 아니라 단일 턴 검증기로 사용
- `task`, `decision_request`, `constraints`, `relevant_files`, `current_hypothesis`, `diff_summary`만 전달
- 시스템 템플릿은 `/home/uproot/ax/poc/.claude/templates/codex-cross-check-system-prompt.xml` 사용

### `/handoff`
- 전체 대화 복붙 금지
- `Curated Context`에 다음 세션에 필요한 안정 사실만 남김

---

## 빠른 사용

```bash
/review
/investigate
/plan-eng-review
/qa-only
/verify
/debug-issue
/codex-cross-check
/handoff
/test-api gateway
/rebuild-service gateway-api
```

---

## Best Practices

1. 구현 전에 `/plan-eng-review` 또는 `/plan-epic`으로 범위와 표면을 먼저 좁힌다.
2. 구현 후에는 `/review`로 위험을 식별하고, 이어서 `/verify`로 최소 검증을 실행한다.
3. UI 문제는 수정 전에 `/qa-only`로 재현과 artifact를 먼저 남기고, 변경 후에는 `npm run test:e2e:dual-ui`를 기본 smoke로 실행한다.
4. 원인이 불명확한 실패는 `/investigate`를 우선하고, legacy 흐름이 필요할 때만 `/debug-issue`를 사용한다.
5. 여전히 판단이 팽팽하면 `/codex-cross-check`로 단일 턴 검증 패킷을 만든다.
6. 세션이 길어지면 `/compact` 또는 `/handoff`로 컨텍스트를 정화한다.
7. 버그는 `/track-issue`로 남겨 재발 방지 기록을 유지한다.

---

## 관련 Skills

- `/home/uproot/ax/poc/.claude/skills/feature-implementer.md`
- `/home/uproot/ax/poc/.claude/skills/prompt-orchestration-guide.md`
- `/home/uproot/ax/poc/.claude/skills/devops-guide.md`
- `/home/uproot/ax/poc/.claude/skills/context-engineering-guide.md`

---

**마지막 업데이트**: 2026-03-23
**버전**: 5.0.0
