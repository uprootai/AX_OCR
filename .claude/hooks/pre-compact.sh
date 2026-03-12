#!/bin/bash
# PreCompact Hook: 컨텍스트 압축 전 진행 중 작업 보존
# 컴팩션 시 Curator 패킷 형태로 핵심 작업 상태만 주입

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
BRANCH=$(git branch --show-current 2>/dev/null)

# --- 출력 (컴팩션 시 보존할 컨텍스트) ---
echo "<context-to-preserve>"
echo "  <curator>"
echo "    <task_state>"
if [ -n "$ACTIVE_SUMMARY" ]; then
    printf '%s\n' "$ACTIVE_SUMMARY"
else
    echo "(no active stories found)"
fi
echo "    </task_state>"
echo "    <branch>"
if [ -n "$BRANCH" ]; then
    echo "$BRANCH"
else
    echo "(unknown branch)"
fi
echo "    </branch>"
echo "    <relevant_files>"
if [ -n "$STAGED" ] || [ -n "$CHANGED" ]; then
    [ -n "$STAGED" ] && printf 'Staged: %s\n' "$STAGED"
    [ -n "$CHANGED" ] && printf 'Modified: %s\n' "$CHANGED"
else
    echo "(clean working tree)"
fi
echo "    </relevant_files>"
echo "    <recent_commits>"
printf '%s\n' "$RECENT_COMMITS"
echo "    </recent_commits>"
echo "    <open_risks>"
echo "Infer from active work and uncommitted changes; avoid replaying full conversation."
echo "    </open_risks>"
echo "    <next_action>"
echo "Resume the active story, inspect modified files, and re-establish the current phase contract."
echo "    </next_action>"
echo "  </curator>"
echo "</context-to-preserve>"

exit 0
