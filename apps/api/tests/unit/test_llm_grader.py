"""Tests for the LLM grading response parser."""

from src.grading.llm_grader import _parse_grading_response


def test_parse_valid_json() -> None:
    content = """{
        "total_score": 7.5,
        "max_score": 10,
        "confidence": 0.85,
        "feedback": "İyi bir cevap.",
        "criteria_scores": [
            {"criterion_id": "c1", "score": 4, "max_score": 5, "feedback": "İyi"},
            {"criterion_id": "c2", "score": 3.5, "max_score": 5, "feedback": "Orta"}
        ]
    }"""
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 7.5
    assert result.max_score == 10.0
    assert result.confidence == 0.85
    assert result.feedback == "İyi bir cevap."
    assert result.grading_method == "llm"
    assert result.is_correct is True  # 7.5 >= 5.0


def test_parse_json_in_markdown_block() -> None:
    content = """```json
{
    "total_score": 3.0,
    "max_score": 10,
    "confidence": 0.9,
    "feedback": "Eksik cevap."
}
```"""
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 3.0
    assert result.is_correct is False  # 3.0 < 5.0


def test_parse_json_with_surrounding_text() -> None:
    content = """İşte değerlendirmem:
{"total_score": 8.0, "max_score": 10, "confidence": 0.75, "feedback": "Güzel"}
Diğer notlar..."""
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 8.0
    assert result.confidence == 0.75


def test_parse_invalid_json_fallback() -> None:
    content = "Bu bir JSON değil"
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 0.0
    assert result.grading_method == "fallback"
    assert result.confidence == 0.0


def test_parse_clamps_score_to_max() -> None:
    content = '{"total_score": 15.0, "max_score": 10, "confidence": 0.8, "feedback": "ok"}'
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 10.0


def test_parse_clamps_negative_score() -> None:
    content = '{"total_score": -5.0, "max_score": 10, "confidence": 0.8, "feedback": "ok"}'
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 0.0


def test_parse_clamps_confidence() -> None:
    content = '{"total_score": 5.0, "max_score": 10, "confidence": 1.5, "feedback": "ok"}'
    result = _parse_grading_response(content, max_score=10.0)
    assert result.confidence == 1.0


def test_parse_missing_fields_defaults() -> None:
    content = '{"total_score": 6.0}'
    result = _parse_grading_response(content, max_score=10.0)
    assert result.score == 6.0
    assert result.confidence == 0.5
    assert result.feedback == ""
