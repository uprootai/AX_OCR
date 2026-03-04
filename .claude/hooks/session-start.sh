#!/bin/bash
# Session Greeting Hook
# MoAI 영감: Session Lifecycle (SessionStart)
# 트리거: UserPromptSubmit — 세션 첫 프롬프트 시 1회만 실행
# 30분 타임아웃으로 중복 실행 방지

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
GREETED_FILE="$LOG_DIR/.session_greeted"

mkdir -p "$LOG_DIR"

# 30분 이내 이미 인사했으면 종료
if [ -f "$GREETED_FILE" ]; then
    LAST=$(stat -c %Y "$GREETED_FILE" 2>/dev/null || echo "0")
    NOW=$(date +%s)
    DIFF=$(( NOW - LAST ))
    if [ "$DIFF" -lt 1800 ]; then
        exit 0
    fi
fi

# 타임스탬프 갱신
touch "$GREETED_FILE"

# --- Git 상태 수집 ---
cd "$PROJECT_ROOT" || exit 0

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git log -1 --format='%h %s' 2>/dev/null || echo "없음")
MODIFIED=$(git diff --name-only 2>/dev/null | wc -l)
STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)

# --- 출력 ---
echo "<session-greeting>"
echo "Branch: ${BRANCH} | Commit: ${LAST_COMMIT}"
echo "Changes: ${MODIFIED} modified, ${STAGED} staged, ${UNTRACKED} untracked"
echo "Reminder: .todo/ACTIVE.md 확인하세요"
echo "Test Policy: gateway-api 기본 pytest는 E2E 제외, E2E는 'pytest -m e2e tests/e2e -v'로 별도 실행"
echo "</session-greeting>"

exit 0
