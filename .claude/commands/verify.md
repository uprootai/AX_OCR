# /verify - 자가 검증 커맨드

> 보리스 체니 전략 #13: 자가 검증 방법 제공

## 목적

코드 변경 후 빌드, 린트, 타입체크를 자동으로 실행하여 품질을 보장합니다.

## 실행 순서

### 1. 변경 파일 분석

```bash
git status --porcelain
git diff --name-only HEAD
```

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
