---
description: 변경 범위 중심의 읽기 전용 코드 리뷰. 버그, 리스크, 회귀 가능성을 우선 식별
---

# /review - 변경 범위 중심 코드 리뷰

읽기 전용 리뷰 명령입니다. 구현을 고치기 전에 현재 diff와 인접 코드 경로를 검토해 버그, 보안 리스크, 회귀 가능성, 빠진 테스트를 먼저 식별합니다.

## 목적

- PR 전 고위험 이슈를 조기에 찾기
- `/verify` 전에 무엇을 검증해야 하는지 좁히기
- 큰 diff에서 놓치기 쉬운 call path를 다시 점검하기

## Review Contract

```xml
<contract>
  <goal>Identify the highest-signal review findings in the current change set</goal>
  <scope>Changed files and directly connected call paths only</scope>
  <success_definition>Findings ordered by severity, or an explicit no-findings verdict with residual risks</success_definition>
  <stop_conditions>
    <condition>Stop broadening scope once the dominant risks are covered.</condition>
    <condition>Do not rewrite code or run unrelated full-suite checks.</condition>
  </stop_conditions>
</contract>
```

## 기본 절차

### 1. 변경 범위 고정

```bash
git status --short
git diff --name-only HEAD
git diff --stat HEAD
```

질문:
- 이번 변경이 `web-ui`, `gateway-api`, `blueprint-ai-bom`, `models` 중 어디를 건드렸는가?
- API contract, 브라우저 경로, OCR/BOM data shape, Docker runtime 중 무엇이 깨질 수 있는가?

### 2. 증거 중심 검토

필요한 경우에만 좁게 검증합니다.

**TypeScript/React**
```bash
cd web-ui && npx tsc --noEmit
cd web-ui && npm run lint
cd blueprint-ai-bom/frontend && npx tsc --noEmit
```

**Python/FastAPI**
```bash
python3 -c "import ast; ast.parse(open('gateway-api/<file>').read())"
python3 -c "import ast; ast.parse(open('blueprint-ai-bom/backend/<file>').read())"
cd gateway-api && pytest <targeted test>
cd blueprint-ai-bom/backend && pytest <targeted test>
```

**API/contract**
```bash
rg -n "<field-or-param>" gateway-api/api_specs web-ui/src blueprint-ai-bom
```

필수 확인:
- `api_specs/*.yaml`과 실제 프론트 파라미터 동기화
- `confidence_threshold` 기본값 0.4 위반 여부
- base64 이미지 전송, console.log/print, 하드코딩 시크릿
- `/bom/*` 라우팅, Playwright 포트, `.gstack` 아티팩트 경로

### 3. 보고 형식

응답 순서는 반드시 다음을 따릅니다.

1. Findings
2. Open questions or assumptions
3. Residual risk / missing verification

출력 예시:

```markdown
## Findings
1. High — web-ui/src/App.tsx:38
   /bom redirect가 dev 포트 5174를 처리하지 못해 Playwright smoke가 실패합니다.

2. Medium — gateway-api/routers/...
   api_specs에는 없는 파라미터를 프론트가 전송하고 있습니다.

## Assumptions
- 사용자가 5020 백엔드를 로컬에서 띄운 상태라고 가정했습니다.

## Residual Risk
- targeted test는 확인했지만 full smoke는 아직 실행하지 않았습니다.
```

## 역할 분담

- `/review`: 읽기 전용, 위험 식별, 우선순위화
- `/verify`: 변경 후 최소 검증 실행
- `/codex-cross-check`: 여전히 판단이 팽팽할 때 단일 턴 2차 검증

새로운 구현 리뷰는 `/review`를 우선하고, 실행 검증은 그다음 `/verify`로 넘깁니다.

## 연결 에이전트

- `.claude/agents/code-reviewer.md`

## 관련 문서

- `.claude/commands/verify.md`
- `.claude/commands/codex-cross-check.md`
- `AGENTS.md`
