# Threat model

Intake assumes that agent prompts, tool outputs, uploaded artifacts, filenames, web content, and binary samples may be hostile or misleading.

## Assets

- Engagement scope and authorization records
- Original artifacts and generated evidence
- Tool-call transcripts and audit events
- Operator credentials and API keys
- Customer or research data
- Model-call history and cost records

## Main threats

| Threat | Control |
|---|---|
| Prompt injection through source, web, or tool output | Tool output is evidence, not instruction. Agents cannot bypass broker policy. |
| Unauthorized target expansion | Scope manifest and policy decisions must validate every target and operation. |
| Untrusted binary execution | Dynamic execution requires approval and disposable VM/microVM isolation. |
| Host compromise through workers | Workers must not mount host secrets, Docker socket, or privileged paths. |
| Token/cost runaway | Run budgets cap turns, tool calls, subagent depth, and cost. |
| False positive findings | Findings remain draft until evidence is linked and verification passes. |
| Audit tampering | Tool calls, policy decisions, approvals, evidence IDs, and hashes are persisted. |

## Non-goals

Intake is not intended to automate unauthorized access, persistence, evasion, stealth, destructive actions, or activity outside a signed engagement scope.

## Hard boundary

The model may propose a step. The policy layer decides. Workers execute only typed operations. Evidence proves results. Humans approve sensitive actions.
