from pathlib import Path

import pytest


@pytest.mark.unit
def test_smoke_script_exists_and_checks_core_routes() -> None:
    script = Path("scripts/smoke.sh")
    body = script.read_text(encoding="utf-8")

    assert "set -euo pipefail" in body
    assert "/health" in body
    assert "/docs" in body
    assert "/engagements" in body
    assert "/tool-calls" in body
    assert "/audit" in body
    assert "Smoke test passed" in body
