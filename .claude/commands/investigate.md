---
description: 근본 원인 중심 조사 명령. 증상 수집에서 root cause 검증까지 단계적으로 진행
---

# /investigate - root cause 중심 조사

`/debug-issue`의 빠른 트리아지 성격을 유지하되, 새 조사 작업은 이 명령을 기본값으로 사용합니다.
핵심은 로그를 많이 모으는 것이 아니라 지배적인 원인 후보 하나를 검증하는 것입니다.

## 목적

- 재현 가능한 실패 하나를 좁게 진단
- 증상 → 가설 → 검증 → 수정/다음 probe 순서를 강제
- 추측성 수정 없이 원인 후보를 수렴

## Investigation Contract

```xml
<contract>
  <goal>Confirm one dominant root cause candidate for the current failure</goal>
  <scope>Only the failing path, related services, and directly connected files</scope>
  <success_definition>Confirmed diagnosis + one fix or one next probe</success_definition>
  <stop_conditions>
    <condition>Stop when two independent signals support the same diagnosis.</condition>
    <condition>Stop and report missing context instead of speculative fixes.</condition>
  </stop_conditions>
</contract>
```

## 단계

### 1. 증상 고정

정확히 하나의 실패를 문장으로 고정합니다.

```xml
<symptom>
  <what_failed/>
  <where_it_failed/>
  <expected/>
  <actual/>
</symptom>
```

### 2. 재현과 증거 수집

필요한 명령만 좁게 실행합니다.

```bash
git status --short
docker ps
docker logs <service> --tail 100
rg -n "<error text or endpoint>" gateway-api blueprint-ai-bom web-ui
```

서비스별 probe 예시:

```bash
curl -s http://localhost:5050/api/v1/health
curl -s http://localhost:5020/health
cd web-ui && npx playwright test e2e/dual-ui-smoke.spec.ts --grep "<scenario>"
```

### 3. 가설 수립

가설은 최대 2개까지만 유지합니다.

```xml
<hypotheses>
  <hypothesis rank="1"/>
  <hypothesis rank="2"/>
</hypotheses>
```

### 4. strongest hypothesis 검증

가설 1개를 뒤집을 수 있는 probe를 먼저 수행합니다.

예시:
- 라우팅 문제면 직접 URL/redirect 확인
- API shape 문제면 schema와 response payload 비교
- OCR/BOM 문제면 bbox, parser output, session payload 비교

### 5. Reflector / Curator

```xml
<reflector>
  <failure_type/>
  <confirmed_facts/>
  <discarded_hypotheses/>
  <root_cause_candidate/>
  <next_probe/>
</reflector>
```

문제가 길어지면:

```xml
<curator>
  <task_state/>
  <relevant_services/>
  <relevant_files/>
  <confirmed_facts/>
  <open_risks/>
  <next_action/>
</curator>
```

## 역할 분담

- `/investigate`: 새 조사 작업의 기본 명령, root cause 검증 중심
- `/debug-issue`: 빠른 트리아지, legacy shortcut 성격 유지
- `/handoff`: 조사 상태를 다음 세션으로 넘길 때 사용

## 관련 문서

- `.claude/commands/debug-issue.md`
- `.claude/commands/handoff.md`
- `.claude/commands/verify.md`
