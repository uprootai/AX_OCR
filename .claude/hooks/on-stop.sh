#!/bin/bash
# On-Stop Hook
# Claude 응답 완료 후 실행

# 선택적: 데스크탑 알림 (Linux)
# notify-send "Claude Code" "작업 완료" 2>/dev/null || true

# 선택적: 소리 알림 (WSL에서는 작동 안 할 수 있음)
# echo -e '\a' 2>/dev/null || true

exit 0
