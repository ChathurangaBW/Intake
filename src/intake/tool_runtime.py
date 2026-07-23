from __future__ import annotations

from sqlalchemy.orm import Session

from intake.tools.ghidra import GhidraAnalyzeTool
from intake.tools.registry import ToolRegistry
from intake.tools.rizin import RizinAnalyzeTool
from intake.workers.local_static import LocalStaticWorkerClient


def build_default_registry(session: Session) -> ToolRegistry:
    """Build the default safe runtime registry.

    Ghidra/Rizin wrappers are wired to the local read-only static worker by
    default. Deployments can replace this worker with containerized wrappers that
    invoke real headless Ghidra/Rizin binaries inside isolated workers.
    """
    worker = LocalStaticWorkerClient(session)
    registry = ToolRegistry()
    registry.register(GhidraAnalyzeTool(worker))
    registry.register(RizinAnalyzeTool(worker))
    return registry
