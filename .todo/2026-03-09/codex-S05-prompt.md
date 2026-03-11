# Codex CLI Prompt — S05: 스펙 및 세션 메타데이터 캐시 도입

## 프로젝트 규칙 (반드시 준수)
- 파일 1000줄 초과 금지 → 초과 시 즉시 분리
- base64 이미지 전송 금지
- Python: FastAPI + Pydantic v2, async 우선
- TypeScript: React 19 + Zustand
- 변경 후 검증: `python3 -c "import ast; ast.parse(open(f).read())"` / `npx tsc --noEmit`

## 작업 내용

현재 API 스펙과 세션 목록 조회는 요청마다 디스크를 다시 훑고 JSON/YAML을 재파싱한다.
자주 읽히고 드물게 바뀌는 메타데이터를 메모리 캐시로 정리하라.

### 변경 대상 파일

| 파일 | 작업 |
|------|------|
| `gateway-api/api_registry.py` | `get_all_specs()` 결과를 메모리 캐시, 변경 시 invalidate |
| `gateway-api/routers/spec_router.py` | 캐시 사용 및 refresh 엔드포인트 추가 |
| `web-ui/src/services/specService.ts` | 중복 fetch 제거 (stale-while-revalidate 또는 간단 캐시) |
| `web-ui/src/hooks/useNodeDefinitions.ts` | 중복 로드 축소 |
| `blueprint-ai-bom/backend/services/session_service.py` | `list_sessions`를 메모리 우선 조회로 변경, 디스크 스캔은 초기화/invalidate 시만 |
| `blueprint-ai-bom/backend/routers/session_router.py` | 조회 경로 검증 |

### 완료 조건

- `/api/v1/specs`가 요청마다 YAML 전체를 재파싱하지 않는다
- 세션 목록 조회가 메모리 캐시 또는 증분 갱신 구조를 사용한다
- 프로젝트별 세션 조회(`list_sessions_by_project`)가 전체 세션 1000건 재로딩 없이 동작한다
- 캐시 무효화 경로가 코드에 명시적으로 존재한다 (세션 생성/삭제 시 자동 invalidate)
- 기존 테스트 통과, `web-ui` 빌드 성공

### 구현 힌트

- `api_registry`는 이미 singleton이므로 `get_all_specs()` 쪽만 캐시를 타게 바꾸면 바로 효과
- `SessionService`는 저장 시점에 메모리 갱신이 이미 있으므로 list 경로를 디스크 스캔 대신 메모리 기준으로 돌릴 수 있음
- 캐시는 무효화 전략 없이 넣지 말 것
- 파일 기반 저장은 유지하되 read path는 메모리 우선으로 변경

### 검증 명령어

```bash
# Python 구문 확인
python3 -c "import ast; ast.parse(open('gateway-api/api_registry.py').read())"
python3 -c "import ast; ast.parse(open('blueprint-ai-bom/backend/services/session_service.py').read())"

# TypeScript 빌드
cd web-ui && npx tsc --noEmit

# 헬스체크
curl -s http://localhost:8000/health
curl -s http://localhost:5020/health
```
