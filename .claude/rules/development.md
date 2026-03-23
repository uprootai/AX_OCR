---
paths:
  - "web-ui/**"
  - "gateway-api/**"
  - "blueprint-ai-bom/**"
---

# 개발 규칙

## 테스트 실행 원칙 (중요)

- `gateway-api` 기본 테스트는 E2E를 제외한 빠른 회귀 검증으로 실행한다.
- E2E는 외부 실행 서비스(`localhost:8000` 등) 의존이 있으므로 별도 명령으로만 실행한다.
- 기본 품질 확인 시 E2E 실패를 일반 회귀 실패와 혼합하지 않는다.

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
cd gateway-api && pytest                    # 기본: E2E 제외 (pytest.ini addopts)
cd gateway-api && pytest -m e2e tests/e2e -v  # 필요 시: E2E만 별도 실행

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

## 브라우저 자동화: Playwright vs Browser Use 역할 분담

두 MCP 서버를 **용도에 따라** 사용한다.

### Playwright MCP — 정확한 조작이 필요할 때

| 용도 | 예시 |
|------|------|
| 스크린샷 캡처 | 문서 사이트 페이지 확인 |
| 셀렉터 기반 조작 | 특정 버튼 클릭, 폼 입력 |
| 파일 업로드 | hidden input 처리 |
| HTTP 요청 | `playwright_post`로 API 호출 |
| E2E 테스트 실행 | `npm run test:e2e` |

```javascript
// Playwright: 정확한 셀렉터로 빠르게 조작
playwright_navigate({ url: "http://localhost:5173/blueprintflow/builder" })
playwright_upload_file({ selector: "input[type=file]", filePath: "/path/to/image.png" })
playwright_screenshot({ name: "result" })
```

### Browser Use MCP — AI가 알아서 탐색해야 할 때

| 용도 | 예시 |
|------|------|
| 외부 사이트 탐색 | 공급사 카탈로그 가격 조회 |
| 복잡한 다단계 워크플로 | "도면 업로드 → 분석 → 결과 검증" 전체 흐름 |
| 적응형 테스트 | UI가 자주 바뀌는 페이지 테스트 |
| 데이터 수집 | 여러 페이지 탐색하며 정보 추출 |
| 자연어 기반 검증 | "리더보드에서 1위 방법의 정확도가 80% 이상인지 확인" |

```python
# Browser Use: 목표만 주면 AI가 알아서 수행
browser_use_run_task("localhost:5173에서 Dimension Lab 페이지로 이동해서 배치평가 탭의 최신 결과를 확인하고 정확도를 JSON으로 반환해줘")
```

### 선택 기준

```
셀렉터를 알고 있는가? → Yes → Playwright
                      → No → Browser Use

외부 사이트인가? → Yes → Browser Use
                → No → Playwright (대부분)

결과가 deterministic해야 하는가? → Yes → Playwright
                                → No → Browser Use OK
```

## GPU 설정

- Dashboard에서 동적 설정 가능
- `docker-compose.override.yml` 사용
