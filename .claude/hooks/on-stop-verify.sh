#!/bin/bash
# Stop Hook: 작업 완료 시 자동 검증
# 보리스 체니 전략 #12, #13 - 장기 작업 핸들링 + 자가 검증

# 변경된 파일 확인
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | head -20)

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

# 변경된 파일 유형 분석
HAS_TS=false
HAS_PY=false

for file in $CHANGED_FILES; do
    case "${file##*.}" in
        ts|tsx|js|jsx) HAS_TS=true ;;
        py) HAS_PY=true ;;
    esac
done

# 검증 결과 수집
ISSUES=""

# TypeScript 프로젝트 체크
if $HAS_TS; then
    # web-ui 빌드 체크
    if echo "$CHANGED_FILES" | grep -q "^web-ui/"; then
        if ! cd /home/uproot/ax/poc/web-ui && npm run build --silent 2>/dev/null; then
            ISSUES="$ISSUES\n- web-ui 빌드 실패"
        fi
    fi

    # blueprint-ai-bom frontend 빌드 체크
    if echo "$CHANGED_FILES" | grep -q "^blueprint-ai-bom/frontend/"; then
        if ! cd /home/uproot/ax/poc/blueprint-ai-bom/frontend && npm run build --silent 2>/dev/null; then
            ISSUES="$ISSUES\n- blueprint-ai-bom frontend 빌드 실패"
        fi
    fi
fi

# 이슈가 있으면 리마인더 출력
if [ -n "$ISSUES" ]; then
    echo "<system-reminder>"
    echo "⚠️ 자동 검증 결과 문제 발견:"
    echo -e "$ISSUES"
    echo "</system-reminder>"
fi

exit 0
