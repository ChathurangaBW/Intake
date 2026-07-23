# Changelog

All notable changes to Intake will be documented in this file.

## 1.0.0 - Stable local-first release

### Added

- Role-aware API authentication and authenticated actor attribution
- Request IDs, structured access logs, trusted hosts, CORS controls, security headers, and request limits
- Liveness, readiness, dependency health, and Prometheus metrics
- Durable execution jobs with leases, retries, cancellation, and worker ownership
- Separate execution worker service
- Evidence integrity verification
- Idempotent, race-safe artifact ingestion
- Finding review and verification lifecycle updates
- Non-root multi-stage container packaging
- Container vulnerability scanning, SBOM generation, and provenance attestations
- Python distribution verification and provenance attestations
- Operations control-plane API and CLI for readiness diagnostics, metadata exports, audit NDJSON, and evidence inventory verification

### Changed

- HTTP tool execution now uses the durable enqueue/worker path by default
- Package and API versioning now share one version source
- Release gates now include clean migrations, readiness, worker execution, and evidence verification
- Operator handoff now includes deterministic engagement export and audit export paths

### Security boundary

- No unrestricted shell runner
- No exploit automation
- No evasion or persistence workflows
- No destructive actions
- No unscoped network operations

## 0.1.0 - Initial app release

### Added

- FastAPI runtime with OpenAPI docs
- Built-in local web dashboard
- Optional API-key authentication
- Typer CLI
- PostgreSQL persistence with Alembic migrations
- OPA policy decision path
- MinIO/S3-compatible evidence storage
- Engagement, target, artifact, tool-call, approval, evidence, finding, and audit models
- Safe local static-analysis worker
- Optional fixed-argument Ghidra/Rizin static-analysis execution path
- Markdown report rendering
- Docker Compose development stack
- CI workflow, QA markers, API contract tests, and smoke workflow
- Branded README, logo assets, documentation homepage, package workflow, and release workflow
