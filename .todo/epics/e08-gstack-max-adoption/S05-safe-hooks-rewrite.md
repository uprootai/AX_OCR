# S05: 기존 훅 체인 위 안전 훅 재설계

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 2d

---

## 설명

`gstack`의 `careful`/`freeze` 훅은 아이디어는 유용하지만 현재 검토 기준으로 그대로 도입할 수 없다.
이 Story에서는 AX 저장소의 기존 `.claude/hooks`와 `.claude/settings.local.json` 체계에 맞춰 안전 훅을 다시 설계한다.

반드시 막아야 하는 재현 케이스는 다음과 같다.

- 인용부호 안의 파괴적 명령이 잘리는 우회
- 경로 prefix 비교만으로 허용되는 우회
- 공백이 포함된 경로 오판
- 기존 `pre-edit-check.sh`, `post-edit-format.sh`, `post-edit-quality.sh`, `on-stop-verify.sh`와의 실행 순서 충돌

훅은 단순 경고를 넘어서, 어떤 명령/경로가 왜 막혔는지 사람이 이해할 수 있게 설명해야 한다.

## 완료 조건

- [x] quoted command 우회 재현 케이스가 차단된다.
- [x] prefix path 우회 재현 케이스가 차단된다.
- [x] 공백 포함 경로와 symlink/realpath 기준 판정이 정리된다.
- [x] 기존 `.claude` 훅과의 실행 순서가 정리된다.
- [x] `.claude/hooks` README 또는 동등한 문서에 동작 순서와 한계가 기록된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `.claude/hooks/` | 신규 또는 수정 |
| `.claude/settings.local.json` | 훅 연결 수정 |
| `.claude/hooks/README.md` | 수정 |
| `tests/hooks/` 또는 동등 경로 | 신규 |
| `.todo/epics/e08-gstack-max-adoption/` | 검증 메모 추가 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: gstack 아이디어를 유지하되 우회 가능한 쉘 훅은 AX 기준으로 재작성
- 필수: 인용부호 우회와 경로 prefix 우회 재현 케이스를 자동 테스트에 포함
- 필수 확인: session-start, pre-edit-check, post-edit-format, post-edit-quality, on-stop-verify와 책임이 겹치지 않아야 함
- 주의: 기존 `.claude/hooks` 동작을 깨지 않도록 실행 순서와 책임을 명확히 분리
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- 검토 기준 재현 스냅샷은 `/tmp/gstack-review`에 있다.
- 단순 문자열 prefix 비교 대신 `realpath` 기반 포함 관계 검증이 필요하다.
- 현재 저장소는 Stop hook에서 자동 검증을 이미 수행하므로, 차단형 훅과 정보형 훅의 책임 분리가 중요하다.
- `pre-bash-safety.sh`는 stdin JSON을 Python으로 파싱하고, `bash -lc "..."` 같은 nested shell command까지 재귀적으로 검사한다.
- `pre-write-safety.sh`는 `.gstack/state/freeze-dir.txt`를 기준으로 범위를 판정하고, `.env`, `*.pem`, `*.key` 같은 민감 경로는 `ask`로 승인을 요구한다.
- `post-edit-format.sh`, `post-edit-quality.sh`는 `CLAUDE_FILE_PATH` 단일 파일 전제이므로 현재는 `Edit|Write`에만 유지했다. `MultiEdit` 후행 포맷/품질 처리는 별도 Story에서 다룬다.
- 회귀 테스트는 `tests/hooks/test_ax_safety_hooks.py`에 추가했고, `pytest -q tests/hooks/test_ax_safety_hooks.py` 기준 `6 passed`를 확인했다.
