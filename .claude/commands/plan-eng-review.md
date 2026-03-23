---
description: 구현 전 엔지니어링 리뷰. 범위, 영향 경로, 테스트 매트릭스, rollout 위험을 검토
---

# /plan-eng-review - 구현 전 엔지니어링 리뷰

`/plan-epic`이 BMAD-Lite Story 분해라면, `/plan-eng-review`는 지금 제안한 구현 방향이 실제 저장소에 맞는가를 검토하는 명령입니다.

## 목적

- 구현 전에 과도한 스코프와 경로 누락을 줄이기
- API contract, touched services, 테스트 범위를 미리 드러내기
- 아키텍처 변경이 실제 AX 저장소 표면과 맞는지 확인하기

## Review Contract

```xml
<contract>
  <goal>Evaluate whether the proposed implementation plan is technically coherent for AX</goal>
  <scope>Plan, touched files, affected services, tests, rollout only</scope>
  <success_definition>Decision + key risks + required changes to the plan</success_definition>
  <stop_conditions>
    <condition>Stop once the plan is clearly viable or clearly needs rework.</condition>
    <condition>Do not start implementation from this command.</condition>
  </stop_conditions>
</contract>
```

## 산출물

반드시 아래 6개를 포함합니다.

### 1. Plan Verdict

- `approve`
- `approve_with_changes`
- `rework_required`

### 2. Touched Surface

| 영역 | 예상 경로 | 위험 |
|------|-----------|------|
| web-ui | `web-ui/src/...` | 라우팅 / Playwright |
| gateway-api | `gateway-api/...` | api_specs / response shape |
| blueprint-ai-bom | `blueprint-ai-bom/...` | BOM workflow / 5020 contract |

### 3. Contract Check

필수 확인:
- `gateway-api/api_specs/*.yaml`
- `web-ui/src/config/*`, `nodeDefinitions.ts`
- `blueprint-ai-bom/frontend` / `backend` 간 실제 포트와 URL
- multipart 업로드 규칙, confidence 기본값 0.4

### 4. ASCII Coverage Diagram

Mermaid 대신 ASCII로 남깁니다.

```text
[web-ui route]
   -> [gateway-api]
   -> [model service]
   -> [result UI]
```

### 5. Test Matrix

예시:

| 변경 유형 | 필수 검증 |
|-----------|-----------|
| web-ui route/env | `cd web-ui && npx tsc --noEmit`, Playwright smoke |
| gateway-api schema | targeted pytest, syntax parse |
| dual-ui flow | `npm run test:e2e:dual-ui` |

### 6. Open Questions / Rollout Risk

- 어떤 포트/환경 변수가 source of truth인가?
- 변경이 Docker와 dev 모드에서 모두 동일하게 동작하는가?
- 실패 시 rollback이 파일/설정 수준에서 가능한가?

## 역할 분담

- `/plan-epic`: Epic/Story 구조화
- `/plan-eng-review`: 구현 방향의 기술 타당성 점검
- `/review`: 구현 후 코드/리스크 검토

## 관련 문서

- `.claude/commands/plan-epic.md`
- `AGENTS.md`
- `.todo/epics/`
- `web-ui/e2e/plan/README.md`
