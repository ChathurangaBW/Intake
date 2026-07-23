# Contributing

Thanks for improving Intake.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,orchestration]
docker compose up -d postgres opa minio
alembic upgrade head
```

## Checks

```bash
make check
make qa
```

## Safety boundary

Changes must preserve Intake's product boundary:

- no unrestricted shell execution
- no exploit automation
- no evasion or persistence workflows
- no destructive actions
- no unscoped network operations

New execution capability must be:

1. typed through a schema,
2. scoped to an engagement,
3. policy-gated,
4. audited,
5. test-covered,
6. documented in the threat model if it changes the runtime boundary.

## Pull requests

A good PR includes:

- implementation
- tests or QA notes
- docs updates when operator behavior changes
- clear safety-boundary notes
