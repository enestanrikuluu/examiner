from src.core.config import Settings


def test_default_settings() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
    )
    assert s.app_name == "AI Examiner"
    assert s.app_version == "0.1.0"
    assert s.debug is False
    assert s.api_prefix == "/api/v1"
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_access_token_expire_minutes == 30


def test_feature_flags_default_off() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
    )
    assert s.feature_proctoring_enabled is False
    assert s.feature_adaptive_enabled is False
    assert s.feature_tab_switch_detection is True
