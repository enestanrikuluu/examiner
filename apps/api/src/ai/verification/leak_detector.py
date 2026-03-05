"""Detects when question stems accidentally reveal the correct answer."""

from __future__ import annotations

from typing import Any


def detect_answer_leak(
    stem: str,
    correct_answer: dict[str, Any],
    options: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Check if the question stem leaks the correct answer.

    Returns a list of warning messages (empty if no leaks detected).
    """
    warnings: list[str] = []
    stem_lower = stem.lower()

    # For MCQ: check if the correct option text appears verbatim in the stem
    if options and "key" in correct_answer:
        correct_key = correct_answer["key"]
        for opt in options:
            if opt.get("key") == correct_key:
                opt_text = opt.get("text", "").lower().strip()
                if opt_text and len(opt_text) > 3 and opt_text in stem_lower:
                    warnings.append(
                        f"Correct answer text '{opt.get('text')}' "
                        f"appears verbatim in the stem"
                    )
                break

    # For True/False: check if stem contains "doğru" or "yanlış" matching answer
    if "value" in correct_answer and isinstance(correct_answer["value"], bool):
        if correct_answer["value"] and "doğrudur" in stem_lower:
            warnings.append("Stem contains 'doğrudur' which leaks true/false answer")
        if not correct_answer["value"] and "yanlıştır" in stem_lower:
            warnings.append("Stem contains 'yanlıştır' which leaks true/false answer")

    # For numeric: check if exact answer value appears in stem
    if "value" in correct_answer and isinstance(correct_answer["value"], (int, float)):
        value_str = str(correct_answer["value"])
        if value_str in stem:
            warnings.append(
                f"Numeric answer value '{value_str}' appears in the stem"
            )

    # For short_answer: check if keywords appear in stem
    if "keywords" in correct_answer:
        for kw in correct_answer["keywords"]:
            if isinstance(kw, str) and kw.lower() in stem_lower:
                warnings.append(f"Keyword '{kw}' appears in the stem")

    return warnings
