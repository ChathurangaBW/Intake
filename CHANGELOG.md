# Changelog

All notable changes to Intake will be documented in this file.

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

### Security boundary

- No unrestricted shell runner
- No exploit automation
- No evasion or persistence workflows
- No destructive actions
- No unscoped network operations
