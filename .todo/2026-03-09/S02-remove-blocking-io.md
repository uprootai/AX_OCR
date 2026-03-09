# S02: Async 경로의 Blocking I/O 제거

> **Epic**: 2026-03-09 성능 개선 계획
> **상태**: ⬜ Todo
> **예상**: 1.5d
> **의존**: S01 권장

---

## 설명

`blueprint-ai-bom/backend`에는 `async def` 라우터가 동기 `requests.post` 또는 `httpx.Client` 기반 서비스를 직접 호출하는 경로가 남아 있다.
이 구조는 네트워크 대기 시간 동안 이벤트 루프를 점유하므로, 같은 워커에서 처리되는 다른 요청과 스트리밍 응답도 함께 지연시킨다.

핵심 작업은 다음과 같다.

1. `LineDetectorService`, `TableService`, `DimensionService`, `DetectionService`의 외부 API 호출을 `async` 버전으로 분리
2. async 라우터는 async 서비스만 호출하게 정리
3. CPU bound 처리만 필요한 경우 `run_in_threadpool` 또는 명시적 executor로 분리
4. 장시간 호출 경로는 timeout/cancellation 전파를 유지

## 완료 조건

- [ ] `blueprint-ai-bom/backend/routers/analysis/*` 주요 async 엔드포인트에서 동기 HTTP 호출이 제거된다
- [ ] `requests` 의존이 필요한 경로는 백그라운드 스레드 또는 async 대체 구현으로 치환된다
- [ ] line/table/dimension/detection 경로에서 취소와 timeout이 유지된다
- [ ] 동시 2개 이상 요청 시 서로 대기열처럼 막히는 현상이 완화된다
- [ ] 관련 테스트 또는 최소 smoke test가 추가된다

## 변경 범위

| 파일 | 작업 |
|------|------|
| `blueprint-ai-bom/backend/routers/analysis/line_router.py` | async 서비스 호출로 변경 |
| `blueprint-ai-bom/backend/routers/analysis/core_router.py` | sync 호출 경로 정리 |
| `blueprint-ai-bom/backend/services/line_detector_service.py` | async API client 도입 |
| `blueprint-ai-bom/backend/services/table_service.py` | sync `httpx.Client` 제거 |
| `blueprint-ai-bom/backend/services/dimension_service.py` | async OCR 호출 경로 정리 |
| `blueprint-ai-bom/backend/services/detection_service.py` | async YOLO 호출 경로 정리 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- async 라우터에서 blocking network I/O를 남기지 마세요.
- 외부 API 호출은 공용 async client를 받아 재사용할 수 있게 설계하세요.
- CPU 작업만 threadpool로 보내고, 네트워크 작업은 async로 유지하세요.
- 완료 후 동시 요청 smoke test를 수행하세요.
```

## 구현 노트

- 이 Story는 S03과 같이 진행하면 중복 작업이 줄어든다.
- 먼저 line/table 경로부터 바꾸고, dimension/detection으로 확장하는 단계적 접근이 안전하다.
