# S01: 이미지 Payload 축소 및 중복 제거

> **Epic**: 2026-03-09 성능 개선 계획
> **상태**: ⬜ Todo
> **예상**: 1.5d

---

## 설명

현재 BlueprintFlow는 업로드 이미지를 Data URL/base64로 읽어 전역 상태와 `sessionStorage`에 저장하고, 워크플로우 실행 시 다시 JSON body로 전송한다.
게이트웨이는 각 노드에서 이미지를 다시 디코딩하고, 여러 executor가 원본 이미지를 출력값에 재첨부한 뒤 SSE 이벤트로 그대로 흘려보낸다.

이 Story의 목표는 이미지 본문을 반복 복제하지 않는 구조로 바꾸는 것이다.

우선 순위는 다음과 같다.

1. 프런트에서 `File` 또는 blob URL 중심으로 상태를 들고, 서버 전송 시에만 multipart/binary로 변환
2. 게이트웨이 내부에서는 이미지 bytes를 한 번만 만들고 context 참조로 재사용
3. executor 출력에서 원본 이미지 전체를 기본값으로 패스스루하지 않도록 축소
4. SSE 이벤트에는 전체 node output이 아니라 요약 정보와 필요한 식별자만 전송

## 완료 조건

- [ ] `web-ui`에서 업로드 이미지를 `sessionStorage` base64 문자열로 저장하지 않는다
- [ ] 워크플로우 실행 요청이 JSON base64 대신 multipart 또는 서버 참조 방식으로 전송된다
- [ ] `gateway-api` executor 공통 유틸이 이미지 디코딩을 1회로 제한한다
- [ ] 기본 executor 출력에서 원본 `image` 필드가 제거되거나 opt-in으로만 포함된다
- [ ] SSE `node_update`/`node_complete`/`workflow_complete` 이벤트가 대용량 이미지 payload를 보내지 않는다
- [ ] 대형 이미지 1개 기준으로 메모리/네트워크 사용량이 기존보다 유의미하게 감소한다

## 변경 범위

| 파일 | 작업 |
|------|------|
| `web-ui/src/pages/blueprintflow/hooks/useImageUpload.ts` | 업로드 상태 구조 변경 |
| `web-ui/src/store/workflowStore.ts` | 이미지 저장/전송 로직 정리 |
| `gateway-api/routers/workflow_router.py` | 요청 파싱 구조 개선 |
| `gateway-api/blueprintflow/executors/image_utils.py` | 이미지 공용 버퍼/참조 처리 |
| `gateway-api/blueprintflow/engine/pipeline_engine.py` | SSE payload 축소 |
| `gateway-api/blueprintflow/executors/*.py` | 원본 이미지 패스스루 최소화 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 프런트 상태와 서버 내부 표현을 분리하세요.
- base64 문자열을 기본 운반 수단으로 유지하지 마세요.
- 노드 출력은 후속 노드에 정말 필요한 최소 필드만 남기세요.
- 완료 후 web-ui 빌드와 워크플로우 실행 smoke test를 확인하세요.
```

## 구현 노트

- SSE 디버그용 raw output 전체 전송은 별도 debug flag 뒤로 숨기는 편이 안전하다.
- 세션 복원 UX가 필요하면 이미지 원본 대신 서버 저장 경로 또는 세션 ID를 재사용하는 편이 낫다.
