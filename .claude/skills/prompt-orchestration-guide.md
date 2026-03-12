---
name: prompt-orchestration-guide
description: XML contract, early-stop criteria, private think scratchpad, and reflector-curator context purification patterns for Claude Code and Codex collaboration
user-invocable: true
allowed-tools: [read, grep]
---

# Prompt Orchestration Guide

**Purpose**: Control Claude Code and Codex with compact contracts instead of verbose prompting.

Use this skill when the task involves any of the following:
- prompt tuning for Claude Code skills or commands
- Codex cross-check or second-opinion prompts
- reducing reasoning cost or latency
- tool-calling accuracy problems
- context decay, repeated failures, or long-session cleanup

## Core Rules

1. Prefer `goal + scope + stop conditions + output schema` over polite or verbose wording.
2. Default to `low` reasoning effort. Raise effort only for architecture choices, ambiguous bugs, or risky edits.
3. Add explicit early-stop criteria so the model stops searching once the decision is stable.
4. Keep the think space private and short. It is a checklist, not a long diary.
5. After a failure, do not drag the full conversation forward. Purify context into a small handoff packet.

## 1. XML Contract Pattern

Use XML to constrain behavior before any tool call or code generation.

Minimum contract:

```xml
<contract>
  <goal/>
  <scope/>
  <success_definition/>
  <forbidden_actions/>
  <tool_policy/>
  <stop_conditions/>
  <output_schema/>
</contract>
```

Field intent:
- `goal`: single task to finish now
- `scope`: allowed files, systems, or questions
- `success_definition`: what must be true to stop
- `forbidden_actions`: no scope creep, no invented APIs, no hidden failure masking
- `tool_policy`: what to read first, what to avoid, when to verify
- `stop_conditions`: enough evidence, safe plan selected, or missing critical input
- `output_schema`: short predictable output

## 2. Reasoning Control

Treat reasoning as a budgeted resource.

Suggested policy:
- `low`: file lookup, API spec checks, narrow edits, verification summaries
- `medium`: comparing two implementation options, debugging with partial signals
- `high`: rare; only for architectural tradeoffs or cross-service incident analysis

Early-stop examples:
- stop after two independent signals support the same diagnosis
- stop after one safe implementation path clearly dominates
- stop and report missing context instead of continuing speculative search
- stop additional doc lookup when it is unlikely to change the recommendation

Avoid:
- "think step by step" without a stopping rule
- open-ended brainstorming in long turns
- forcing detailed reasoning output for simple tasks

## 3. Private Think Scratchpad

Use a short private scratchpad before tool calls.

Recommended schema:

```xml
<think_tool visibility="private">
  <task_class/>
  <unknowns/>
  <evidence_needed/>
  <tool_sequence/>
  <risk_checks/>
  <exit_test/>
</think_tool>
```

Guidelines:
- one line per field
- fill only the fields needed for the current task
- never let the scratchpad become the final answer
- if `unknowns` block safe execution, stop and ask for the missing fact

## 4. Reflector and Curator

When the agent fails, split recovery into two roles.

`Reflector`:
- classify the failure
- keep only confirmed facts
- list discarded hypotheses
- propose one next probe

`Curator`:
- compress the state for the next turn
- keep task, touched files, decisions, risks, and next action
- remove stale brainstorming, duplicated logs, and abandoned plans

Recommended failure packet:

```xml
<failure_protocol>
  <reflector>
    <failure_type/>
    <confirmed_facts/>
    <discarded_hypotheses/>
    <root_cause_candidate/>
    <next_probe/>
  </reflector>
  <curator>
    <task_state/>
    <relevant_files/>
    <decisions/>
    <open_risks/>
    <next_action/>
  </curator>
</failure_protocol>
```

## 5. Claude Code Pattern

For Claude Code, keep the contract in the skill or command prompt and keep outputs short.

Workflow:
1. Load only the relevant project rule or skill.
2. Fill the private think scratchpad.
3. Read the minimum source-of-truth files.
4. Stop early once the plan is stable.
5. If the task fails or the session grows, emit a purified packet for `/compact` or `/handoff`.

Template:
- [claude-skill-system-prompt.xml](../templates/claude-skill-system-prompt.xml)

## 6. Codex Cross-Check Pattern

Use Codex as a single-turn verifier, not as a long-running co-author in the same context.

Pass only:
- task
- current hypothesis
- constraints
- relevant files or diff summary
- specific decision to validate

Ask Codex to return:
- best recommendation
- confidence
- top counter-risk
- next action
- whether more context is required

Template:
- [codex-cross-check-system-prompt.xml](../templates/codex-cross-check-system-prompt.xml)

## 7. AX POC Integration Notes

Map this guide onto the existing project structure:
- root policy: `/home/uproot/ax/poc/CLAUDE.md`
- context rules: `/home/uproot/ax/poc/.claude/skills/context-engineering-guide.md`
- long-session reset: `/home/uproot/ax/poc/.claude/commands/handoff.md`
- compact preservation hook: `/home/uproot/ax/poc/.claude/hooks/pre-compact.sh`

Recommended triggers:
- "prompt", "system prompt", "XML contract"
- "Codex cross-check", "second opinion"
- "context decay", "context rot", "handoff"
- "reasoning cost", "latency", "stop early"
