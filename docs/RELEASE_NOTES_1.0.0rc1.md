# Intake 1.0.0rc1

This release candidate moves Intake from an alpha local application toward a release-quality operator platform.

## Major changes

- role-aware API authentication
- request IDs, structured access logs, security headers, CORS/trusted-host configuration, and body limits
- liveness, readiness, dependency checks, and Prometheus metrics
- durable database-backed execution jobs
- separate worker process with leases, retries, cancellation, and audit events
- evidence digest and size verification
- finding review lifecycle updates
- release-grade CLI commands for jobs and integrity checks
- non-root multi-stage container image
- Compose deployment with readiness-gated worker startup
- full-stack smoke workflow and stronger CI gates

The product safety boundary remains unchanged.
