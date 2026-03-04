#!/bin/bash
# Stop Hook: 작업 완료 시 자동 검증
# 보리스 체니 전략 #12, #13 - 장기 작업 핸들링 + 자가 검증

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# 변경된 파일 확인
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | head -50)

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

# 변경된 파일 유형 분석
HAS_TS=false
HAS_PY=false
HAS_DOCS=false
HAS_GATEWAY=false
HAS_GATEWAY_E2E=false

while IFS= read -r file; do
    case "${file##*.}" in
        ts|tsx|js|jsx) HAS_TS=true ;;
        py) HAS_PY=true ;;
    esac
    case "$file" in
        docs-site/*) HAS_DOCS=true ;;
        gateway-api/*) HAS_GATEWAY=true ;;
        gateway-api/tests/e2e/*) HAS_GATEWAY_E2E=true ;;
    esac
done <<< "$CHANGED_FILES"

# 검증 결과 수집
ISSUES=""

# TypeScript 프로젝트 체크 (stdout+stderr 모두 억제)
if $HAS_TS; then
    if echo "$CHANGED_FILES" | grep -q "^web-ui/"; then
        if ! (cd "$PROJECT_ROOT/web-ui" && npm run build &>/dev/null); then
            ISSUES="$ISSUES\n- web-ui 빌드 실패"
        fi
    fi

    if echo "$CHANGED_FILES" | grep -q "^blueprint-ai-bom/frontend/"; then
        if ! (cd "$PROJECT_ROOT/blueprint-ai-bom/frontend" && npm run build &>/dev/null); then
            ISSUES="$ISSUES\n- blueprint-ai-bom frontend 빌드 실패"
        fi
    fi
fi

# Python 문법 체크 (ast.parse — sys.argv로 경로 전달, injection 방지)
if $HAS_PY; then
    while IFS= read -r file; do
        case "$file" in
            *.py)
                FULL_PATH="$PROJECT_ROOT/$file"
                if [ -f "$FULL_PATH" ]; then
                    if ! python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$FULL_PATH" 2>/dev/null; then
                        ISSUES="$ISSUES\n- Python 구문 오류: $file"
                    fi
                fi
                ;;
        esac
    done <<< "$CHANGED_FILES"
fi

# docs-site 빌드 체크
if $HAS_DOCS; then
    if [ -f "$PROJECT_ROOT/docs-site/package.json" ]; then
        if ! (cd "$PROJECT_ROOT/docs-site" && npm run build &>/dev/null); then
            ISSUES="$ISSUES\n- docs-site 빌드 실패"
        fi
    fi
fi

# gateway-api 기본 테스트 (pytest.ini에서 e2e 제외 정책 적용)
if $HAS_GATEWAY; then
    if ! (cd "$PROJECT_ROOT/gateway-api" && pytest -q &>/dev/null); then
        ISSUES="$ISSUES\n- gateway-api 기본 테스트 실패 (E2E 제외)"
    fi
fi

# gateway-api E2E 변경 감지 시 별도 실행 안내
if $HAS_GATEWAY_E2E; then
    ISSUES="$ISSUES\n- 참고: E2E 변경 감지됨. 필요 시 수동 실행: cd gateway-api && pytest -m e2e tests/e2e -v"
fi

# 이슈가 있으면 리마인더 출력
if [ -n "$ISSUES" ]; then
    echo "<system-reminder>"
    echo "자동 검증 결과 문제 발견:"
    echo -e "$ISSUES"
    echo "</system-reminder>"
fi

exit 0
