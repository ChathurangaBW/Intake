# Python SDK

Intake includes a small typed Python client for automation around the HTTP API.

## Install

```bash
pip install -e .
```

## Basic use

```python
from intake.client import IntakeClient

client = IntakeClient(base_url="http://127.0.0.1:8000")
print(client.health())
```

If API key authentication is enabled:

```python
client = IntakeClient(
    base_url="http://127.0.0.1:8000",
    api_key="change-this-long-random-value",
)
```

## Workflow

```python
artifact = client.upload_artifact("sdk-demo", "sample.bin")
proposal = client.propose_tool_call(
    "sdk-demo",
    "sdk",
    "ghidra",
    "analyze",
    arguments={"artifact_id": artifact["id"], "profile": "quick"},
)

if proposal["status"] == "authorized":
    result = client.execute_tool_call(proposal["tool_call_id"])
```

## Example

See [`examples/sdk_quickstart.py`](../examples/sdk_quickstart.py).

## Boundary

The SDK does not bypass server-side policy. Tool calls still go through scope, policy, approval, audit, and constrained execution.
