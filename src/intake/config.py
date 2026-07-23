from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Intake."""

    model_config = SettingsConfigDict(env_prefix="INTAKE_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql://intake:intake@localhost:5432/intake"

    object_store_endpoint: str = "http://localhost:9000"
    object_store_bucket: str = "intake-evidence"
    object_store_access_key: str = "intake"
    object_store_secret_key: str = "intake-dev-password"
    object_store_region: str = "us-east-1"
    object_store_secure: bool = False

    opa_url: str = "http://localhost:8181/v1/data/intake/decision"
    default_network_policy: str = "deny_all"

    api_key: str | None = None
    enable_web_ui: bool = True

    worker_static_image: str = "intake/static-worker:dev"
    worker_dynamic_backend: str = "manual-vm"
    enable_external_static_tools: bool = False
    rizin_path: str = "rizin"
    ghidra_analyze_headless_path: str = "analyzeHeadless"
    ghidra_project_root: str = "/tmp/intake-ghidra"
    external_tool_output_limit_bytes: int = 262144

    maximum_tool_runtime_seconds: int = 1800
    maximum_agent_turns: int = 12
    maximum_tool_calls: int = 30
    maximum_subagent_depth: int = 1
    maximum_cost_usd: float = 2.0

    allow_unrestricted_shell: bool = False
    allow_dynamic_execution_without_approval: bool = False


settings = Settings()
