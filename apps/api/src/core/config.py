import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI Examiner"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = '["http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> list[str]:
        v = self.cors_origins.strip()
        if v.startswith("["):
            return json.loads(v)  # type: ignore[no-any-return]
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # Database
    database_url: str = "postgresql+asyncpg://examiner:examiner@localhost:5432/examiner"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "examiner"
    minio_use_ssl: bool = False

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # AI Providers
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # Feature Flags
    feature_proctoring_enabled: bool = False
    feature_tab_switch_detection: bool = True
    feature_copy_paste_block: bool = False
    feature_fullscreen_required: bool = False
    feature_adaptive_enabled: bool = False


settings = Settings()
