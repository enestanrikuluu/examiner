"""CSV export for exam session results."""

from __future__ import annotations

import csv
import io
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.questions.models import QuestionItem
from src.sessions.models import ExamSession, Response


async def export_sessions_csv(
    db: AsyncSession,
    template_id: uuid.UUID,
    include_responses: bool = False,
    include_grades: bool = True,
) -> str:
    """Generate CSV content for session results.

    Returns CSV as a string.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if include_responses and include_grades:
        await _write_detailed_csv(db, writer, template_id)
    elif include_grades:
        await _write_grades_csv(db, writer, template_id)
    else:
        await _write_summary_csv(db, writer, template_id)

    return output.getvalue()


async def _write_summary_csv(
    db: AsyncSession,
    writer: Any,
    template_id: uuid.UUID,
) -> None:
    """Session-level summary CSV."""
    writer.writerow([
        "session_id",
        "user_id",
        "status",
        "total_score",
        "max_score",
        "percentage",
        "passed",
        "started_at",
        "submitted_at",
    ])

    stmt = (
        select(ExamSession)
        .where(
            ExamSession.template_id == template_id,
            ExamSession.status.in_(["submitted", "graded"]),
        )
        .order_by(ExamSession.created_at)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    for s in sessions:
        writer.writerow([
            str(s.id),
            str(s.user_id),
            s.status,
            s.total_score,
            s.max_score,
            s.percentage,
            s.passed,
            s.started_at.isoformat() if s.started_at else "",
            s.submitted_at.isoformat() if s.submitted_at else "",
        ])


async def _write_grades_csv(
    db: AsyncSession,
    writer: Any,
    template_id: uuid.UUID,
) -> None:
    """Per-question grades CSV."""
    writer.writerow([
        "session_id",
        "user_id",
        "question_id",
        "question_type",
        "topic",
        "grading_method",
        "score",
        "max_score",
        "is_correct",
        "confidence",
        "feedback",
    ])

    stmt = (
        select(ExamSession)
        .options(
            selectinload(ExamSession.responses).selectinload(Response.grades)
        )
        .where(
            ExamSession.template_id == template_id,
            ExamSession.status.in_(["submitted", "graded"]),
        )
        .order_by(ExamSession.created_at)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Build question lookup
    q_stmt = select(QuestionItem).where(QuestionItem.template_id == template_id)
    q_result = await db.execute(q_stmt)
    q_map = {q.id: q for q in q_result.scalars().all()}

    for s in sessions:
        for resp in s.responses:
            q = q_map.get(resp.question_id)
            for grade in resp.grades:
                writer.writerow([
                    str(s.id),
                    str(s.user_id),
                    str(resp.question_id),
                    q.question_type if q else "",
                    q.topic if q else "",
                    grade.grading_method,
                    grade.score,
                    grade.max_score,
                    grade.is_correct,
                    grade.confidence,
                    (grade.feedback or "").replace("\n", " ")[:200],
                ])


async def _write_detailed_csv(
    db: AsyncSession,
    writer: Any,
    template_id: uuid.UUID,
) -> None:
    """Detailed CSV including response data."""
    writer.writerow([
        "session_id",
        "user_id",
        "question_id",
        "question_type",
        "topic",
        "answer",
        "time_spent_seconds",
        "is_flagged",
        "grading_method",
        "score",
        "max_score",
        "is_correct",
        "confidence",
        "feedback",
    ])

    stmt = (
        select(ExamSession)
        .options(
            selectinload(ExamSession.responses).selectinload(Response.grades)
        )
        .where(
            ExamSession.template_id == template_id,
            ExamSession.status.in_(["submitted", "graded"]),
        )
        .order_by(ExamSession.created_at)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    q_stmt = select(QuestionItem).where(QuestionItem.template_id == template_id)
    q_result = await db.execute(q_stmt)
    q_map = {q.id: q for q in q_result.scalars().all()}

    for s in sessions:
        for resp in s.responses:
            q = q_map.get(resp.question_id)
            answer_str = str(resp.answer)[:200]

            if resp.grades:
                for grade in resp.grades:
                    writer.writerow([
                        str(s.id),
                        str(s.user_id),
                        str(resp.question_id),
                        q.question_type if q else "",
                        q.topic if q else "",
                        answer_str,
                        resp.time_spent_seconds,
                        resp.is_flagged,
                        grade.grading_method,
                        grade.score,
                        grade.max_score,
                        grade.is_correct,
                        grade.confidence,
                        (grade.feedback or "").replace("\n", " ")[:200],
                    ])
            else:
                writer.writerow([
                    str(s.id),
                    str(s.user_id),
                    str(resp.question_id),
                    q.question_type if q else "",
                    q.topic if q else "",
                    answer_str,
                    resp.time_spent_seconds,
                    resp.is_flagged,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ])
