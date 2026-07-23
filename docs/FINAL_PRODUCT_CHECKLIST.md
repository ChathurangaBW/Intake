# Final product checklist

This checklist defines what Intake considers release-grade for the local-first product.

## Runtime

- [x] FastAPI app
- [x] Built-in dashboard
- [x] CLI
- [x] Python SDK
- [x] Durable worker entrypoint
- [x] Demo seeding workflow
- [x] Compose development profile
- [x] Compose production overlay

## Data and governance

- [x] Engagements
- [x] Targets
- [x] Artifacts
- [x] Tool calls
- [x] Approvals
- [x] Evidence
- [x] Findings
- [x] Audit logs
- [x] Jobs
- [x] Evidence integrity verification

## Distribution

- [x] Dockerfile
- [x] GHCR workflow
- [x] Python package metadata
- [x] Release workflow
- [x] Release manifest
- [x] Changelog
- [x] License

## Documentation

- [x] README landing page
- [x] Docs homepage
- [x] Demo guide
- [x] SDK guide
- [x] Operations guide
- [x] QA guide
- [x] Security boundary
- [x] Threat model
- [x] Packaging guide
- [x] Release guide

## QA and safety

- [x] Unit tests
- [x] API contract tests
- [x] Smoke script
- [x] Compose smoke target
- [x] Security scan target
- [x] Supply-chain workflow docs
- [x] No unrestricted shell runner
- [x] No exploit automation
- [x] No persistence/evasion workflows
- [x] No destructive or unscoped network workflow

## Non-goals for this release

- Multi-tenant SaaS
- Internet-exposed production hosting
- Autonomous active network testing
- High-risk malware detonation
- Offensive exploit execution
