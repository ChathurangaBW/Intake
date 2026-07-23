# Security boundary

Intake is an authorized security automation app. It is intentionally designed with product guardrails.

## Allowed default behaviors

- Engagement creation
- Target recording
- Artifact ingestion
- Policy decision recording
- Approval workflow
- Evidence storage
- Audit logging
- Safe static metadata and string extraction
- Optional fixed-argument static tool execution
- Markdown report generation

## Not exposed by default

- Unrestricted shell execution
- Exploit automation
- Persistence
- Evasion
- Destructive actions
- Unscoped active network operations
- Autonomous dynamic execution

## Why

A useful security automation framework should be auditable and scoped. The model may propose actions, but policy and human approval define what executes.
