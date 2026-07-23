from __future__ import annotations

from intake.tools.base import IntakeTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, IntakeTool] = {}

    def register(self, tool: IntakeTool) -> None:
        key = f"{tool.spec.name}.{tool.spec.operation}"
        if key in self._tools:
            raise ValueError(f"tool already registered: {key}")
        self._tools[key] = tool

    def get(self, name: str, operation: str) -> IntakeTool:
        key = f"{name}.{operation}"
        try:
            return self._tools[key]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {key}") from exc

    def list_specs(self) -> list[dict[str, object]]:
        return [tool.spec.model_dump(mode="json") for tool in self._tools.values()]
