# Intake architecture

Intake is built as a policy-controlled security automation framework for authorized work only.

## Control flow

```text
Operator / API
  -> engagement scope validation
  -> OPA policy decision
  -> typed tool request
  -> isolated worker
  -> evidence store
  -> verifier
  -> report output
```

## Design principles

1. **No unrestricted shell by default**
   - Tools must be typed and schema-validated.
   - Emergency shell access, if added, must be human-approved, isolated, timed, and fully logged.

2. **Policy before execution**
   - The planner may propose actions.
   - OPA or equivalent policy code decides whether the action may proceed.

3. **Isolation by task class**
   - Static analysis: rootless disposable containers.
   - Dynamic or untrusted execution: disposable VM or microVM workers.

4. **Evidence integrity**
   - Store evidence by hash.
   - Findings should reference evidence IDs, not copied unverified text.

5. **Model cost control**
   - Use deterministic parsing before LLM reasoning.
   - Pass only relevant fragments into prompts.
   - Set turn, tool-call, token, and cost budgets.

## Early components

- FastAPI API surface
- Typer CLI
- Pydantic schemas
- OPA/Rego starter policy
- Local development stack with PostgreSQL, OPA, and MinIO
