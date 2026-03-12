---
description: Prepare a compact single-turn Codex cross-check packet for risky decisions, repeated failures, or unresolved implementation tradeoffs
---

Please prepare a Codex cross-check packet using this workflow:

## 1. When to Use

Use this command only when one of these is true:
- High or Critical risk change
- `/verify` or `/debug-issue` failed repeatedly
- Two implementation options remain viable after local inspection
- A second opinion is needed before a risky edit or merge

Do not use it for broad brainstorming or open-ended research.

## 2. Build a Narrow Contract

First define a small decision surface:

```xml
<contract>
  <goal>Get one clear recommendation from Codex</goal>
  <scope>Current task, decision, and directly relevant files only</scope>
  <success_definition>Decision + confidence + top counter-risk + next action</success_definition>
  <stop_conditions>
    <condition>Stop adding context once the decision can be evaluated safely.</condition>
    <condition>Do not include raw logs or unrelated conversation history.</condition>
  </stop_conditions>
</contract>
```

## 3. Create the Codex Packet

Use this system template:
- `/home/uproot/ax/poc/.claude/templates/codex-cross-check-system-prompt.xml`

Prepare only the following payload:

```xml
<context_packet>
  <task></task>
  <decision_request></decision_request>
  <constraints></constraints>
  <relevant_files></relevant_files>
  <current_hypothesis></current_hypothesis>
  <diff_summary></diff_summary>
</context_packet>
```

Rules:
- compress to stable facts only
- include only files that affect the current decision
- summarize logs into findings, never paste long raw output
- if context is insufficient, say so explicitly instead of padding

## 4. Output Format

Return a handoff-ready packet in this form:

````markdown
## Codex Cross-Check

### Why Codex
- [one sentence]

### System Prompt
- /home/uproot/ax/poc/.claude/templates/codex-cross-check-system-prompt.xml

### User Payload
```xml
<context_packet>
  ...
</context_packet>
```

### Expected Answer
- decision
- confidence
- why
- counter_risk
- next_action
- need_more_context
````

## 5. Curator Before Send

Before finalizing the packet, compress the local state:

```xml
<curator>
  <task_state/>
  <relevant_files/>
  <confirmed_facts/>
  <open_risks/>
  <next_action/>
</curator>
```

If the packet exceeds what is needed for the decision, shrink it again.
