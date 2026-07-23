# Intake application capabilities

This document defines what the completed safe app runtime provides.

## Product surface

Intake provides three operator surfaces:

1. FastAPI JSON API
2. Built-in HTML dashboard
3. Typer CLI

The API and CLI expose the same core workflow: create an engagement, add scope, ingest artifacts, propose typed tool calls, execute authorized tool calls, record evidence, create findings, render reports, and inspect audit events.

## Completed safe runtime features

- Engagement lifecycle
- Authorized target management
- Artifact upload and content-addressed storage
- Evidence creation, listing, and download
- Typed tool-call proposal
- OPA policy decision recording
- Approval and rejection workflow
- Authorized tool-call execution
- Built-in safe static worker for metadata and strings extraction
- Optional fixed-argument Rizin worker
- Optional fixed-argument Ghidra headless worker
- Finding creation and evidence linkage
- Markdown report generation
- Persistent audit log
- Dashboard statistics
- Web dashboard
- Optional API-key protection
- Docker Compose runtime
- Alembic migration startup

## Security boundary

The app does not include an unrestricted shell endpoint. That is intentional. The runtime only executes typed tool contracts after policy authorization.

External Ghidra/Rizin execution uses fixed argument vectors. The app never accepts an arbitrary shell command string from an operator or model.

## Reverse-engineering workflow now supported

1. Upload artifact.
2. Propose `ghidra.analyze` or `rizin.analyze` as a read-only tool call.
3. OPA authorizes the read-only analysis.
4. Execute the tool call.
5. The static worker writes analysis output as evidence.
6. Create findings linked to evidence.
7. Render a report.

If real Ghidra/Rizin binaries are not installed or external static tools are disabled, the runtime falls back to the built-in metadata and string extraction worker.

## Dynamic and active network operations

Dynamic execution and active network testing remain policy-gated extension points. They are not auto-run by the default runtime because they require deployment-specific isolation, target allowlists, and human approval.

That is a safety and authorization boundary, not a missing basic app feature.
