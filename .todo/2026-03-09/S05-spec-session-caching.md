# S05: 스펙 및 세션 메타데이터 캐시 도입

> **Epic**: 2026-03-09 성능 개선 계획
> **상태**: ⬜ Todo
> **예상**: 0.5d

---

## 설명

현재 API 스펙과 세션 목록 조회는 요청이 올 때마다 디스크를 다시 훑고 JSON/YAML을 재파싱하는 경로가 남아 있다.
파일 수가 늘어나면 관리 화면과 빌더 진입 시 체감 지연이 커지고, 의미 없는 I/O가 계속 발생한다.

이 Story는 자주 읽히고 드물게 바뀌는 메타데이터를 메모리 캐시 또는 명시적 refresh 방식으로 정리하는 작업이다.

핵심 작업은 다음과 같다.

1. `gateway-api`의 `/api/v1/specs` 계열에서 스펙 캐시 재사용
2. 스펙 변경 시 명시적 invalidate 경로 추가
3. `SessionService.list_sessions`가 매번 디스크 전체를 읽지 않도록 메모리 우선 구조로 변경
4. 프로젝트별 세션 조회가 전체 1000건 재스캔을 기본 경로로 쓰지 않도록 개선
5. 프런트는 이미 있는 cache/react-query와 중복 fetch를 줄이도록 연결

## 완료 조건

- [ ] `/api/v1/specs`가 요청마다 YAML 전체를 재파싱하지 않는다
- [ ] 세션 목록 조회가 메모리 캐시 또는 증분 갱신 구조를 사용한다
- [ ] 프로젝트별 세션 조회가 전체 세션 재로딩 없이 동작한다
- [ ] 프런트의 스펙 fetch가 불필요하게 중복 호출되지 않는다
- [ ] 캐시 무효화 경로가 문서화되거나 코드에 드러난다

## 변경 범위

| 파일 | 작업 |
|------|------|
| `gateway-api/api_registry.py` | 스펙 캐시 재사용 |
| `gateway-api/routers/spec_router.py` | 캐시 사용 및 refresh 경로 정리 |
| `web-ui/src/services/specService.ts` | fetch 전략 조정 |
| `web-ui/src/hooks/useNodeDefinitions.ts` | 중복 로드 축소 |
| `blueprint-ai-bom/backend/services/session_service.py` | 세션 목록 캐시 개선 |
| `blueprint-ai-bom/backend/routers/session_router.py` | 조회 경로 검증 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 캐시는 무효화 전략 없이 넣지 마세요.
- 파일 기반 저장은 유지하되, read path는 메모리 우선으로 바꾸세요.
- 프런트와 백엔드 둘 다 중복 fetch/scan을 줄이는 방향으로 정리하세요.
```

## 구현 노트

- `api_registry`는 이미 singleton이므로 `get_all_specs()` 쪽만 캐시를 타게 바꾸면 바로 효과가 난다.
- `SessionService`는 저장 시점에 메모리 갱신이 이미 있으므로 list 경로를 디스크 스캔 대신 메모리 기준으로 돌릴 수 있다.
