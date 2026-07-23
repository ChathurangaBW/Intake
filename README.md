# Intake

Intake is a policy-controlled security automation app for authorized reverse engineering, evidence handling, and assessment workflows.

The project is built around this rule:

> The model proposes. Policy decides. Isolated workers execute. Evidence proves. A human authorizes sensitive actions.

## What works now

This is no longer only an architecture scaffold. The repository includes a runnable API and CLI with:

- FastAPI service
- Typer operator CLI
- PostgreSQL persistence through SQLAlchemy and Alembic
- OPA/Rego policy decisions
- MinIO/S3-compatible content-addressed evidence storage
- Engagements, targets, artifacts, tool calls, approvals, evidence, and findings
- Authorized tool-call execution path
- Safe local static-analysis worker for metadata and strings extraction
- Ghidra/Rizin tool contracts routed through the worker boundary
- Markdown report rendering
- Docker Compose development stack
- CI workflow and tests

## What is intentionally not included

Intake does **not** expose unrestricted shell execution, exploit automation, persistence, evasion, destructive actions, or unscopeable network activity. Dynamic execution and active network operations remain approval-gated design areas.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

The API starts on:

```text
http://127.0.0.1:8000
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

The API container runs Alembic migrations on startup.

## Local CLI setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,orchestration]
docker compose up -d postgres opa minio
alembic upgrade head
intake doctor
```

## Example workflow

Create an engagement:

```bash
intake engagement create eng-demo "Demo Authorized Assessment" --manifest examples/engagement.yaml
```

Add an authorized target:

```bash
intake target add eng-demo app.authorized-example.test domain
```

Ingest a local artifact:

```bash
intake artifact ingest eng-demo ./sample.bin
```

Propose a read-only static analysis tool call:

```bash
intake tool propose eng-demo analyst ghidra analyze read_only '{"artifact_id":"<artifact-id>","profile":"quick"}'
```

Execute it after the policy marks it `authorized`:

```bash
intake tool execute <tool-call-id>
```

Create a finding:

```bash
intake finding create eng-demo "Finding title" "Evidence-backed description" informational
```

Render a report:

```bash
intake finding report eng-demo --output report.md
```

## API workflow

Create an engagement:

```bash
curl -s http://127.0.0.1:8000/engagements \
  -H 'content-type: application/json' \
  -d '{"engagement_id":"eng-demo","name":"Demo Authorized Assessment"}'
```

Propose a tool call:

```bash
curl -s http://127.0.0.1:8000/tool-calls \
  -H 'content-type: application/json' \
  -d '{"engagement_id":"eng-demo","actor":"analyst","tool":"ghidra","operation":"analyze","risk":"read_only","arguments":{"artifact_id":"<artifact-id>","profile":"quick"}}'
```

Execute an authorized tool call:

```bash
curl -s -X POST http://127.0.0.1:8000/tool-calls/<tool-call-id>/execute
```

Render report:

```bash
curl -s http://127.0.0.1:8000/engagements/eng-demo/report.md
```

## Repository layout

```text
src/intake/                  Python package
src/intake/api.py            FastAPI app
src/intake/cli.py            Operator CLI
src/intake/services.py       Runtime application service layer
src/intake/models.py         SQLAlchemy persistence models
src/intake/storage.py        Content-addressed evidence store
src/intake/tool_runtime.py   Default constrained tool registry
src/intake/tool_broker.py    Policy-gated tool execution path
src/intake/scope.py          Engagement scope validation
src/intake/tools/            Typed tool wrappers
src/intake/workers/          Static/dynamic worker contracts and local static worker
src/intake/orchestration/    Workflow state-machine skeleton
migrations/                  Alembic migrations
policies/                    OPA/Rego policy
examples/                    Example engagement manifest
docs/                        Architecture, operations, threat model, roadmap
```

## Make targets

```bash
make install
make dev-up
make migrate
make api
make test
make lint
make check
```

## Safety boundary

This project is for systems, binaries, applications, and networks that you own or are explicitly authorized to assess. It is not designed to bypass authorization, evade detection, establish persistence, perform destructive actions, or automate activity outside a signed engagement scope.
