from unittest.mock import patch

from src.core.feature_flags import is_enabled


def test_is_enabled_returns_true_for_enabled_flag() -> None:
    with patch("src.core.feature_flags.settings") as mock_settings:
        mock_settings.feature_tab_switch_detection = True
        assert is_enabled("tab_switch_detection") is True


def test_is_enabled_returns_false_for_disabled_flag() -> None:
    with patch("src.core.feature_flags.settings") as mock_settings:
        mock_settings.feature_proctoring_enabled = False
        assert is_enabled("proctoring_enabled") is False


def test_is_enabled_returns_false_for_nonexistent_flag() -> None:
    with patch("src.core.feature_flags.settings") as mock_settings:
        del mock_settings.feature_nonexistent
        mock_settings.configure_mock(**{})
        assert is_enabled("nonexistent") is False
