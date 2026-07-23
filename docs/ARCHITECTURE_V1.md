# Intake 1.0 architecture

```text
Operator CLI / Web API
        |
Role-aware authentication and request middleware
        |
Engagement scope + OPA policy decision
        |
Authorized tool call
        |
Durable execution job
        |
Database-leased worker process
        |
Constrained static-analysis tool adapter
        |
Content-addressed evidence storage
        |
Integrity verification + audit + findings + report
```

## Control plane

The FastAPI service owns authenticated operator requests, scope records, policy decisions, approvals, job creation, evidence metadata, audit history, and reporting.

## Execution plane

Workers claim jobs with PostgreSQL row locking and time-limited leases. Failed jobs retry up to a bounded maximum. Queued jobs can be cancelled immediately; running jobs use cooperative cancellation at the completion boundary.

## Evidence plane

Artifacts and tool outputs are stored by SHA-256 digest. Integrity verification re-reads the object and validates both digest and size against database metadata.

## Safety boundary

Execution remains typed and constrained. No generic shell endpoint, exploit automation, evasion, persistence, destructive action, or unscoped active network operation is introduced by the release-candidate architecture.
