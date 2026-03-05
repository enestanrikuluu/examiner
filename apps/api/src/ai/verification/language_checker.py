"""Checks that generated questions are in the expected language."""

from __future__ import annotations


def check_language(text: str, expected_locale: str) -> bool:
    """Check if text is likely in the expected language.

    Uses langdetect for basic language detection.
    Returns True if language matches or detection is inconclusive.
    """
    if len(text.strip()) < 20:
        return True  # Too short to reliably detect

    try:
        from langdetect import detect

        detected = detect(text)
    except Exception:
        return True  # If detection fails, don't block

    locale_to_lang = {
        "tr-TR": "tr",
        "en-US": "en",
    }
    expected_lang = locale_to_lang.get(expected_locale, expected_locale[:2])
    return bool(detected == expected_lang)
