# Intake

Intake is a policy-controlled security automation framework for authorized reverse engineering, evidence handling, and assessment workflows.

The project is intentionally built around this rule:

> The model proposes. Policy decides. Isolated workers execute. Evidence proves. A human authorizes sensitive actions.

## Current status

Expanded framework foundation. This repository now includes the core architecture skeleton for a safe security-automation platform: schema-validated tool calls, OPA policy checks, persistence, evidence storage, worker contracts, reverse-engineering wrappers, and workflow scaffolding.

It is not yet a production pentest system. Dynamic execution, active network assessment, and any state-changing operation are intentionally gated behind policy and review paths.

## Core design

- **Scope-first execution**: every target, artifact, and operation must belong to an engagement manifest.
- **Policy-gated tools**: tool calls pass through schema validation and OPA checks before execution.
- **No unrestricted shell path**: tools are typed contracts, not arbitrary command strings.
- **Isolated workers**: static analysis is designed for disposable containers; dynamic analysis should run in disposable VMs or microVMs.
- **Evidence integrity**: artifacts and outputs are stored by SHA-256 content address and referenced by immutable IDs.
- **Human approval gates**: dynamic execution, state-changing actions, and active network checks require approval.
- **LLM cost control**: budgets cap turns, tool calls, subagent depth, and cost.

## Repository layout

```text
src/intake/                  Python package
src/intake/models.py         SQLAlchemy persistence models
src/intake/storage.py        Content-addressed evidence store
src/intake/tool_broker.py    Policy-gated tool execution path
src/intake/scope.py          Engagement scope validation
src/intake/tools/            Typed tool wrappers
src/intake/workers/          Static/dynamic worker contracts
src/intake/orchestration/    Workflow state-machine skeleton
migrations/                  Alembic migrations
policies/                    OPA/Rego policy
examples/                    Example engagement manifest
docs/                        Architecture, operations, threat model, roadmap
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,orchestration]
docker compose up -d
alembic upgrade head
pytest
intake --help
```

## Intended build sequence

1. Finish database persistence services around the SQLAlchemy models.
2. Implement object-store evidence write/read flows in API endpoints.
3. Add OPA policy tests and CI.
4. Implement static worker backend for Ghidra/Rizin in disposable containers.
5. Add LangGraph nodes around the existing workflow state machine.
6. Add approval API and operator CLI commands.
7. Add dynamic-analysis VM backend only after isolation tests pass.

## Safety boundary

This project is for systems, binaries, applications, and networks that you own or are explicitly authorized to assess. It is not designed to bypass authorization, evade detection, establish persistence, perform destructive actions, or automate activity outside a signed engagement scope.
