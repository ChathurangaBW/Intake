from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from intake.config import settings
from intake.platform import install_platform, router

pytestmark = pytest.mark.unit


def test_request_id_security_headers_and_liveness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_hosts", ["testserver"])
    monkeypatch.setattr(settings, "allowed_origins", [])
    monkeypatch.setattr(settings, "maximum_request_bytes", 1024)
    app = FastAPI()
    install_platform(app)
    app.include_router(router)

    @app.get("/hello")
    def hello(request: Request) -> dict[str, str]:
        return {"request_id": request.state.request_id}

    client = TestClient(app)
    response = client.get("/hello", headers={"x-request-id": "qa-request-1234"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "qa-request-1234"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.json()["request_id"] == "qa-request-1234"
    assert client.get("/health/live").json() == {"status": "alive"}


def test_request_size_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_hosts", ["testserver"])
    monkeypatch.setattr(settings, "allowed_origins", [])
    monkeypatch.setattr(settings, "maximum_request_bytes", 8)
    app = FastAPI()
    install_platform(app)

    @app.post("/echo")
    async def echo(request: Request) -> dict[str, int]:
        return {"size": len(await request.body())}

    response = TestClient(app).post("/echo", content=b"0123456789")
    assert response.status_code == 413


def test_inline_execution_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_hosts", ["testserver"])
    monkeypatch.setattr(settings, "allowed_origins", [])
    monkeypatch.setattr(settings, "enable_inline_tool_execution", False)
    app = FastAPI()
    install_platform(app)

    @app.post("/tool-calls/{tool_call_id}/execute")
    def execute(tool_call_id: str) -> dict[str, str]:
        return {"tool_call_id": tool_call_id}

    response = TestClient(app).post("/tool-calls/tool-1/execute")
    assert response.status_code == 409
    assert response.json()["enqueue_endpoint"] == "/tool-calls/tool-1/enqueue"


def test_route_specific_csp_keeps_docs_and_dashboard_usable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_hosts", ["testserver"])
    monkeypatch.setattr(settings, "allowed_origins", [])
    app = FastAPI()
    install_platform(app)

    @app.get("/ui", response_class=HTMLResponse)
    def ui() -> str:
        return "<style>body{display:block}</style>"

    client = TestClient(app)
    docs_csp = client.get("/docs").headers["content-security-policy"]
    ui_csp = client.get("/ui").headers["content-security-policy"]

    assert "https://cdn.jsdelivr.net" in docs_csp
    assert "'unsafe-inline'" in ui_csp
    assert "frame-ancestors 'none'" in docs_csp
    assert "frame-ancestors 'none'" in ui_csp
