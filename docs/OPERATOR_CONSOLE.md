# Operator console

Intake includes a self-contained browser console at `/ui`.

The console is designed for local and controlled operator workflows. It is not a separate frontend build; it ships with the FastAPI app and calls the same API surface documented at `/docs`.

## Open the console

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8000/ui
```

If `INTAKE_API_KEY` or `INTAKE_API_KEYS` is configured, enter the key in the console header and click **Save key**. The key is stored only in browser local storage.

## Console sections

| Section | Purpose |
|---|---|
| Overview | Stats, recent engagements, readiness summary |
| Engagements | Create engagements and add scoped targets |
| Artifacts | Upload files and inspect artifact inventory |
| Tools & jobs | Propose scoped tool calls and execute authorized calls |
| Approvals | Review pending approvals and approve or reject them |
| Findings | Create findings and inspect review state |
| Evidence | Store text evidence and download existing records |
| Ops & exports | Run readiness checks, verify evidence inventory, export audit logs, export engagement metadata, and download reports |

## What changed from the old UI

The previous `/ui` rendered read-only tables. The operator console is action-oriented. It can now perform the normal local workflow from the browser:

```text
create engagement
  -> add target
  -> upload artifact
  -> propose tool call
  -> approve or execute authorized work
  -> store evidence
  -> create finding
  -> export report/audit/engagement metadata
```

## Safety boundary

The console does not add new dangerous execution primitives. It calls the existing typed APIs and preserves the product boundary:

- no unrestricted shell runner
- no destructive workflow
- no persistence/evasion workflow
- no unscoped network operation
- policy and approval checks remain server-side

## API parity

Every console action maps to an HTTP API endpoint. Operators can switch between the console, the CLI, the SDK, and raw HTTP requests without changing the underlying workflow.
