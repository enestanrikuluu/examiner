from src.core.config import settings


def is_enabled(flag_name: str) -> bool:
    attr = f"feature_{flag_name}"
    return bool(getattr(settings, attr, False))
