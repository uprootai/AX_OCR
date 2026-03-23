# Claude Code Hooks

에이전트 루프 생명주기의 단계를 관찰하고 자동화 스크립트를 실행합니다.
현재 AX 저장소는 정보형 훅과 차단형 훅을 함께 사용합니다.

---

## 설정 파일

`.claude/settings.local.json`에서 hooks 정의:

```json
{
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "PreCompact": [...],
    "Stop": [...]
  }
}
```

---

## 실행 순서

### 1. PreToolUse
**시점**: 도구 사용 직전
**용도**: 위험 명령 차단, 민감 파일/수정 범위 제어, 파일 크기 경고

| 스크립트 | 매처 | 기능 |
|----------|------|------|
| `pre-bash-safety.sh` | `Bash` | 파괴적 명령 감지 후 `ask` 또는 `deny` |
| `pre-write-safety.sh` | `Edit\|Write\|MultiEdit` | 민감 파일 수정 확인, freeze 범위 밖 수정 차단 |
| `pre-edit-check.sh` | `Edit\|Write\|MultiEdit` | 1000줄 이상 파일 경고 |

### 2. PostToolUse
**시점**: 도구 사용 직후
**용도**: 로깅, 포맷/품질 체크

| 스크립트 | 매처 | 기능 |
|----------|------|------|
| `post-bash-log.sh` | `Bash` | 실패한 명령 로깅 |
| `post-edit-format.sh` | `Edit\|Write` | 저장 후 포맷 보정 |
| `post-edit-quality.sh` | `Edit\|Write` | 저장 후 품질 체크 |

### 3. Stop
**시점**: Claude 응답 완료 후
**용도**: 알림, 변경 파일 기반 검증

| 스크립트 | 매처 | 기능 |
|----------|------|------|
| `on-stop.sh` | `""` (전체) | 작업 완료 알림 (선택적) |
| `on-stop-verify.sh` | `""` (전체) | 변경 파일 기반 자동 검증 (빌드/구문/pytest 기본) |

---

## 차단형 훅 동작 방식

PreToolUse 훅은 stdin으로 전달된 JSON payload를 읽고, 필요한 경우 stderr에 JSON을 출력한 뒤 `exit 2`로 종료해 Claude에 `allow`, `ask`, `deny` 결정을 전달합니다.

예시:

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "ask"
  },
  "systemMessage": "Destructive recursive delete requires confirmation: rm -rf /tmp/pwn"
}
```

현재 AX 차단형 훅은 `grep` 기반 문자열 절단 대신 Python JSON 파싱을 사용합니다.

---

## 환경 변수와 입력

훅 스크립트는 환경 변수와 stdin JSON을 함께 사용합니다.

| 항목 | 설명 | 사용 가능한 훅 |
|------|------|--------------|
| `CLAUDE_TOOL_NAME` | 실행된 도구 이름 | PreToolUse, PostToolUse |
| `CLAUDE_FILE_PATH` | 대상 파일 경로 | 일부 PreToolUse |
| `CLAUDE_EXIT_CODE` | 종료 코드 | PostToolUse (Bash) |
| stdin JSON | `tool_input.command`, `tool_input.file_path` 등 도구 입력 | PreToolUse |
| `AX_HOOK_PROJECT_ROOT` | 프로젝트 루트 강제 지정 | `pre-write-safety.sh` |
| `AX_HOOK_STATE_DIR` | hook 상태 디렉터리 지정 | `pre-write-safety.sh` |

---

## Freeze 상태 파일

AX의 freeze 상태는 repo-local ignored path에 저장합니다.

| 경로 | 의미 |
|------|------|
| `.gstack/` | 로컬 아티팩트 루트 (`.gitignore`로 무시) |
| `.gstack/state/` | 훅 상태 디렉터리 |
| `.gstack/auth/` | storage state, 임시 auth 파일 (민감 정보) |
| `.gstack/state/freeze-dir.txt` | 활성 수정 범위 루트 1개를 저장 |

`pre-write-safety.sh`는 `realpath` 성격의 `resolve(strict=False)` + `os.path.commonpath()`로 범위를 판정합니다.
그래서 단순 prefix 비교, 공백 포함 경로, `/app` vs `/application` 같은 우회를 막습니다.

---

## 현재 안전 훅 규칙

### `pre-bash-safety.sh`

- `deny`: `mkfs*`, `dd if=... of=/dev/...`, `rm -rf /`, `rm -rf ~`
- `ask`: 일반 recursive `rm`, `git reset --hard`, `git checkout --`, `git clean -fdx`, `git push --force`, `docker * prune`, `DROP TABLE`, `TRUNCATE`
- 예외: `dist`, `build`, `coverage`, `__pycache__`, `node_modules` 같은 안전 cleanup 타겟은 허용
- 특징: `bash -lc "rm -rf ..."` 같은 중첩 shell command를 재귀적으로 파싱

### `pre-write-safety.sh`

- `ask`: `.env`, `.env.*`, `*.pem`, `*.key`, `credentials`, `secrets` 경로 수정
- `deny`: freeze가 활성화된 상태에서 수정 대상이 freeze 루트 밖일 때
- 특징: 상대 경로 입력도 프로젝트 루트 기준 절대 경로로 정규화 후 판정

---

## 테스트 위치

안전 훅 회귀 테스트는 아래 경로에 둡니다.

```text
tests/hooks/test_ax_safety_hooks.py
```

검증 예시:

```bash
pytest -q tests/hooks/test_ax_safety_hooks.py
```

---

## 파일 구조

```text
.claude/
├── settings.local.json        # Hooks 설정
├── hooks/
│   ├── README.md              # 이 문서
│   ├── pre-bash-safety.sh     # Bash 차단형 안전 훅
│   ├── pre-write-safety.sh    # Edit/Write 차단형 안전 훅
│   ├── pre-edit-check.sh      # 대형 파일 경고
│   ├── post-bash-log.sh       # Bash 후 로깅
│   ├── on-stop.sh             # 응답 완료 알림
│   └── on-stop-verify.sh      # 응답 완료 자동 검증
└── logs/                      # 훅 로그 저장
```

---

## 주의사항

1. **성능**: 훅은 동기적으로 실행되므로 빠르게 완료되어야 함
2. **차단형 종료 코드**: 안내용 훅은 `exit 0`, 차단형 훅은 stderr JSON + `exit 2`를 사용
3. **권한**: 스크립트에 실행 권한 필요 (`chmod +x`)
4. **경로 기준**: 프로젝트 루트 기준 상대 경로 사용, freeze 판정은 repo-local `.gstack/state` 기준
5. **아티팩트 정책**: `.gstack/`은 공유 산출물이 아니라 로컬 런타임 상태 저장소다
6. **민감 파일**: `.gstack/auth/`, storage state, token이 포함된 파일은 커밋/공유 금지

---

**마지막 업데이트**: 2026-03-23
