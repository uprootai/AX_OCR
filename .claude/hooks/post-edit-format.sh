#!/bin/bash
# Post-tool Hook: Edit/Write 후 자동 포매팅
# 보리스 체니 전략 #9 - 포매팅 문제 10% 자동 해결

FILE_PATH="$CLAUDE_FILE_PATH"

# 파일이 없으면 종료
[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# 확장자 추출
EXT="${FILE_PATH##*.}"

# TypeScript/JavaScript 파일 포매팅
if [[ "$EXT" == "ts" || "$EXT" == "tsx" || "$EXT" == "js" || "$EXT" == "jsx" ]]; then
    # prettier가 있으면 실행
    if command -v npx &> /dev/null; then
        # 프로젝트 루트 찾기
        DIR=$(dirname "$FILE_PATH")
        while [ "$DIR" != "/" ]; do
            if [ -f "$DIR/package.json" ]; then
                cd "$DIR"
                npx prettier --write "$FILE_PATH" 2>/dev/null || true
                npx eslint --fix "$FILE_PATH" 2>/dev/null || true
                break
            fi
            DIR=$(dirname "$DIR")
        done
    fi
fi

# Python 파일 포매팅
if [[ "$EXT" == "py" ]]; then
    if command -v ruff &> /dev/null; then
        ruff format "$FILE_PATH" 2>/dev/null || true
        ruff check --fix "$FILE_PATH" 2>/dev/null || true
    elif command -v black &> /dev/null; then
        black "$FILE_PATH" 2>/dev/null || true
    fi
fi

exit 0
