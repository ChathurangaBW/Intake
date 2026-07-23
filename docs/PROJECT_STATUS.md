# Project status

Intake is at `1.0.0`, the first stable release of its documented local-first, single-tenant product scope.

## Supported production scope

- Local or isolated single-tenant deployments
- Authorized engagement and target management
- Artifact intake with idempotent content-addressed storage
- OPA-backed policy decisions and approval workflow
- Durable read-only static-analysis jobs
- Evidence storage, integrity verification, audit logging, findings, and reports
- API, CLI, and built-in operator dashboard
- PostgreSQL, OPA, MinIO, API, and worker deployment through Docker Compose

## Deployment requirements

- Configure role-aware API keys before non-local access
- Use dedicated credentials rather than example Compose credentials
- Keep external static tools inside an isolated worker environment
- Retain default-deny network and execution policies
- Review the threat model and security boundary before adding tools

## Outside the supported 1.0 scope

- Multi-tenant identity federation
- Public internet exposure without an authenticated reverse proxy and additional hardening
- High-risk malware detonation
- Autonomous active network testing
- Unrestricted command execution
- Exploit, evasion, persistence, or destructive workflows

## Release validation

The 1.0 gate covers linting, unit and API contract tests, package build, dependency audit, static security analysis, container vulnerability scanning, clean migrations, readiness, durable worker execution, and evidence verification.
