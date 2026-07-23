# Intake 1.0.0

Intake 1.0.0 is the first stable release of the documented local-first product scope.

## Control plane

- role-aware API keys with viewer, operator, approver, and admin roles
- constant-time key verification
- trusted-host and optional CORS controls
- request IDs, structured access logging, request/upload limits, and security headers
- liveness, readiness, dependency health, and Prometheus metrics

## Execution plane

- durable PostgreSQL-backed execution jobs
- row-lock claiming, bounded retries, leases, cancellation, and worker ownership
- separate worker process and readiness-gated Compose startup
- synchronous HTTP execution disabled by default; authorized work is enqueued

## Evidence and review

- content-addressed storage
- race-safe, idempotent artifact ingestion
- evidence digest and size verification
- audit logging and finding lifecycle updates
- Markdown reporting

## Distribution trust

- non-root multi-stage container image
- dependency and static security scans
- high/critical container vulnerability gate
- container SBOM and provenance attestation
- Python distribution verification and provenance attestation

## Validated release gate

The release workflow requires linting, unit tests, API contracts, package building, dependency audit, static security analysis, container vulnerability scanning, clean database migrations, API readiness, durable worker execution, and evidence verification.

## Product boundary

Intake does not expose unrestricted shell execution, exploit automation, persistence, evasion, destructive actions, or unscoped active network execution.
