# Implementation plan

## Phase 1: Control plane

- FastAPI service
- Typer operator CLI
- PostgreSQL state
- OPA policy decision path
- MinIO/S3 evidence store
- Alembic migrations

## Phase 2: Static reverse engineering

- Artifact intake and hashing
- Ghidra headless worker
- Rizin scripted worker
- Function, string, import, symbol, and metadata extraction
- Evidence records for every output

## Phase 3: Workflow orchestration

- LangGraph-backed state machine
- Planner node
- Policy-review node
- Tool-dispatch node
- Evidence-review node
- Finding-verification node
- Report-render node

## Phase 4: Dynamic analysis

- Disposable VM or microVM worker backend
- No host secrets
- Deny-all network default
- Optional target allowlist
- Packet capture and process trace evidence
- Snapshot restore after every run

## Phase 5: Authorized assessment workflows

- Signed engagement manifests
- Target import and resolution lock
- Safe passive discovery
- Approval-gated active checks
- Verified finding workflow
- Report export

## Phase 6: Hardening

- Policy tests
- Prompt-injection tests
- Tool-output poisoning tests
- Scope-bypass tests
- Worker-isolation tests
- Cost-budget tests
- CI release gate
