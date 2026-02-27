---
paths:
  - "web-ui/**"
  - "gateway-api/**"
  - "blueprint-ai-bom/**"
---

# 개발 규칙

## 프론트엔드 핵심 파일 (web-ui/)

| 목적 | 파일 경로 |
|------|----------|
| **API 레지스트리** | `src/config/apiRegistry.ts` |
| **노드 정의** | `src/config/nodeDefinitions.ts` |
| **스펙 서비스** | `src/services/specService.ts` |
| **API 클라이언트** | `src/lib/api.ts` |
| **스토어** | `src/store/workflowStore.ts`, `apiConfigStore.ts` |
| **BlueprintFlow** | `src/pages/blueprintflow/BlueprintFlowBuilder.tsx` |

## 개발 명령어

```bash
# 프론트엔드
cd web-ui && npm run dev       # 개발 서버
cd web-ui && npm run build     # 프로덕션 빌드
cd web-ui && npm run test:run  # 테스트

# 백엔드
cd gateway-api && pytest tests/ -v

# Docker
docker-compose up -d
docker logs gateway-api -f
```

## CI/CD 파이프라인

| 워크플로우 | 파일 | 트리거 |
|------------|------|--------|
| CI | `.github/workflows/ci.yml` | Push, PR (main, develop) |
| CD | `.github/workflows/cd.yml` | CI 성공 후 또는 수동 |

```
CI: Frontend (lint/build/test) + Backend (ruff/pytest) → Summary
CD: Pre-check → Build Images (6개) → Staging → Production (수동) → Rollback
```

## 코드 품질 기준

| 항목 | 기준 |
|------|------|
| TypeScript 빌드 | 에러 0개 |
| ESLint | 에러 0개 |
| 파일 크기 | 모든 파일 < 1000줄 |

## 자가 검증 (`/verify`)

```bash
# 1. TypeScript 빌드
cd web-ui && npm run build
cd blueprint-ai-bom/frontend && npm run build

# 2. Python 문법
python -m py_compile gateway-api/api_server.py

# 3. API 헬스체크
curl -s http://localhost:5020/health
curl -s http://localhost:8000/api/v1/health
```

## 새 API 추가

```bash
python scripts/create_api.py my-api --port 5025 --category detection
```

**상세 가이드**: `.claude/skills/api-creation-guide.md`, `.claude/skills/devops-guide.md`

## Playwright 브라우저 테스트 패턴

```javascript
// 1. 브라우저 열기
playwright_navigate({ url: "http://localhost:5173/blueprintflow/builder" })

// 2. 파일 업로드 (hidden input 처리)
playwright_evaluate({ script: "document.querySelector('input[type=file]').style.display='block'" })
playwright_upload_file({ selector: "input[type=file]", filePath: "/path/to/image.png" })

// 3. 스크린샷으로 결과 확인
playwright_screenshot({ name: "result" })
```

## GPU 설정

- Dashboard에서 동적 설정 가능
- `docker-compose.override.yml` 사용
