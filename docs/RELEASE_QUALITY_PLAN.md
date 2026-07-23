# Release-quality product pass

This document defines the engineering gate for Intake 1.0 release candidates.

## Product blockers addressed in this pass

- role-aware API authentication with constant-time key comparison
- request IDs, structured access logs, security headers, and upload limits
- liveness and dependency-aware readiness probes
- durable database-backed execution jobs and a separate worker process
- evidence integrity verification
- artifact deduplication
- finding lifecycle updates
- pagination limits on high-cardinality APIs
- Prometheus-compatible metrics
- Compose smoke testing and security-oriented CI checks

## Release gate

A release candidate is acceptable only when:

1. unit and API contract tests pass,
2. migrations apply from a clean database,
3. the Compose stack reaches readiness,
4. the HTTP smoke workflow completes,
5. the worker claims and completes an authorized read-only job,
6. evidence verification returns a matching digest and size,
7. unauthenticated and under-privileged requests are rejected,
8. the container image builds successfully.

The product guardrail remains unchanged: no unrestricted shell runner, exploit automation, persistence, evasion, destructive workflow, or unscoped active network execution.
