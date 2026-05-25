from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://ava:ava@localhost:5432/ava"
    langgraph_database_url: str = "postgresql://ava:ava@localhost:5432/ava"
    redis_url: str = "redis://localhost:6379/0"
    litellm_model: str = "gpt-4o"
    litellm_fallback_models: str = "gpt-4o-mini,claude-3-5-sonnet-20241022,gemini/gemini-1.5-pro"
    openai_api_key: str | None = None
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    mock_llm: bool = False
    mock_connectors: bool = True
    artifacts_dir: str = "./data/artifacts"
    storage_backend: str = "local"  # local | s3
    s3_bucket: str = "ava-artifacts"
    s3_endpoint: str | None = None
    collab_ws_url: str = "ws://localhost:1234"
    default_tenant_id: str = "default"
    ee_license_key: str | None = None
    jwt_secret: str = "dev-secret-change-in-production"
    oauth_redirect_uri: str = "http://localhost:3000/oauth/callback"
    enable_otel: bool = True
    ensemble_confidence_threshold: float = 0.55
    nango_url: str | None = None
    nango_secret_key: str | None = None
    replicate_api_key: str | None = None
    embedding_dimensions: int = 384
    llm_requests_per_minute: int = 60
    mcp_mount_path: str = "/mcp"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.litellm_fallback_models.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
