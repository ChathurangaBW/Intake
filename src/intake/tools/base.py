from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from intake.schemas import RiskLevel


class ToolSpec(BaseModel):
    name: str
    operation: str
    risk: RiskLevel
    description: str
    requires_artifact: bool = False
    requires_target: bool = False
    network_required: bool = False


class ToolResult(BaseModel):
    status: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class IntakeTool(ABC):
    spec: ToolSpec

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        """Run a constrained tool implementation inside its assigned worker boundary."""
