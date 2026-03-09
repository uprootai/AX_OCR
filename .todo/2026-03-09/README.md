# 2026-03-09 성능 개선 계획

> **상태**: ⬜ Todo
> **대상**: `web-ui` + `gateway-api` + `blueprint-ai-bom/backend`
> **목표**: 검토에서 확인된 상위 5개 비효율을 순차적으로 제거

---

## 우선순위

1. 이미지 payload 축소 및 base64 중복 제거
2. `blueprint-ai-bom`의 blocking I/O 제거
3. HTTP 클라이언트 재사용 구조 도입
4. BlueprintFlow 재렌더 범위 축소
5. 스펙/세션 메타데이터 캐시 도입

## 작업 순서

| 문서 | 목적 | 선행 조건 |
|------|------|-----------|
| `S01-image-payload-reduction.md` | 이미지 직렬화/복제 비용 제거 | 없음 |
| `S02-remove-blocking-io.md` | async 라우터의 이벤트 루프 블로킹 제거 | S01 권장 |
| `S03-http-client-pooling.md` | API 호출 keep-alive/connection pooling 복구 | S02 일부 연계 |
| `S04-blueprintflow-rerender-trim.md` | BlueprintFlow 화면 버벅임 완화 | S01 완료 권장 |
| `S05-spec-session-caching.md` | 메타데이터 조회 비용 축소 | 독립 진행 가능 |

## 완료 기준

- [ ] 이미지 전달 경로가 base64 JSON 중심 구조에서 바이너리/참조 중심 구조로 축소된다
- [ ] `blueprint-ai-bom/backend` 주요 async 엔드포인트에서 동기 HTTP 클라이언트 사용이 제거된다
- [ ] `gateway-api`와 `blueprint-ai-bom/backend`에 공용 HTTP client lifecycle이 도입된다
- [ ] BlueprintFlow 실행 중 heartbeat/update 이벤트에서 전체 캔버스 재렌더가 줄어든다
- [ ] `/api/v1/specs`, 세션 목록 조회의 디스크 반복 스캔이 캐시 또는 메모리 조회로 대체된다
- [ ] `web-ui` 빌드와 관련 백엔드 테스트/헬스체크가 다시 통과한다

## 검증 메모

- 정적 검토 기준 상위 병목은 이미지 payload, blocking I/O, connection churn, 전체 store 구독, 디스크 재스캔이었다.
- `web-ui` 빌드 확인 결과 `BlueprintFlowBuilder` 청크가 195KB 수준이라 재렌더 축소의 체감 효과가 클 가능성이 높다.
