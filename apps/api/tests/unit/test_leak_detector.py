from src.ai.verification.leak_detector import detect_answer_leak


def test_no_leak_for_clean_mcq() -> None:
    warnings = detect_answer_leak(
        stem="2+2 kaçtır?",
        correct_answer={"key": "B"},
        options=[
            {"key": "A", "text": "3"},
            {"key": "B", "text": "4"},
            {"key": "C", "text": "5"},
            {"key": "D", "text": "6"},
        ],
    )
    assert warnings == []


def test_detects_mcq_answer_in_stem() -> None:
    warnings = detect_answer_leak(
        stem="Ankara Türkiye'nin başkentidir. Türkiye'nin başkenti neresidir?",
        correct_answer={"key": "A"},
        options=[
            {"key": "A", "text": "Ankara"},
            {"key": "B", "text": "İstanbul"},
            {"key": "C", "text": "İzmir"},
            {"key": "D", "text": "Bursa"},
        ],
    )
    assert len(warnings) >= 1
    assert "verbatim" in warnings[0].lower() or "appears" in warnings[0].lower()


def test_detects_numeric_value_in_stem() -> None:
    warnings = detect_answer_leak(
        stem="Pi sayısı 3.14'e yakındır. Pi'nin değeri nedir?",
        correct_answer={"value": 3.14},
    )
    assert len(warnings) >= 1


def test_detects_keyword_in_stem() -> None:
    warnings = detect_answer_leak(
        stem="Ankara, Türkiye'nin başkentidir. Türkiye'nin başkenti neresidir?",
        correct_answer={"keywords": ["Ankara"]},
    )
    assert len(warnings) >= 1


def test_no_leak_for_short_options() -> None:
    """Very short option texts (<=3 chars) should be ignored."""
    warnings = detect_answer_leak(
        stem="What is the value of x if x = 2?",
        correct_answer={"key": "A"},
        options=[
            {"key": "A", "text": "2"},
            {"key": "B", "text": "3"},
        ],
    )
    assert warnings == []
