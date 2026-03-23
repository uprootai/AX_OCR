# S04: AX 핵심 흐름 QA 시나리오 팩 재편

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 2.5d

---

## 설명

브라우저 실행 기반만으로는 부족하다.
실제 사용자 가치와 연결되는 핵심 흐름을 시나리오 팩으로 묶어야 `gstack`식 브라우저 검증이 살아난다.
다만 AX 저장소는 이미 `web-ui/e2e/plan`과 다수의 Playwright spec을 갖고 있으므로, 이 Story는 새 시나리오를 무한히 늘리는 대신 기존 자산을 `BOM 견적 워크플로우`와 `Dimension Lab/overlay` 중심으로 재편하는 작업이어야 한다.

우선 시나리오는 아래 흐름을 포함한다.

1. 프로젝트 진입 + 주요 카드 렌더링 확인
2. BOM 업로드 또는 BOM 워크플로우 진입
3. 도면 매칭 테이블 확인
4. 세션 생성/검토 큐 또는 결과 검토 화면 확인
5. Dimension Lab 또는 overlay 렌더링 확인
6. `web-ui`에서 `/bom/*` 리다이렉트 후 `blueprint-ai-bom/frontend` 동작 확인

각 시나리오는 선택자 전략, 필요 fixture, 기대 결과, 실패 시 캡처 규칙을 함께 가져야 한다.

## 완료 조건

- [x] 핵심 사용자 흐름 기준 시나리오 그룹이 최소 5개 정의된다.
- [x] 각 시나리오에 필요한 fixture 또는 mock 전략이 `web-ui/e2e/fixtures`와 연결된다.
- [x] 실패 시 trace/screenshot 수집 규칙이 포함된다.
- [x] flaky 포인트와 재시도 정책이 문서화된다.
- [x] 기존 `web-ui/e2e/plan` 문서와 중복되는 시나리오는 통합 또는 정리된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `web-ui/e2e/` | 신규 또는 확장 |
| `web-ui/e2e/plan/` | 재편 |
| `blueprint-ai-bom/frontend/e2e/` | 신규 검토 |
| `web-ui/src/pages/project/components/BOMWorkflowSection.tsx` | 선택자 보강 검토 |
| `web-ui/src/pages/project/components/DrawingMatchTable.tsx` | 선택자 보강 검토 |
| `web-ui/src/utils/svgOverlay.ts` | 시각 검증 기준 정리 검토 |
| `blueprint-ai-bom/frontend/src/pages/dimension-lab/` | 브라우저 진입점 검토 |
| `.todo/epics/e08-gstack-max-adoption/` | 시나리오 문서 추가 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: AX의 실제 업무 흐름을 재현하는 브라우저 QA 시나리오 팩 확보
- 기준 화면: 프로젝트 페이지, BOM 워크플로우, 도면 매칭, 검증/세션, 치수/overlay
- 필수 재사용: web-ui/e2e/fixtures/api-fixtures.ts, 기존 e2e/plan 문서, blueprint-ai-bom.spec.ts 계열
- 주의: 단순 페이지 오픈 테스트로 끝내지 말고, 사용자가 무엇을 보고 성공이라 판단하는지까지 포함
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- 시나리오 설계 시 `bbox`, `overlay`, `검토 큐`처럼 AX 고유 UI 신호를 반드시 포함한다.
- 선택자가 불안정하면 UI 컴포넌트에 `data-testid`를 추가하는 작업이 동반될 수 있다.
- `BOMWorkflowSection`과 `DrawingMatchTable`은 이미 시나리오 중심 UI라 첫 번째 test-id 보강 후보로 본다.
- `web-ui/e2e/plan/09-ax-scenario-pack.md`를 AX 핵심 흐름용 source of truth로 추가했다.
- 핵심 그룹은 `AX-SMOKE`, `AX-BOM-PROJECT`, `AX-WORKFLOW`, `AX-DIMENSION`, `AX-OVERLAY` 5개로 재편했다.
- `web-ui/src/pages/project/components/BOMWorkflowSection.tsx`, `DrawingMatchTable.tsx`에 최소 `data-testid`를 보강했다.
- trace/screenshot/video 규칙은 S02에서 정한 `.gstack/reports/playwright/` 경로를 그대로 따른다.
