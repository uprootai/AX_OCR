# S04: BlueprintFlow 재렌더 범위 축소

> **Epic**: 2026-03-09 성능 개선 계획
> **상태**: ⬜ Todo
> **예상**: 1d
> **의존**: S01 완료 권장

---

## 설명

`BlueprintFlowBuilder`가 Zustand store 전체에 구독되어 있고, 실행 중 heartbeat/update 이벤트마다 `nodeStatuses` 객체 전체가 새로 만들어진다.
이 때문에 노드 하나의 진행률이 바뀌어도 ReactFlow 캔버스와 패널이 넓게 재렌더될 가능성이 높다.

이 Story는 구독 범위를 잘게 나누고, 실행 중 자주 바뀌는 상태를 캔버스와 분리하는 작업이다.

핵심 작업은 다음과 같다.

1. `useWorkflowStore()` 전체 구독을 selector 기반 구독으로 교체
2. `nodeStatuses`는 노드별 selector 또는 파생 store로 분리
3. `BlueprintFlowBuilder`에서 캔버스에 필요한 상태와 실행 UI 상태를 분리
4. `NodeDetailPanel`도 선택된 노드 상태만 구독하도록 축소
5. 필요하면 ReactFlow 관련 prop/object 생성도 더 안정적으로 분리

## 완료 조건

- [ ] `BlueprintFlowBuilder`에서 전체 store 구독이 제거된다
- [ ] 실행 중 heartbeat 이벤트가 전체 캔버스 재렌더를 유발하지 않는다
- [ ] `NodeDetailPanel`은 선택된 노드 상태만 갱신될 때 재렌더된다
- [ ] 장시간 워크플로우 실행 시 UI 입력 지연이나 패널 버벅임이 줄어든다
- [ ] 관련 렌더링 회귀 테스트 또는 최소 확인 절차가 문서화된다

## 변경 범위

| 파일 | 작업 |
|------|------|
| `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx` | selector 기반 구독으로 분리 |
| `web-ui/src/store/workflowStore.ts` | node status 갱신 구조 개선 |
| `web-ui/src/components/blueprintflow/NodeDetailPanel.tsx` | 선택 노드 상태 구독 최소화 |
| `web-ui/src/pages/blueprintflow/components/*` | 실행 UI state 분리 필요 시 조정 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- store 전체 구독을 금지하고 selector 단위로 쪼개세요.
- 자주 바뀌는 실행 상태와 상대적으로 정적인 그래프 상태를 분리하세요.
- 변경 후 React DevTools 없이도 체감 가능한 수준으로 실행 중 UI가 덜 흔들리게 만드세요.
- 완료 후 web-ui 빌드와 수동 실행 확인을 하세요.
```

## 구현 노트

- 먼저 `useWorkflowStore()` 무선택 사용 지점을 전부 찾아 제거하는 것이 좋다.
- 상태 비교 최적화가 필요하면 shallow equality를 제한적으로 도입한다.
