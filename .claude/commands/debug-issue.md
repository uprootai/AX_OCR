---
description: Debug common issues following systematic workflow
---

> 새 조사 작업은 `/investigate`를 기본값으로 사용하세요. `/debug-issue`는 빠른 트리아지와 legacy workflow 호환용으로 유지합니다.

Please debug the issue using this systematic approach:

## 0. Debug Contract

Before running commands, define a narrow contract for the current failure.

```xml
<contract>
  <goal>Identify one root cause candidate for the current issue</goal>
  <scope>Only relevant services, logs, files, and failing paths</scope>
  <success_definition>Confirmed failure type + one next fix or probe</success_definition>
  <stop_conditions>
    <condition>Stop when two independent signals support the same diagnosis.</condition>
    <condition>Stop and report missing context instead of speculative debugging.</condition>
  </stop_conditions>
</contract>
```

Use a short private scratchpad before tool calls:

```xml
<think_tool visibility="private">
  <failure_symptom/>
  <unknowns/>
  <evidence_needed/>
  <tool_sequence/>
  <exit_test/>
</think_tool>
```

## 1. Check Logs
```bash
# Gateway API errors
docker logs gateway-api --tail 100 | grep ERROR

# Specific service errors
docker logs <service-name> --tail 50

# Look for exceptions
docker logs gateway-api | grep -A 10 "Exception in ASGI"
```

## 2. Common Issue Patterns

### "바운딩박스 값이 안나와요" (OCR values not showing)
1. Check if OCR is returning data:
   ```bash
   docker logs gateway-api | grep "eDOCr2 완료"
   # Should see: "eDOCr2 완료: N개 치수 추출"
   ```
2. If N=0, check data structure access in code
3. Verify matching logic is working

### API 500 Error
1. Look for Pydantic validation errors:
   ```bash
   docker logs gateway-api | grep "ResponseValidationError"
   ```
2. Check model definitions in models/response.py
3. Verify data types match API response

### Container Unhealthy
1. Check status: `docker ps | grep unhealthy`
2. Check health endpoint: `curl http://localhost:<port>/api/v1/health`
3. Restart: `docker-compose restart <service-name>`
4. If still failing, rebuild:
   ```bash
   docker-compose build <service-name>
   docker-compose up -d <service-name>
   ```

## 3. Reflector Before Retry

If the first probe fails, summarize before trying something else.

```xml
<reflector>
  <failure_type/>
  <confirmed_facts/>
  <discarded_hypotheses/>
  <root_cause_candidate/>
  <next_probe/>
</reflector>
```

Rules:
- do not continue branching once one diagnosis is clearly dominant
- do not keep appending raw logs to the conversation
- if logs are insufficient, switch to targeted file inspection instead of broader search

## 4. Curator for Escalation or Handoff

If the issue is not resolved quickly, leave a compact packet:

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

Use this packet before `/compact`, `/handoff`, or Codex cross-check.

## 5. Document in KNOWN_ISSUES.md
If this is a new issue, add it to KNOWN_ISSUES.md following the template
