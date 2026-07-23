# Intake

Intake is a policy-controlled security automation app for authorized reverse engineering, evidence handling, and assessment workflows.

The project is built around this rule:

> The model proposes. Policy decides. Isolated workers execute. Evidence proves. A human authorizes sensitive actions.

## Current app capability

Intake is now a runnable local application, not just an architecture scaffold. It includes:

- FastAPI service with OpenAPI docs
- Built-in web dashboard at `/ui`
- Optional API key authentication through `INTAKE_API_KEY`
- Typer operator CLI
- PostgreSQL persistence through SQLAlchemy and Alembic
- OPA/Rego policy decisions
- MinIO/S3-compatible content-addressed evidence storage
- Engagements, targets, artifacts, tool calls, approvals, audit logs, evidence, and findings
- API artifact upload and CLI artifact ingestion
- Tool catalog and tool availability endpoints
- Authorized tool-call execution path
- Safe local static-analysis worker for metadata and strings extraction
- Optional fixed-argument Ghidra/Rizin execution path when the operator enables external tools
- Markdown report rendering
- Docker Compose development stack
- CI workflow and tests

## Guardrails

Intake does not expose unrestricted shell execution. It exposes typed, scoped tool contracts. Dynamic execution and active network actions are policy-gated and not auto-run by the default runtime.

This is a deliberate product boundary, not an unfinished placeholder. The included app performs authorized intake, artifact handling, policy decisions, approval workflow, safe static analysis, evidence storage, audit logging, and reporting.

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

Web dashboard:

```text
http://127.0.0.1:8000/ui
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

## Recommended local security setting

Set an API key before exposing the service beyond localhost:

```bash
export INTAKE_API_KEY='change-this-long-random-value'
docker compose up --build
```

Then send API requests with:

```bash
-H 'X-Intake-Api-Key: change-this-long-random-value'
```

## Example CLI workflow

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

Check tool availability:

```bash
intake tool status
```

Propose a read-only static analysis tool call:

```bash
intake tool propose eng-demo analyst ghidra analyze read_only '{"artifact_id":"<artifact-id>","profile":"quick"}'
```

Execute it after the policy marks it `authorized`:

```bash
intake tool execute <tool-call-id>
```

List evidence:

```bash
intake evidence list eng-demo
```

Create a finding:

```bash
intake finding create eng-demo "Finding title" "Evidence-backed description" informational '["<evidence-id>"]'
```

Render a report:

```bash
intake finding report eng-demo --output report.md
```

Inspect audit logs:

```bash
intake audit list
```

## API workflow

Create an engagement:

```bash
curl -s http://127.0.0.1:8000/engagements \
  -H 'content-type: application/json' \
  -d '{"engagement_id":"eng-demo","name":"Demo Authorized Assessment"}'
```

Upload an artifact:

```bash
curl -s http://127.0.0.1:8000/engagements/eng-demo/artifacts \
  -F 'file=@./sample.bin;type=application/octet-stream'
```

List tool status:

```bash
curl -s http://127.0.0.1:8000/tools/status
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

Download evidence:

```bash
curl -s http://127.0.0.1:8000/evidence/<evidence-id>/download -o evidence.json
```

Render report:

```bash
curl -s http://127.0.0.1:8000/engagements/eng-demo/report.md
```

## Enabling real Ghidra/Rizin execution

By default, Intake uses its safe built-in metadata and string extraction worker. To use installed Ghidra/Rizin binaries, enable fixed-argument external static tools:

```bash
export INTAKE_ENABLE_EXTERNAL_STATIC_TOOLS=true
export INTAKE_RIZIN_PATH=rizin
export INTAKE_GHIDRA_ANALYZE_HEADLESS_PATH=analyzeHeadless
```

The external execution path uses fixed argument vectors, not arbitrary shell strings. If a binary is missing, Intake falls back to the built-in safe static worker.

## Repository layout

```text
src/intake/                  Python package
src/intake/api.py            FastAPI app
src/intake/auth.py           Optional API key auth
src/intake/web.py            Built-in HTML dashboard
src/intake/cli.py            Operator CLI
src/intake/services.py       Runtime application service layer
src/intake/models.py         SQLAlchemy persistence models
src/intake/storage.py        Content-addressed evidence store
src/intake/tool_runtime.py   Default constrained tool registry
src/intake/scope.py          Engagement scope validation
src/intake/tools/            Typed tool wrappers
src/intake/workers/          Static/dynamic worker contracts and static workers
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
