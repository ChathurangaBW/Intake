from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


class IntakeClientError(RuntimeError):
    """Raised when the Intake API returns an error response."""


@dataclass(frozen=True)
class IntakeClient:
    """Small typed client for the Intake HTTP API.

    The client is intentionally thin. It keeps integrations stable without
    hiding the policy-gated nature of the server-side runtime.
    """

    base_url: str = "http://127.0.0.1:8000"
    api_key: str | None = None
    timeout: float = 30.0

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["x-intake-api-key"] = self.api_key
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.update(self._headers())
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise IntakeClientError(f"{response.status_code} {response.text}")
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def stats(self) -> dict[str, Any]:
        return self._request("GET", "/stats")

    def create_engagement(
        self,
        engagement_id: str,
        name: str,
        *,
        classification: str = "internal",
        manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/engagements",
            json={
                "engagement_id": engagement_id,
                "name": name,
                "classification": classification,
                "manifest": manifest or {},
            },
        )

    def add_target(self, engagement_id: str, target_ref: str, target_type: str = "domain") -> dict[str, Any]:
        return self._request(
            "POST",
            f"/engagements/{engagement_id}/targets",
            json={"target_ref": target_ref, "target_type": target_type},
        )

    def upload_artifact(self, engagement_id: str, path: str | Path, media_type: str = "application/octet-stream") -> dict[str, Any]:
        file_path = Path(path)
        with file_path.open("rb") as handle:
            return self._request(
                "POST",
                f"/engagements/{engagement_id}/artifacts",
                files={"file": (file_path.name, handle, media_type)},
            )

    def propose_tool_call(
        self,
        engagement_id: str,
        actor: str,
        tool: str,
        operation: str,
        *,
        risk: str = "read_only",
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/tool-calls",
            json={
                "engagement_id": engagement_id,
                "actor": actor,
                "tool": tool,
                "operation": operation,
                "risk": risk,
                "arguments": arguments or {},
            },
        )

    def execute_tool_call(self, tool_call_id: str) -> dict[str, Any]:
        return self._request("POST", f"/tool-calls/{tool_call_id}/execute")

    def list_evidence(self, engagement_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/engagements/{engagement_id}/evidence")

    def render_report(self, engagement_id: str) -> str:
        return self._request("GET", f"/engagements/{engagement_id}/report.md")
