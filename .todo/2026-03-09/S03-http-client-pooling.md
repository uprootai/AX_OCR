# S03: HTTP Client Pooling 공용화

> **Epic**: 2026-03-09 성능 개선 계획
> **상태**: ⬜ Todo
> **예상**: 1d
> **의존**: S02 일부 연계

---

## 설명

현재 `gateway-api`와 `blueprint-ai-bom/backend`는 API 호출마다 새 `httpx.AsyncClient` 또는 `httpx.Client`를 만들고 바로 닫는 패턴이 넓게 퍼져 있다.
이렇게 하면 keep-alive, connection reuse, DNS/TCP 재사용 이점을 잃고 fan-out이 많은 파이프라인에서 지연이 누적된다.

이 Story는 애플리케이션 수명주기에 맞춘 공용 HTTP 클라이언트 계층을 도입하는 작업이다.

핵심 작업은 다음과 같다.

1. 앱 lifespan에서 공용 `AsyncClient` 초기화/종료
2. executor/service에 client를 주입하거나 accessor로 제공
3. timeout/limits/retries를 중앙 설정으로 통합
4. sync-only 경로는 가능한 범위에서 async로 전환하고, 불가 시 최소한 재사용 가능한 client wrapper 제공

## 완료 조건

- [ ] `gateway-api` 주요 executor가 공용 `AsyncClient`를 사용한다
- [ ] `workflow_router`, health check, spec/registry 관련 네트워크 호출이 같은 client pool을 사용한다
- [ ] `blueprint-ai-bom/backend` 외부 API 호출도 공용 client 경로로 정리된다
- [ ] timeout, connection limit, retry 정책이 파일마다 흩어져 있지 않고 공통화된다
- [ ] 회귀 없이 기존 API 호출 테스트가 통과한다

## 변경 범위

| 파일 | 작업 |
|------|------|
| `gateway-api/api_server.py` | lifespan 기반 HTTP client 등록 |
| `gateway-api/blueprintflow/executors/base_executor.py` | per-call client 생성 제거 |
| `gateway-api/blueprintflow/executors/generic_api_executor.py` | 공용 client 사용 |
| `gateway-api/routers/workflow_router.py` | template/BOM API 호출 공용화 |
| `blueprint-ai-bom/backend/api_server.py` | backend client lifecycle 추가 |
| `blueprint-ai-bom/backend/services/*` | 외부 API 호출 wrapper 정리 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- httpx client lifecycle을 앱 startup/shutdown에 묶으세요.
- timeout과 retry는 호출부마다 하드코딩하지 말고 중앙 설정화하세요.
- 새 구조가 테스트하기 쉽도록 dependency injection 경로를 남기세요.
```

## 구현 노트

- `APICallerMixin`이 이미 공통점 역할을 하고 있으므로, 여기서 client 주입 지점을 만드는 것이 가장 파급력이 크다.
- S02 완료 전에 공용 client 틀부터 만들면 이후 async 전환이 쉬워진다.
