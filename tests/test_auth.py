from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from intake.auth import install_api_key_auth
from intake.config import settings


def test_api_key_auth_can_be_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_key", "secret")
    app = FastAPI()
    install_api_key_auth(app)

    @app.get("/private")
    def private() -> dict[str, str]:
        return {"ok": "yes"}

    client = TestClient(app)
    assert client.get("/private").status_code == 401
    assert client.get("/private", headers={"x-intake-api-key": "secret"}).status_code == 200


def test_health_is_public_when_auth_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_key", "secret")
    app = FastAPI()
    install_api_key_auth(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    assert TestClient(app).get("/health").status_code == 200
