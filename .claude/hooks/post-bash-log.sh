#!/bin/bash
# Post-Bash Log Hook
# Bash 명령 실행 후 로깅

# 환경 변수:
# - CLAUDE_TOOL_NAME: 도구 이름
# - CLAUDE_EXIT_CODE: 종료 코드

EXIT_CODE="${CLAUDE_EXIT_CODE:-0}"
LOG_DIR="/home/uproot/ax/poc/.claude/logs"
LOG_FILE="$LOG_DIR/bash_$(date +%Y%m%d).log"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 실패한 명령만 로깅
if [ "$EXIT_CODE" -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] EXIT_CODE=$EXIT_CODE" >> "$LOG_FILE"
fi

exit 0
