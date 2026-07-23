# Operating model

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,orchestration]
docker compose up -d
alembic upgrade head
pytest
```

## Execution rules

1. Create or import an engagement manifest.
2. Register targets and artifacts.
3. Propose a typed tool call.
4. Validate request schema.
5. Send the request to OPA.
6. If approved by policy, dispatch to the correct worker boundary.
7. Store outputs as content-addressed evidence.
8. Link evidence to findings.
9. Verify findings before reporting.

## Worker modes

| Worker | Isolation expectation | Network |
|---|---|---|
| Static analysis | Rootless disposable container | Disabled by default |
| Dynamic analysis | Disposable VM or microVM | Deny-all or target allowlist |
| Reporting | Local process | Disabled by default |

## Approval-required operations

- Dynamic execution
- Active network checks
- State-changing requests
- High-cost model runs
- Any operation outside the default read-only profile

## Cost control

Set run budgets before every workflow:

```yaml
maximum_agent_turns: 12
maximum_tool_calls: 30
maximum_subagent_depth: 1
maximum_cost_usd: 2.00
```

The framework should fail closed when a budget is exceeded.
