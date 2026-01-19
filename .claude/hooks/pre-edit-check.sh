#!/bin/bash
# Pre-Edit Check Hook
# Edit/Write 도구 사용 전 실행

# 환경 변수로 전달되는 정보:
# - CLAUDE_TOOL_NAME: 도구 이름
# - CLAUDE_FILE_PATH: 대상 파일 경로 (있는 경우)

FILE_PATH="${CLAUDE_FILE_PATH:-}"

if [ -n "$FILE_PATH" ]; then
    # 파일 크기 체크 (1000줄 이상 경고)
    if [ -f "$FILE_PATH" ]; then
        LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null || echo "0")
        if [ "$LINE_COUNT" -gt 1000 ]; then
            echo "<system-reminder>"
            echo "⚠️ 파일 크기 경고: $FILE_PATH ($LINE_COUNT줄)"
            echo "1000줄 이상 파일입니다. 분리를 고려하세요."
            echo "참조: .claude/skills/modularization-guide.md"
            echo "</system-reminder>"
        fi
    fi
fi

exit 0
