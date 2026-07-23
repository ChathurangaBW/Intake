from fastapi import FastAPI

from intake.orchestrator import Orchestrator
from intake.schemas import ToolCallDecision, ToolCallRequest

app = FastAPI(title="Intake", version="0.1.0")
orchestrator = Orchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/authorize", response_model=ToolCallDecision)
async def authorize_tool_call(request: ToolCallRequest) -> ToolCallDecision:
    return await orchestrator.authorize(request)
