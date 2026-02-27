#!/bin/bash
# PreCompact Hook: 컨텍스트 압축 전 진행 중 작업 보존
# 컴팩션 시 .todo/ACTIVE.md + 변경 파일 목록을 주입하여 작업 연속성 보장

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# --- 진행 중 Epic/Story 요약 ---
ACTIVE_FILE="$PROJECT_ROOT/.todo/ACTIVE.md"
ACTIVE_SUMMARY=""
if [ -f "$ACTIVE_FILE" ]; then
    # "in_progress" 또는 "⬜ Todo" 상태인 Story만 추출
    ACTIVE_SUMMARY=$(grep -E "(###|Story|⬜|🔄|in_progress)" "$ACTIVE_FILE" | head -10)
fi

# --- 미커밋 변경 파일 ---
cd "$PROJECT_ROOT" || exit 0
CHANGED=$(git diff --name-only 2>/dev/null | head -20)
STAGED=$(git diff --cached --name-only 2>/dev/null | head -20)

# --- 최근 커밋 ---
RECENT_COMMITS=$(git log --oneline -3 2>/dev/null)

# --- 출력 (컴팩션 시 보존할 컨텍스트) ---
echo "<context-to-preserve>"
echo "## Active Work"
if [ -n "$ACTIVE_SUMMARY" ]; then
    echo "$ACTIVE_SUMMARY"
else
    echo "(no active stories found)"
fi
echo ""
echo "## Uncommitted Changes"
if [ -n "$CHANGED" ] || [ -n "$STAGED" ]; then
    [ -n "$STAGED" ] && echo "Staged: $STAGED"
    [ -n "$CHANGED" ] && echo "Modified: $CHANGED"
else
    echo "(clean working tree)"
fi
echo ""
echo "## Recent Commits"
echo "$RECENT_COMMITS"
echo "</context-to-preserve>"

exit 0
