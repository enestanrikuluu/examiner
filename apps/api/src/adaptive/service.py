from __future__ import annotations

import math
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.adaptive.irt import (
    ItemParams,
    estimate_theta_eap,
    fisher_information,
    select_next_item,
    standard_error,
)
from src.adaptive.repository import ItemParameterRepository, ThetaHistoryRepository
from src.adaptive.schemas import (
    AdaptiveRespondOut,
    AdaptiveSessionOut,
    CalibrationResultOut,
    NextQuestionOut,
    NoMoreQuestions,
    ThetaHistoryEntry,
    ThetaOut,
)
from src.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from src.exams.repository import ExamTemplateRepository
from src.grading.deterministic import can_grade_deterministically, grade_deterministic
from src.questions.models import QuestionItem
from src.questions.repository import QuestionItemRepository
from src.sessions.models import ExamSession
from src.sessions.repository import ResponseRepository, SessionRepository

# Defaults
DEFAULT_MAX_ITEMS = 40
DEFAULT_MIN_ITEMS = 5
DEFAULT_SE_THRESHOLD = 0.30
DEFAULT_INITIAL_THETA = 0.0
DEFAULT_TIME_LIMIT_MINUTES = 90


class AdaptiveService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.session_repo = SessionRepository(db)
        self.response_repo = ResponseRepository(db)
        self.template_repo = ExamTemplateRepository(db)
        self.question_repo = QuestionItemRepository(db)
        self.item_param_repo = ItemParameterRepository(db)
        self.theta_repo = ThetaHistoryRepository(db)

    async def create_session(
        self, template_id: uuid.UUID, user_id: uuid.UUID
    ) -> AdaptiveSessionOut:
        """Create a new adaptive session for a template."""
        template = await self.template_repo.get_by_id(template_id)
        if template is None:
            raise NotFoundError("Exam template not found")
        if not template.is_published:
            raise ValidationError("Cannot start a session for an unpublished template")

        questions, _ = await self.question_repo.list_by_template(
            template_id, is_active=True
        )
        if not questions:
            raise ValidationError("Template has no active questions")

        # Only deterministic types in adaptive mode
        adaptive_types = {"mcq", "true_false", "numeric"}
        eligible = [q for q in questions if q.question_type in adaptive_types]
        if not eligible:
            raise ValidationError(
                "Template has no questions suitable for adaptive testing "
                "(requires mcq, true_false, or numeric)"
            )

        settings: dict[str, Any] = dict(template.settings or {})
        max_items = settings.get("adaptive_max_items", DEFAULT_MAX_ITEMS)
        time_limit = template.time_limit_minutes or DEFAULT_TIME_LIMIT_MINUTES
        now = datetime.now(UTC)

        session = await self.session_repo.create(
            template_id=template_id,
            user_id=user_id,
            status="in_progress",
            started_at=now,
            expires_at=now + timedelta(minutes=time_limit),
            theta=DEFAULT_INITIAL_THETA,
            session_metadata={
                "adaptive": True,
                "max_items": max_items,
                "min_items": DEFAULT_MIN_ITEMS,
                "se_threshold": DEFAULT_SE_THRESHOLD,
                "eligible_question_ids": [str(q.id) for q in eligible],
            },
        )

        return AdaptiveSessionOut(
            session_id=session.id,
            template_id=template_id,
            status=session.status,
            theta=DEFAULT_INITIAL_THETA,
            se=None,
            items_administered=0,
            max_items=max_items,
        )

    async def get_next_question(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> NextQuestionOut | NoMoreQuestions:
        """Select the next best question based on current theta."""
        session = await self._get_session(session_id, user_id)
        self._require_in_progress(session)
        self._check_expired(session)

        meta = session.session_metadata or {}
        max_items = meta.get("max_items", DEFAULT_MAX_ITEMS)
        min_items = meta.get("min_items", DEFAULT_MIN_ITEMS)
        se_threshold = meta.get("se_threshold", DEFAULT_SE_THRESHOLD)
        eligible_ids = meta.get("eligible_question_ids", [])

        # Get history to know which questions were already administered
        history = await self.theta_repo.list_by_session(session_id)
        administered_ids = {str(h.question_id) for h in history}
        step = len(history)

        theta = float(session.theta or DEFAULT_INITIAL_THETA)
        current_se = self._compute_se(theta, history)

        # Check termination conditions
        if step >= max_items:
            return NoMoreQuestions(
                finish_reason="max_items_reached",
                theta=theta,
                se=current_se,
                items_administered=step,
            )

        if step >= min_items and current_se <= se_threshold:
            return NoMoreQuestions(
                finish_reason="precision_reached",
                theta=theta,
                se=current_se,
                items_administered=step,
            )

        # Get available questions
        remaining_ids = [
            uuid.UUID(qid)
            for qid in eligible_ids
            if qid not in administered_ids
        ]
        if not remaining_ids:
            return NoMoreQuestions(
                finish_reason="no_items_remaining",
                theta=theta,
                se=current_se,
                items_administered=step,
            )

        # Load item parameters for remaining questions
        item_params_list = await self._get_item_params(remaining_ids)

        # Select top-k by Fisher information, then randomize within top-k
        top_items = select_next_item(theta, item_params_list, top_k=5)
        if not top_items:
            return NoMoreQuestions(
                finish_reason="no_items_remaining",
                theta=theta,
                se=current_se,
                items_administered=step,
            )

        selected = random.choice(top_items)

        # Load full question
        question = await self.question_repo.get_by_id(uuid.UUID(selected.item_id))
        if question is None:
            raise NotFoundError("Question not found")

        return NextQuestionOut(
            question_id=question.id,
            stem=question.stem,
            question_type=question.question_type,
            options=question.options,
            step=step + 1,
            theta=theta,
            se=current_se,
        )

    async def respond(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        question_id: uuid.UUID,
        answer: dict[str, Any],
        time_spent_seconds: int | None = None,
    ) -> AdaptiveRespondOut:
        """Process a response: grade, update theta, record history."""
        session = await self._get_session(session_id, user_id)
        self._require_in_progress(session)
        self._check_expired(session)

        # Load question
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            raise NotFoundError("Question not found")

        # Check question hasn't already been answered in this session
        history = await self.theta_repo.list_by_session(session_id)
        answered_ids = {h.question_id for h in history}
        if question_id in answered_ids:
            raise ValidationError("Question already answered in this session")

        # Grade deterministically
        if not can_grade_deterministically(question.question_type):
            raise ValidationError(
                f"Cannot grade '{question.question_type}' adaptively"
            )

        result = grade_deterministic(
            question.question_type, answer, question.correct_answer
        )
        is_correct = bool(result.is_correct)

        # Save response
        await self.response_repo.upsert(
            session_id=session_id,
            question_id=question_id,
            answer=answer,
            time_spent_seconds=time_spent_seconds,
        )

        # Build response history for theta estimation
        responses_for_irt = await self._build_response_tuples(history)
        # Add current response
        item_p = await self._get_single_item_params(question)
        responses_for_irt.append((item_p.a, item_p.b, 1.0 if is_correct else 0.0))

        # Estimate new theta
        new_theta = estimate_theta_eap(responses_for_irt)

        # Compute SE
        administered_items = [
            (r[0], r[1]) for r in responses_for_irt
        ]
        se = standard_error(new_theta, administered_items)

        step = len(history) + 1
        info = fisher_information(new_theta, item_p.a, item_p.b)

        # Record theta history
        await self.theta_repo.create(
            session_id=session_id,
            question_id=question_id,
            step=step,
            theta=round(new_theta, 3),
            se=round(se, 4),
            is_correct=is_correct,
            information=round(info, 4),
        )

        # Update session theta
        await self.session_repo.update(
            session, theta=round(new_theta, 3)
        )

        # Check termination
        meta = session.session_metadata or {}
        max_items = meta.get("max_items", DEFAULT_MAX_ITEMS)
        min_items = meta.get("min_items", DEFAULT_MIN_ITEMS)
        se_threshold = meta.get("se_threshold", DEFAULT_SE_THRESHOLD)

        is_finished = False
        finish_reason: str | None = None

        if step >= max_items:
            is_finished = True
            finish_reason = "max_items_reached"
        elif step >= min_items and se <= se_threshold:
            is_finished = True
            finish_reason = "precision_reached"
        else:
            eligible_ids = meta.get("eligible_question_ids", [])
            remaining = [
                qid for qid in eligible_ids
                if qid not in {str(qid2) for qid2 in answered_ids} and qid != str(question_id)
            ]
            if not remaining:
                is_finished = True
                finish_reason = "no_items_remaining"

        if is_finished:
            await self.session_repo.update(
                session,
                status="submitted",
                submitted_at=datetime.now(UTC),
            )

        return AdaptiveRespondOut(
            is_correct=is_correct,
            theta=round(new_theta, 3),
            se=round(se, 4),
            step=step,
            is_finished=is_finished,
            finish_reason=finish_reason,
        )

    async def get_theta(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ThetaOut:
        """Get theta history for a session."""
        session = await self._get_session(session_id, user_id)
        history = await self.theta_repo.list_by_session(session_id)

        return ThetaOut(
            session_id=session_id,
            current_theta=float(session.theta) if session.theta is not None else None,
            current_se=history[-1].se if history else None,
            history=[
                ThetaHistoryEntry(
                    step=h.step,
                    question_id=h.question_id,
                    theta=float(h.theta),
                    se=float(h.se),
                    is_correct=h.is_correct,
                    information=float(h.information) if h.information is not None else None,
                )
                for h in history
            ],
        )

    async def calibrate(
        self,
        template_id: uuid.UUID | None = None,
        min_responses: int = 30,
    ) -> CalibrationResultOut:
        """Calibrate item parameters from response history.

        For each eligible question, collect all responses across sessions,
        compute discrimination and difficulty using simplified approach.
        """
        from sqlalchemy import select

        from src.sessions.models import Response

        # Get questions to calibrate
        if template_id is not None:
            questions, _ = await self.question_repo.list_by_template(
                template_id, is_active=True
            )
        else:
            # Calibrate all questions — limited scope
            questions, _ = await self.question_repo.list_by_template(
                uuid.UUID(int=0),  # placeholder; real impl would do broader query
                is_active=True,
            )
            # For now, require template_id
            raise ValidationError("template_id is required for calibration")

        items_calibrated = 0
        items_skipped = 0
        errors: list[str] = []

        for question in questions:
            if question.question_type not in ("mcq", "true_false", "numeric"):
                items_skipped += 1
                continue

            # Get all responses for this question
            stmt = select(Response).where(Response.question_id == question.id)
            result = await self.db.execute(stmt)
            responses = list(result.scalars().all())

            if len(responses) < min_responses:
                items_skipped += 1
                continue

            # Compute p-value (proportion correct)
            correct_count = 0
            for resp in responses:
                try:
                    gr = grade_deterministic(
                        question.question_type,
                        resp.answer,
                        question.correct_answer,
                    )
                    if gr.is_correct:
                        correct_count += 1
                except Exception:
                    continue

            p_value = correct_count / len(responses) if responses else 0.5
            # Clamp p-value to avoid infinite b
            p_value = max(0.01, min(0.99, p_value))

            # Convert p-value to IRT difficulty (logit transform)
            b = -math.log(p_value / (1.0 - p_value))
            # Default discrimination; more sophisticated methods would use
            # joint MLE or marginal MLE
            a = float(question.discrimination or 1.0)

            try:
                await self.item_param_repo.upsert(
                    question_id=question.id,
                    a=round(a, 4),
                    b=round(b, 3),
                    response_count=len(responses),
                    calibration_method="p_value_logit",
                    calibrated_at=datetime.now(UTC),
                )
                items_calibrated += 1
            except Exception as e:
                errors.append(f"Question {question.id}: {e}")

        return CalibrationResultOut(
            items_calibrated=items_calibrated,
            items_skipped=items_skipped,
            errors=errors,
        )

    # --- Private helpers ---

    async def _get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamSession:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError("Session not found")
        if session.user_id != user_id:
            raise ForbiddenError("This is not your session")
        return session

    def _require_in_progress(self, session: ExamSession) -> None:
        if session.status != "in_progress":
            raise ValidationError(
                f"Session is not in progress (status: {session.status})"
            )

    def _check_expired(self, session: ExamSession) -> None:
        if session.expires_at is not None and datetime.now(UTC) > session.expires_at:
            raise ValidationError("Session has expired")

    async def _get_item_params(
        self, question_ids: list[uuid.UUID]
    ) -> list[ItemParams]:
        """Get IRT params for questions, falling back to defaults."""
        db_params = await self.item_param_repo.get_by_question_ids(question_ids)
        params_map = {p.question_id: p for p in db_params}

        result: list[ItemParams] = []
        for qid in question_ids:
            if qid in params_map:
                p = params_map[qid]
                result.append(ItemParams(
                    item_id=str(qid),
                    a=float(p.a),
                    b=float(p.b),
                ))
            else:
                # Fall back to question's own difficulty/discrimination
                question = await self.question_repo.get_by_id(qid)
                a = float(question.discrimination or 1.0) if question else 1.0
                b = float(question.difficulty or 0.0) if question else 0.0
                result.append(ItemParams(item_id=str(qid), a=max(0.1, a), b=b))

        return result

    async def _get_single_item_params(
        self, question: QuestionItem
    ) -> ItemParams:
        """Get IRT params for a single question."""
        db_param = await self.item_param_repo.get_by_question_id(question.id)
        if db_param is not None:
            return ItemParams(
                item_id=str(question.id),
                a=float(db_param.a),
                b=float(db_param.b),
            )
        a = max(0.1, float(question.discrimination or 1.0))
        b = float(question.difficulty or 0.0)
        return ItemParams(item_id=str(question.id), a=a, b=b)

    async def _build_response_tuples(
        self, history: list[Any]
    ) -> list[tuple[float, float, float]]:
        """Build (a, b, correct) tuples from theta history entries."""
        tuples: list[tuple[float, float, float]] = []
        for h in history:
            question = await self.question_repo.get_by_id(h.question_id)
            if question is None:
                continue
            ip = await self._get_single_item_params(question)
            tuples.append((ip.a, ip.b, 1.0 if h.is_correct else 0.0))
        return tuples

    def _compute_se(
        self, theta: float, history: list[Any]
    ) -> float:
        """Compute SE from history entries (approximate without DB lookups)."""
        if not history:
            return 10.0
        # Use stored information values
        total_info = sum(
            float(h.information or 0.0) for h in history
        )
        if total_info < 1e-15:
            return 10.0
        return 1.0 / math.sqrt(total_info)
