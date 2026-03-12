# /verify - 자가 검증 커맨드

> 보리스 체니 전략 #13: 자가 검증 방법 제공

## 목적

코드 변경 후 빌드, 린트, 타입체크를 자동으로 실행하여 품질을 보장합니다.

## Verification Contract

검증 전 현재 변경 범위에 맞는 최소 계약을 정의합니다.

```xml
<contract>
  <goal>Changed scope에 대해 신뢰할 수 있는 최소 검증 수행</goal>
  <scope>이번 변경과 직접 관련된 패키지, 서비스, 파일</scope>
  <success_definition>필수 검증 통과 또는 차단 실패 1개 명확화</success_definition>
  <stop_conditions>
    <condition>Critical failure가 확인되면 후속 검증을 중단하고 보고한다.</condition>
    <condition>Docs-only or config-only change면 불필요한 빌드 전체 실행을 생략한다.</condition>
  </stop_conditions>
</contract>
```

운영 규칙:
- 기본은 변경 범위 중심의 최소 검증
- 전체 스택 검증은 다중 영역 변경, 배포 직전, 또는 사용자가 명시적으로 요청한 경우에만 수행
- 실패 시 raw 로그를 길게 붙이지 말고 실패 요약만 남긴다

## 실행 순서

### 1. 변경 파일 분석

```bash
git status --porcelain
git diff --name-only HEAD
```

분류 기준:
- `web-ui/`만 변경: frontend 검증 우선
- `gateway-api/`만 변경: backend 검증 우선
- `*.md`만 변경: 문서 검증만 하고 빌드 생략 가능
- 다중 서비스 변경: 관련 검증 후 필요 시 전체 검증

### 2. Frontend 검증 (TypeScript)

**web-ui:**
```bash
cd web-ui && npm run build && npm run lint
```

**blueprint-ai-bom frontend:**
```bash
cd blueprint-ai-bom/frontend && npm run build
```

### 3. Backend 검증 (Python)

**gateway-api:**
```bash
cd gateway-api && python -m py_compile api_server.py
cd gateway-api && pytest
# E2E 별도 검증(필요 시)
cd gateway-api && pytest -m e2e tests/e2e -v
```

**blueprint-ai-bom backend:**
```bash
cd blueprint-ai-bom/backend && python -m py_compile api_server.py
```

### 4. Docker 검증 (선택)

```bash
docker-compose config --quiet
```

### 5. API 헬스체크

```bash
curl -s http://localhost:5020/health
curl -s http://localhost:8000/api/v1/health
```

## Early Stop Rules

- 첫 번째 차단 실패가 나오면 동일 계층의 후속 무거운 검증은 중지
- 실패 원인이 명확하면 전체 테스트 대신 수정 또는 보고로 전환
- Health check만 필요한 상황에서는 빌드/테스트를 생략

## Failure Summary Format

```xml
<reflector>
  <failed_check/>
  <confirmed_facts/>
  <root_cause_candidate/>
  <next_action/>
</reflector>
```

## 출력 형식

```
✅ web-ui 빌드 성공
✅ blueprint-ai-bom frontend 빌드 성공
✅ gateway-api 문법 검증 통과
✅ BOM API healthy
⚠️ Gateway API degraded (일부 서비스 미실행)
```

## 사용 시점

- 코드 변경 완료 후
- 커밋 전
- PR 생성 전

## 관련 스킬

- `.claude/skills/devops-guide.md` - CI/CD 파이프라인
- `.claude/skills/modularization-guide.md` - 코드 품질 기준
- `.claude/skills/prompt-orchestration-guide.md` - 조기 종료, Reflector/Curator
