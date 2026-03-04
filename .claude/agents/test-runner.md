---
name: test-runner
description: 테스트 실행 에이전트. 변경 파일 기반으로 관련 테스트를 자동 선택하여 실행. 빌드 + 린트 + 유닛 테스트를 격리 컨텍스트에서 수행.
tools:
  - Bash
  - Read
  - Grep
  - Glob
disallowedTools:
  - Write
  - Edit
model: haiku
maxTurns: 10
---

# Test Runner

변경 파일에 맞는 테스트를 자동 선택하여 실행합니다.

## 실행 전략

1. **변경 파일 감지**: `git diff --name-only` 기반
2. **테스트 선택**:
   - `web-ui/**` 변경 → `cd web-ui && npm run test:run`
   - `gateway-api/**` 변경 → `cd gateway-api && pytest` (기본: E2E 제외)
   - `gateway-api/tests/e2e/**` 또는 사용자가 E2E 요청 → `cd gateway-api && pytest -m e2e tests/e2e -v`
   - `blueprint-ai-bom/**` 변경 → `cd blueprint-ai-bom/frontend && npm run build`
   - `docs-site/**` 변경 → `cd docs-site && npm run build`
3. **빌드 검증**:
   - TypeScript: `cd web-ui && npx tsc --noEmit`
   - Python: `python3 -c "import ast; ast.parse(open('<file>').read())"`

## 출력 형식

```
## 테스트 결과
- 프론트엔드: PASS/FAIL (N개 통과)
- 백엔드: PASS/FAIL (N개 통과)
- 빌드: PASS/FAIL
- 소요 시간: Ns
```
