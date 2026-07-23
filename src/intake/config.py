from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Intake."""

    model_config = SettingsConfigDict(env_prefix="INTAKE_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql://intake:intake@localhost:5432/intake"
    object_store_endpoint: str = "http://localhost:9000"
    object_store_bucket: str = "intake-evidence"
    opa_url: str = "http://localhost:8181/v1/data/intake/decision"
    default_network_policy: str = "deny_all"


settings = Settings()
