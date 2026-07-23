from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from intake.auth import install_api_key_auth
from intake.config import settings

pytestmark = pytest.mark.unit


def make_app() -> FastAPI:
    app = FastAPI()
    install_api_key_auth(app)

    @app.get("/records")
    def read_records() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/records")
    def write_records() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/tool-calls/one/execute")
    def execute() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/health/live")
    def live() -> dict[str, bool]:
        return {"ok": True}

    return app


def headers(key: str) -> dict[str, str]:
    return {"x-intake-api-key": key}


def test_role_hierarchy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "api_key", None)
    monkeypatch.setattr(
        settings,
        "api_keys",
        {
            "viewer-key": "viewer",
            "operator-key": "operator",
            "approver-key": "approver",
            "admin-key": "admin",
        },
    )
    client = TestClient(make_app())

    assert client.get("/records", headers=headers("viewer-key")).status_code == 200
    assert client.post("/records", headers=headers("viewer-key")).status_code == 403
    assert client.post("/records", headers=headers("operator-key")).status_code == 200
    assert client.post("/tool-calls/one/execute", headers=headers("operator-key")).status_code == 403
    assert client.post("/tool-calls/one/execute", headers=headers("approver-key")).status_code == 200
    assert client.post("/tool-calls/one/execute", headers=headers("admin-key")).status_code == 200


def test_invalid_key_is_rejected_and_health_is_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "api_key", None)
    monkeypatch.setattr(settings, "api_keys", {"admin-key": "admin"})
    client = TestClient(make_app())

    assert client.get("/records").status_code == 401
    assert client.get("/records", headers=headers("wrong")).status_code == 401
    assert client.get("/health/live").status_code == 200
