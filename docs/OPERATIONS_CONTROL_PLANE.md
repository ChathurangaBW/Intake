# Operations control plane

The operations control plane adds runtime-facing diagnostics and export surfaces for operators.

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /ops/readiness` | Database-backed readiness report with record counts, failed job status, and pending approval checks |
| `GET /ops/engagements/{engagement_id}/export` | Engagement metadata export bundle without raw evidence bytes |
| `GET /ops/audit/export.ndjson` | Canonical NDJSON export of recent audit events |
| `GET /ops/evidence/verify` | Re-read recent evidence objects and verify digest/size metadata |

## CLI commands

```bash
intake ops readiness
intake ops export-engagement eng-demo --output eng-demo-export.json
intake ops export-audit --output intake-audit.ndjson --limit 1000
intake ops verify-evidence --limit 500
```

## Export model

Engagement exports contain:

- export manifest
- engagement metadata
- targets
- artifact metadata
- tool calls
- execution jobs
- policy decisions
- approvals
- evidence metadata
- findings
- finding-evidence links
- model-call cost records

Raw evidence bytes are intentionally not embedded in the export bundle. Evidence remains content-addressed in the configured object store and can be retrieved through dedicated evidence download endpoints.

## Integrity behavior

The export bundle includes a deterministic SHA-256 over the exported `data` payload. This is not a cryptographic signature, but it gives operators a stable tamper-evidence checksum for exported metadata.

The evidence verification command/API re-reads stored evidence objects and checks:

- expected SHA-256 vs actual SHA-256
- expected byte size vs actual byte size
- retrievability from the configured object store

## Operational usage

Use these checks before handoff:

```bash
make check
intake ops readiness
intake ops verify-evidence
intake ops export-audit --output handoff-audit.ndjson
intake ops export-engagement <engagement-id> --output handoff-engagement.json
```

## Boundary

The control plane is read-only except for normal audit records produced by existing service operations. It does not introduce shell execution, active network checks, dynamic execution, destructive actions, or scope expansion.
