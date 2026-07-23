from __future__ import annotations

from pathlib import Path

from intake.client import IntakeClient


client = IntakeClient()
engagement_id = "sdk-demo"

try:
    client.create_engagement(engagement_id, "SDK Demo Authorized Assessment")
except Exception:
    # Demo-friendly: allow repeated runs when the engagement already exists.
    pass

sample = Path("sample-sdk.bin")
sample.write_bytes(b"hello from intake sdk quickstart")

artifact = client.upload_artifact(engagement_id, sample)
proposal = client.propose_tool_call(
    engagement_id,
    "sdk",
    "ghidra",
    "analyze",
    arguments={"artifact_id": artifact["id"], "profile": "quick"},
)

if proposal["status"] == "authorized":
    result = client.execute_tool_call(proposal["tool_call_id"])
    print(result)
else:
    print(proposal)

print(client.render_report(engagement_id))
