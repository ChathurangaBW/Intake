from __future__ import annotations

from pydantic import BaseModel, Field

from intake.schemas import RiskLevel
from intake.tools.base import IntakeTool, ToolResult, ToolSpec
from intake.workers.static import StaticWorkerClient, StaticWorkerRequest


class GhidraAnalyzeArgs(BaseModel):
    artifact_id: str
    profile: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    timeout_seconds: int = Field(default=900, ge=30, le=3600)


class GhidraAnalyzeTool(IntakeTool):
    spec = ToolSpec(
        name="ghidra",
        operation="analyze",
        risk=RiskLevel.READ_ONLY,
        description="Run headless Ghidra static analysis on an authorized artifact.",
        requires_artifact=True,
        network_required=False,
    )

    def __init__(self, worker: StaticWorkerClient) -> None:
        self.worker = worker

    async def run(self, arguments: dict[str, object]) -> ToolResult:
        args = GhidraAnalyzeArgs.model_validate(arguments)
        result = await self.worker.submit(
            StaticWorkerRequest(
                worker_id="static-ghidra",
                tool_call_id=str(arguments.get("tool_call_id", "pending")),
                artifact_id=args.artifact_id,
                profile=args.profile,
                timeout_seconds=args.timeout_seconds,
            )
        )
        return ToolResult(
            status=result.status,
            summary=result.summary,
            evidence_ids=[item["id"] for item in result.evidence if "id" in item],
            data={"worker_id": result.worker_id},
        )
