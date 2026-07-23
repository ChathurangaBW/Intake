from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from intake import __version__
from intake.api import app

pytestmark = pytest.mark.unit


def test_final_version_is_consistent() -> None:
    assert __version__ == "1.0.0"
    assert app.version == __version__
    assert TestClient(app).get("/health").json()["version"] == __version__
