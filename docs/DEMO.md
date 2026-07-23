# Demo workflow

Use the demo workflow to verify that Intake behaves like a complete local app.

## Start the stack

```bash
cp .env.example .env
docker compose up --build
```

## Seed demo data

In another terminal:

```bash
python scripts/seed_demo.py
```

The script creates:

- a demo engagement
- an authorized target
- a harmless sample artifact
- a read-only static-analysis tool call
- evidence records
- an informational finding

## Open the UI

```text
http://127.0.0.1:8000/ui/engagements/demo-intake
```

## Run smoke test

```bash
make smoke
```

## Python SDK demo

```bash
python examples/sdk_quickstart.py
```

## HTTP collection

Open [`examples/http/intake.http`](../examples/http/intake.http) in an editor that supports `.http` request files.
