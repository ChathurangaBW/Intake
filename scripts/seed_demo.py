from __future__ import annotations

import asyncio
from pathlib import Path

from intake.db import SessionLocal
from intake.schemas import RiskLevel, ToolCallRequest
from intake.services import IntakeError, IntakeService


async def main() -> None:
    engagement_id = "demo-intake"
    sample_path = Path("demo-sample.bin")
    sample_path.write_bytes(b"Intake demo sample artifact. Authorized read-only analysis only.\n")

    with SessionLocal() as session:
        service = IntakeService(session)
        try:
            service.create_engagement(
                engagement_id=engagement_id,
                name="Demo Intake Assessment",
                classification="demo",
                manifest={
                    "targets": {"domains": ["app.authorized-example.test"]},
                    "allowed": {"read_only_static_analysis": True},
                },
                actor="seed-demo",
            )
        except IntakeError:
            pass

        try:
            service.add_target(
                engagement_id=engagement_id,
                target_ref="app.authorized-example.test",
                target_type="domain",
                actor="seed-demo",
            )
        except Exception:
            pass

        artifact = service.ingest_artifact(
            engagement_id=engagement_id,
            path=sample_path,
            media_type="application/octet-stream",
            source="seed-demo",
            metadata={"purpose": "demo"},
            actor="seed-demo",
        )

        proposal = await service.propose_tool_call(
            ToolCallRequest(
                engagement_id=engagement_id,
                actor="seed-demo",
                tool="ghidra",
                operation="analyze",
                risk=RiskLevel.READ_ONLY,
                arguments={"artifact_id": artifact.id, "profile": "quick"},
            )
        )

        if proposal.status == "authorized":
            result = await service.execute_tool_call(proposal.tool_call_id)
            print(result.model_dump_json(indent=2))
        else:
            print({"tool_call_id": proposal.tool_call_id, "status": proposal.status})

        service.create_finding(
            engagement_id=engagement_id,
            title="Demo static-analysis evidence captured",
            description="The seeded demo created a harmless artifact and routed it through the authorized read-only analysis path.",
            severity="informational",
            actor="seed-demo",
        )

    print("Demo seeded. Open http://127.0.0.1:8000/ui/engagements/demo-intake")


if __name__ == "__main__":
    asyncio.run(main())
