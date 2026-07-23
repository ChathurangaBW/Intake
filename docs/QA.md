# Intake QA Plan

This document defines the minimum QA gate for Intake releases.

## QA layers

| Layer | Purpose | Command |
|---|---|---|
| Static lint | Catch style and obvious code issues | `ruff check .` |
| Unit tests | Validate pure functions and narrow components | `pytest -m unit` |
| API contract tests | Validate route shape, auth, and error mapping with mocked services | `pytest -m contract` |
| Integration smoke | Validate Docker runtime, migrations, API health, and core workflow | `make smoke` |
| Manual acceptance | Verify UI, approvals, evidence download, and report rendering | checklist below |

## Release gate

A release is not considered QA-passed until:

- `make check` passes locally or in CI.
- `make smoke` passes against the Compose stack.
- `/health` returns `status=ok`.
- `/ui` loads when web UI is enabled.
- `/docs` loads.
- An engagement can be created.
- An artifact can be uploaded or ingested.
- A read-only tool call can be proposed.
- An authorized tool call can be executed.
- Evidence is stored and downloadable.
- A finding can be created.
- A Markdown report can be rendered.
- Audit log contains entries for the above workflow.
- API key auth blocks protected endpoints when `INTAKE_API_KEY` is set.

## Manual smoke workflow

```bash
cp .env.example .env
docker compose up --build
```

In another terminal:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ui >/dev/null
curl -fsS http://127.0.0.1:8000/docs >/dev/null

curl -fsS http://127.0.0.1:8000/engagements \
  -H 'content-type: application/json' \
  -d '{"engagement_id":"qa-smoke","name":"QA Smoke"}'

printf 'hello qa sample' > /tmp/intake-qa-sample.bin
curl -fsS http://127.0.0.1:8000/engagements/qa-smoke/artifacts \
  -F 'file=@/tmp/intake-qa-sample.bin;type=application/octet-stream'

curl -fsS http://127.0.0.1:8000/stats
curl -fsS http://127.0.0.1:8000/audit
```

## Non-goals

QA must not require real exploit traffic, destructive testing, persistence, evasion, or unrestricted command execution. Reverse-engineering worker tests should use harmless local fixtures or mocked fixed-argument executors.
