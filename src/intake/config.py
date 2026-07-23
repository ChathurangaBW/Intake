from __future__ import annotations

import tempfile
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_ghidra_project_root() -> str:
    return str(Path(tempfile.gettempdir()) / "intake-ghidra")


class Settings(BaseSettings):
    """Runtime configuration for Intake.

    Structured values such as ``api_keys``, ``allowed_origins``, and
    ``trusted_hosts`` can be supplied as JSON through environment variables.
    """

    model_config = SettingsConfigDict(env_prefix="INTAKE_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+psycopg://intake:intake@localhost:5432/intake"
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)

    object_store_endpoint: str = "http://localhost:9000"
    object_store_bucket: str = "intake-evidence"
    object_store_access_key: str = ""
    object_store_secret_key: str = ""
    object_store_region: str = "us-east-1"
    object_store_secure: bool = False

    opa_url: str = "http://localhost:8181/v1/data/intake/decision"
    opa_health_url: str = "http://localhost:8181/health"
    default_network_policy: str = "deny_all"

    # Legacy single-key configuration. It is treated as an admin key.
    api_key: str | None = None
    # JSON mapping of API key to role, for example:
    # {"viewer-secret":"viewer","operator-secret":"operator","admin-secret":"admin"}
    api_keys: dict[str, str] = Field(default_factory=dict)
    enable_web_ui: bool = True
    allowed_origins: list[str] = Field(default_factory=list)
    trusted_hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "testserver"])
    maximum_request_bytes: int = Field(default=16 * 1024 * 1024, ge=1024)
    maximum_upload_bytes: int = Field(default=64 * 1024 * 1024, ge=1024)
    readiness_timeout_seconds: float = Field(default=3.0, ge=0.1, le=30.0)
    structured_logging: bool = True
    metrics_enabled: bool = True
    enable_inline_tool_execution: bool = False

    worker_static_image: str = "intake/static-worker:dev"
    worker_dynamic_backend: str = "manual-vm"
    enable_external_static_tools: bool = False
    rizin_path: str = "rizin"
    ghidra_analyze_headless_path: str = "analyzeHeadless"
    ghidra_project_root: str = Field(default_factory=default_ghidra_project_root)
    external_tool_output_limit_bytes: int = 262144
    worker_poll_interval_seconds: float = Field(default=1.0, ge=0.1, le=60.0)
    job_lease_seconds: int = Field(default=900, ge=30, le=86400)

    maximum_tool_runtime_seconds: int = 1800
    maximum_agent_turns: int = 12
    maximum_tool_calls: int = 30
    maximum_subagent_depth: int = 1
    maximum_cost_usd: float = 2.0

    allow_unrestricted_shell: bool = False
    allow_dynamic_execution_without_approval: bool = False


settings = Settings()
