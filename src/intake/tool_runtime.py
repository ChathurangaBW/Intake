from __future__ import annotations

from sqlalchemy.orm import Session

from intake.tools.ghidra import GhidraAnalyzeTool
from intake.tools.registry import ToolRegistry
from intake.tools.rizin import RizinAnalyzeTool
from intake.workers.external_static import HybridStaticWorkerClient


def build_default_registry(session: Session) -> ToolRegistry:
    """Build the default safe runtime registry.

    The hybrid worker uses fixed-argument Ghidra/Rizin invocations when enabled
    and available, otherwise it falls back to the built-in read-only metadata and
    string extraction worker.
    """
    worker = HybridStaticWorkerClient(session)
    registry = ToolRegistry()
    registry.register(GhidraAnalyzeTool(worker))
    registry.register(RizinAnalyzeTool(worker))
    return registry
