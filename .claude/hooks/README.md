# Claude Code Hooks

에이전트 루프 생명주기의 단계를 관찰하고 자동화 스크립트를 실행합니다.

---

## 설정 파일

`.claude/settings.local.json`에서 hooks 정의:

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

---

## 사용 가능한 Hooks

### 1. PreToolUse
**시점**: 도구 사용 직전
**용도**: 파일 크기 체크, 리마인더 주입

| 스크립트 | 매처 | 기능 |
|----------|------|------|
| `pre-edit-check.sh` | `Edit\|Write` | 1000줄 이상 파일 경고 |

### 2. PostToolUse
**시점**: 도구 사용 직후
**용도**: 로깅, 검증

| 스크립트 | 매처 | 기능 |
|----------|------|------|
| `post-bash-log.sh` | `Bash` | 실패한 명령 로깅 |

### 3. Stop
**시점**: Claude 응답 완료 후
**용도**: 알림, 정리 작업

| 스크립트 | 매처 | 기능 |
|----------|------|------|
| `on-stop.sh` | `""` (전체) | 작업 완료 알림 (선택적) |

---

## 환경 변수

훅 스크립트에서 사용 가능한 환경 변수:

| 변수 | 설명 | 사용 가능한 훅 |
|------|------|--------------|
| `CLAUDE_TOOL_NAME` | 실행된 도구 이름 | PreToolUse, PostToolUse |
| `CLAUDE_FILE_PATH` | 대상 파일 경로 | PreToolUse (Edit/Write) |
| `CLAUDE_EXIT_CODE` | 종료 코드 | PostToolUse (Bash) |

---

## 스크립트 작성 가이드

### System Reminder 주입

```bash
echo "<system-reminder>"
echo "⚠️ 경고 메시지"
echo "참조: .claude/skills/modularization-guide.md"
echo "</system-reminder>"
```

### 조건부 실행

```bash
if [ "$LINE_COUNT" -gt 1000 ]; then
    # 경고 출력
fi
```

### 로깅

```bash
LOG_FILE=".claude/logs/$(date +%Y%m%d).log"
echo "[$(date)] $MESSAGE" >> "$LOG_FILE"
```

---

## 추가 가능한 Hooks 예시

### API 테스트 자동 실행
```bash
# PostToolUse에서 models/ 파일 수정 시 테스트 실행
if [[ "$CLAUDE_FILE_PATH" == *"models/"* ]]; then
    pytest tests/ -q 2>/dev/null || true
fi
```

### 컨텍스트 경고
```bash
# UserPromptSubmit에서 컨텍스트 사용률 체크
# (Claude Code 내부 API 필요)
```

### 특정 키워드 감지
```bash
# "새 API" 감지 시 가이드 리마인더
if echo "$CLAUDE_INPUT" | grep -qi "새.*API"; then
    echo "<system-reminder>"
    echo "📖 새 API 추가 가이드: .claude/skills/api-creation-guide.md"
    echo "</system-reminder>"
fi
```

---

## 파일 구조

```
.claude/
├── settings.local.json    # Hooks 설정
├── hooks/
│   ├── README.md          # 이 문서
│   ├── pre-edit-check.sh  # Edit/Write 전 체크
│   ├── post-bash-log.sh   # Bash 후 로깅
│   └── on-stop.sh         # 응답 완료 알림
└── logs/                  # 훅 로그 저장
```

---

## 주의사항

1. **성능**: 훅은 동기적으로 실행되므로 빠르게 완료되어야 함
2. **에러 처리**: 항상 `exit 0`으로 종료 (실패해도 Claude 작업 차단 안 함)
3. **권한**: 스크립트에 실행 권한 필요 (`chmod +x`)
4. **경로**: 프로젝트 루트 기준 상대 경로 사용

---

**마지막 업데이트**: 2026-01-16
**참조**: [sankalp.bearblog.dev - Claude Code 2.0 가이드](https://sankalp.bearblog.dev/my-experience-with-claude-code-20-and-how-to-get-better-at-using-coding-agents/)
