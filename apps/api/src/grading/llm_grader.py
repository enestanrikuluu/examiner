"""LLM-based grader using Claude for subjective question types (long_form)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.models import ModelTrace
from src.ai.providers.anthropic_provider import AnthropicProvider
from src.grading.deterministic import GradeResult

# System prompt for rubric-based grading
GRADING_SYSTEM_PROMPT = """\
Sen profesyonel bir sınav değerlendiricisisin. Öğrenci cevaplarını verilen rubriğe göre \
puanlayacaksın.

Kurallar:
- Her kriteri bağımsız olarak değerlendir.
- Puanlamada objektif ol, yalnızca cevap içeriğine odaklan.
- Geri bildirim yapıcı ve öğretici olsun.
- Türkçe cevap ver.

Çıktını SADECE JSON formatında ver:\
"""

GRADING_USER_TEMPLATE = """\
Soru: {stem}

Rubrik:
{rubric_text}

Öğrenci Cevabı:
{student_answer}

JSON formatında değerlendir:
{{
  "total_score": <toplam puan>,
  "max_score": {max_score},
  "confidence": <0.0-1.0 arası güven>,
  "feedback": "<genel geri bildirim>",
  "criteria_scores": [
    {{
      "criterion_id": "<kriter id>",
      "score": <puan>,
      "max_score": <max puan>,
      "feedback": "<kriter geri bildirimi>"
    }}
  ]
}}\
"""


def _format_rubric(rubric: dict[str, Any]) -> tuple[str, float]:
    """Format rubric into human-readable text. Returns (text, max_score)."""
    criteria = rubric.get("criteria", [])
    max_score = float(rubric.get("max_score", 10.0))
    lines = []
    for c in criteria:
        lines.append(
            f"- {c.get('id', '?')}: {c.get('description', '')} "
            f"(Maks: {c.get('max_points', 0)} puan)"
        )
    return "\n".join(lines), max_score


async def grade_with_llm(
    stem: str,
    student_answer: str,
    rubric: dict[str, Any],
    db: AsyncSession,
    user_id: uuid.UUID | None = None,
    template_id: uuid.UUID | None = None,
    temperature: float = 0.3,
) -> tuple[GradeResult, uuid.UUID | None]:
    """Grade a long-form answer using Claude with rubric.

    Returns:
        Tuple of (GradeResult, model_trace_id)
    """
    rubric_text, max_score = _format_rubric(rubric)

    user_prompt = GRADING_USER_TEMPLATE.format(
        stem=stem,
        rubric_text=rubric_text,
        student_answer=student_answer,
        max_score=max_score,
    )

    provider = AnthropicProvider()
    trace_id: uuid.UUID | None = None

    try:
        response = await provider.generate_with_timing(
            system_prompt=GRADING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            json_mode=False,
            temperature=temperature,
            max_tokens=2048,
        )

        # Log model trace
        trace = ModelTrace(
            provider=provider.provider_name,
            model=provider.default_model,
            task_type="grading",
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            status="success",
            template_id=template_id,
            user_id=user_id,
        )
        db.add(trace)
        await db.flush()
        await db.refresh(trace)
        trace_id = trace.id

        # Parse response
        result = _parse_grading_response(response.content, max_score)
        return result, trace_id

    except Exception as e:
        # Log failed trace
        trace = ModelTrace(
            provider=provider.provider_name,
            model=provider.default_model,
            task_type="grading",
            status="error",
            error_message=str(e),
            template_id=template_id,
            user_id=user_id,
        )
        db.add(trace)
        await db.flush()
        await db.refresh(trace)

        return GradeResult(
            score=0.0,
            max_score=max_score,
            is_correct=None,
            feedback=f"LLM grading failed: {e}",
            confidence=0.0,
            grading_method="fallback",
        ), trace.id


def _parse_grading_response(content: str, max_score: float) -> GradeResult:
    """Parse the JSON response from the LLM grader."""
    # Try to extract JSON from the response
    content = content.strip()

    # Handle markdown code blocks
    if content.startswith("```"):
        lines = content.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                json_lines.append(line)
        content = "\n".join(json_lines)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(content[start:end])
            except json.JSONDecodeError:
                return GradeResult(
                    score=0.0,
                    max_score=max_score,
                    is_correct=None,
                    feedback="LLM yanıtı ayrıştırılamadı.",
                    confidence=0.0,
                    grading_method="fallback",
                )
        else:
            return GradeResult(
                score=0.0,
                max_score=max_score,
                is_correct=None,
                feedback="LLM yanıtı JSON içermiyor.",
                confidence=0.0,
                grading_method="fallback",
            )

    total_score = float(data.get("total_score", 0))
    confidence = float(data.get("confidence", 0.5))
    feedback = data.get("feedback", "")

    # Clamp score to valid range
    total_score = max(0.0, min(total_score, max_score))
    confidence = max(0.0, min(confidence, 1.0))

    return GradeResult(
        score=round(total_score, 2),
        max_score=max_score,
        is_correct=total_score >= max_score * 0.5,
        feedback=feedback,
        confidence=round(confidence, 3),
        grading_method="llm",
    )
