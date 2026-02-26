#!/bin/bash
# Post-Edit Quality Gate Hook
# MoAI 영감: Quality Gate (TaskCompleted 패턴)
# 트리거: PostToolUse — Edit/Write 후 (post-edit-format.sh 다음에 실행)
# 규칙: 항상 exit 0 (차단 없음, 정보 제공만)

FILE_PATH="${CLAUDE_FILE_PATH:-}"

# 파일이 없으면 종료
[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

EXT="${FILE_PATH##*.}"
BASENAME=$(basename "$FILE_PATH")
WARNINGS=()

# 테스트 파일 판별
is_test_file() {
    case "$1" in
        *.test.*|*.spec.*|*_test.*|*_spec.*|test_*|*/tests/*|*/__tests__/*) return 0 ;;
        *) return 1 ;;
    esac
}

# --- TS/JS: console.log 체크 (테스트 파일 제외) ---
if [[ "$EXT" =~ ^(ts|tsx|js|jsx)$ ]] && ! is_test_file "$FILE_PATH"; then
    COUNT=$(grep -c 'console\.log' "$FILE_PATH" 2>/dev/null)
    COUNT=${COUNT:-0}
    if [ "$COUNT" -gt 0 ]; then
        WARNINGS+=("- console.log ${COUNT}개 발견 (${BASENAME}) — 커밋 전 제거 권장")
    fi
fi

# --- Python: print() 체크 (테스트 파일 제외, 3개 초과 시) ---
if [[ "$EXT" == "py" ]] && ! is_test_file "$FILE_PATH"; then
    COUNT=$(grep -cE '^\s*print\(' "$FILE_PATH" 2>/dev/null)
    COUNT=${COUNT:-0}
    if [ "$COUNT" -gt 3 ]; then
        WARNINGS+=("- print() ${COUNT}개 발견 (${BASENAME}) — logger 사용 권장")
    fi
fi

# --- 공통: 하드코딩 시크릿 패턴 (double/single 따옴표 모두 검출) ---
if grep -qEi "(password|secret|api_key|api_secret|private_key)\s*=\s*[\"'][^\"']+[\"']" "$FILE_PATH" 2>/dev/null; then
    WARNINGS+=("- 하드코딩 시크릿 패턴 감지 (${BASENAME}) — 환경변수 사용 필수")
fi

# --- 공통: TODO/FIXME/HACK 누적 체크 (4개 초과 시) ---
COUNT=$(grep -cEi '\b(TODO|FIXME|HACK)\b' "$FILE_PATH" 2>/dev/null)
COUNT=${COUNT:-0}
if [ "$COUNT" -gt 4 ]; then
    WARNINGS+=("- TODO/FIXME/HACK ${COUNT}개 누적 (${BASENAME}) — 정리 필요")
fi

# --- 결과 출력 ---
if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo "<quality-gate>"
    printf '%s\n' "${WARNINGS[@]}"
    echo "</quality-gate>"
fi

exit 0
