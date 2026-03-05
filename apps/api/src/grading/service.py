"""Grading service: orchestrates deterministic + LLM grading for exam sessions."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError
from src.grading.deterministic import (
    GradeResult,
    can_grade_deterministically,
    grade_deterministic,
)
from src.grading.llm_grader import grade_with_llm
from src.grading.models import Grade
from src.grading.repository import GradeRepository
from src.grading.schemas import GradeOverride
from src.questions.models import QuestionItem
from src.sessions.models import ExamSession, Response

# Confidence thresholds
CONFIDENCE_REGRADE_THRESHOLD = 0.7
CONFIDENCE_MANUAL_REVIEW_THRESHOLD = 0.5


class GradingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GradeRepository(db)

    async def get_grade(self, grade_id: uuid.UUID) -> Grade:
        grade = await self.repo.get_by_id(grade_id)
        if grade is None:
            raise NotFoundError("Grade not found")
        return grade

    async def list_session_grades(self, session_id: uuid.UUID) -> list[Grade]:
        return await self.repo.list_by_session(session_id)

    async def override_grade(
        self,
        grade_id: uuid.UUID,
        data: GradeOverride,
        graded_by: uuid.UUID,
    ) -> Grade:
        grade = await self.get_grade(grade_id)
        return await self.repo.update(
            grade,
            score=data.score,
            feedback=data.feedback,
            grading_method="manual",
            graded_by=graded_by,
        )

    async def grade_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> ExamSession:
        """Grade all responses in a session.

        1. For each response, determines grading method:
           - Objective types (MCQ, T/F, numeric, short_answer) -> deterministic
           - Subjective types (long_form) -> LLM (Claude)
        2. Applies confidence thresholds for LLM grades:
           - < 0.7: re-grade with temperature=0.0
           - < 0.5 after re-grade: flag for manual review
        3. Computes session totals and updates session status to 'graded'.
        """
        # Load session with responses
        result = await self.db.execute(
            select(ExamSession)
            .options(selectinload(ExamSession.responses))
            .where(ExamSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise NotFoundError("Session not found")

        if session.status not in ("submitted", "graded"):
            raise ValidationError(
                f"Cannot grade session in '{session.status}' status"
            )

        # Load all questions for this session's template
        q_result = await self.db.execute(
            select(QuestionItem).where(
                QuestionItem.template_id == session.template_id,
                QuestionItem.is_active.is_(True),
            )
        )
        questions_by_id: dict[uuid.UUID, QuestionItem] = {
            q.id: q for q in q_result.scalars().all()
        }

        total_score = 0.0
        total_max = 0.0

        for response in session.responses:
            question = questions_by_id.get(response.question_id)
            if question is None:
                continue

            grade_result = await self._grade_response(
                response=response,
                question=question,
                session=session,
                user_id=user_id,
            )

            # Create or update grade record
            await self.repo.create(
                response_id=response.id,
                grading_method=grade_result.grading_method,
                score=grade_result.score,
                max_score=grade_result.max_score,
                is_correct=grade_result.is_correct,
                feedback=grade_result.feedback,
                confidence=grade_result.confidence,
            )

            total_score += grade_result.score
            total_max += grade_result.max_score

        # Update session totals
        percentage = round((total_score / total_max * 100), 2) if total_max > 0 else 0.0

        # Check pass/fail
        from src.exams.repository import ExamTemplateRepository

        template_repo = ExamTemplateRepository(self.db)
        template = await template_repo.get_by_id(session.template_id)
        passed: bool | None = None
        if template and template.pass_score is not None:
            passed = percentage >= float(template.pass_score)

        session.total_score = round(total_score, 2)
        session.max_score = round(total_max, 2)
        session.percentage = percentage
        session.passed = passed
        session.status = "graded"
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def regrade_response(
        self,
        grade_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> Grade:
        """Re-grade a single response using LLM with temperature=0."""
        grade = await self.get_grade(grade_id)

        # Load the response and question
        resp_result = await self.db.execute(
            select(Response).where(Response.id == grade.response_id)
        )
        response = resp_result.scalar_one_or_none()
        if response is None:
            raise NotFoundError("Response not found")

        q_result = await self.db.execute(
            select(QuestionItem).where(QuestionItem.id == response.question_id)
        )
        question = q_result.scalar_one_or_none()
        if question is None:
            raise NotFoundError("Question not found")

        if question.question_type != "long_form":
            raise ValidationError("Only long_form questions can be re-graded via LLM")

        rubric = question.rubric or {"max_score": 10, "criteria": []}
        student_text = str(response.answer.get("text", ""))

        llm_result, trace_id = await grade_with_llm(
            stem=question.stem,
            student_answer=student_text,
            rubric=rubric,
            db=self.db,
            user_id=user_id,
            template_id=question.template_id,
            temperature=0.0,
        )

        return await self.repo.update(
            grade,
            score=llm_result.score,
            feedback=llm_result.feedback,
            confidence=llm_result.confidence,
            grading_method="llm",
            model_trace_id=trace_id,
        )

    async def _grade_response(
        self,
        response: Response,
        question: QuestionItem,
        session: ExamSession,
        user_id: uuid.UUID | None,
    ) -> GradeResult:
        """Grade a single response, choosing deterministic or LLM grading."""
        answer: dict[str, Any] = response.answer
        correct_answer: dict[str, Any] = question.correct_answer
        qt = question.question_type

        # Deterministic grading for objective types
        if can_grade_deterministically(qt):
            return grade_deterministic(qt, answer, correct_answer)

        # LLM grading for long_form
        if qt == "long_form":
            rubric = question.rubric or {"max_score": 10, "criteria": []}
            student_text = str(answer.get("text", ""))

            if not student_text.strip():
                return GradeResult(
                    score=0.0,
                    max_score=float(rubric.get("max_score", 10)),
                    is_correct=False,
                    feedback="Cevap boş bırakıldı.",
                )

            llm_result, _trace_id = await grade_with_llm(
                stem=question.stem,
                student_answer=student_text,
                rubric=rubric,
                db=self.db,
                user_id=user_id,
                template_id=session.template_id,
            )

            # Confidence threshold: if low, re-grade with temperature=0
            if llm_result.confidence < CONFIDENCE_REGRADE_THRESHOLD:
                regrade_result, _trace_id = await grade_with_llm(
                    stem=question.stem,
                    student_answer=student_text,
                    rubric=rubric,
                    db=self.db,
                    user_id=user_id,
                    template_id=session.template_id,
                    temperature=0.0,
                )

                # If still low confidence, flag for manual review
                if regrade_result.confidence < CONFIDENCE_MANUAL_REVIEW_THRESHOLD:
                    regrade_result.grading_method = "fallback"
                    regrade_result.feedback = (
                        f"{regrade_result.feedback or ''}\n\n"
                        "⚠ Düşük güven skoru - manuel değerlendirme önerilir."
                    ).strip()

                return regrade_result

            return llm_result

        # Unknown type: can't grade
        return GradeResult(
            score=0.0,
            max_score=1.0,
            is_correct=None,
            feedback=f"Bilinmeyen soru tipi: {qt}",
            confidence=0.0,
            grading_method="fallback",
        )
