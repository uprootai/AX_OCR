# Custom Claude Code Commands

이 디렉토리에는 Claude Code 운영에 쓰는 커스텀 커맨드가 들어 있습니다.

---

## 사용 가능한 Commands (10개)

| 커맨드 | 용도 | 추천 시점 |
|--------|------|-----------|
| `/verify` | 변경 범위 기반 자가 검증 | 코드 수정 후, 커밋 전 |
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
/verify
/debug-issue
/codex-cross-check
/handoff
/test-api gateway
/rebuild-service gateway-api
```

---

## Best Practices

1. 구현 전에는 `/skill feature-implementer` 또는 계획 문서로 현재 Phase를 좁힌다.
2. 검증은 항상 `/verify`로 시작하고, 실패가 반복되면 `/debug-issue`로 이동한다.
3. 여전히 판단이 팽팽하면 `/codex-cross-check`로 단일 턴 검증 패킷을 만든다.
4. 세션이 길어지면 `/compact` 또는 `/handoff`로 컨텍스트를 정화한다.
5. 버그는 `/track-issue`로 남겨 재발 방지 기록을 유지한다.

---

## 관련 Skills

- `/home/uproot/ax/poc/.claude/skills/feature-implementer.md`
- `/home/uproot/ax/poc/.claude/skills/prompt-orchestration-guide.md`
- `/home/uproot/ax/poc/.claude/skills/devops-guide.md`
- `/home/uproot/ax/poc/.claude/skills/context-engineering-guide.md`

---

**마지막 업데이트**: 2026-03-12
**버전**: 4.0.0
