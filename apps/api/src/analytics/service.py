from __future__ import annotations

import statistics
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.models import ModelTrace
from src.analytics.schemas import (
    AICostByProvider,
    AICostByTask,
    AICostOut,
    DashboardOut,
    ItemAnalysis,
    ItemAnalysisOut,
    PerformanceOverTimeOut,
    PerformancePoint,
    ScoreBucket,
    ScoreDistributionOut,
    SessionSummary,
    TopicMastery,
    TopicMasteryOut,
)
from src.grading.models import Grade
from src.questions.models import QuestionItem
from src.sessions.models import ExamSession, Response


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Score Distribution ───────────────────────────────────────────

    async def score_distribution(
        self,
        template_id: uuid.UUID,
        bucket_count: int = 10,
    ) -> ScoreDistributionOut:
        """Compute score distribution for graded sessions of a template."""
        stmt = select(ExamSession).where(
            ExamSession.template_id == template_id,
            ExamSession.status.in_(["submitted", "graded"]),
        )
        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())

        total = len(sessions)
        graded = [s for s in sessions if s.percentage is not None]
        percentages = [float(s.percentage) for s in graded if s.percentage is not None]

        distribution: list[ScoreBucket] = []
        mean_score: float | None = None
        median_score: float | None = None
        std_dev: float | None = None
        min_score: float | None = None
        max_score: float | None = None
        pass_rate: float | None = None

        if percentages:
            mean_score = round(statistics.mean(percentages), 2)
            median_score = round(statistics.median(percentages), 2)
            std_dev = (
                round(statistics.stdev(percentages), 2)
                if len(percentages) > 1
                else 0.0
            )
            min_score = round(min(percentages), 2)
            max_score = round(max(percentages), 2)

            passed = [s for s in graded if s.passed]
            pass_rate = round(len(passed) / len(graded) * 100, 2)

            # Build histogram buckets
            step = 100.0 / bucket_count
            for i in range(bucket_count):
                lo = round(i * step, 1)
                hi = round((i + 1) * step, 1)
                is_last = i == bucket_count - 1
                count = sum(
                    1 for p in percentages
                    if lo <= p < hi or (is_last and p == hi)
                )
                distribution.append(ScoreBucket(range_start=lo, range_end=hi, count=count))

        return ScoreDistributionOut(
            template_id=template_id,
            total_sessions=total,
            graded_sessions=len(graded),
            mean_score=mean_score,
            median_score=median_score,
            std_dev=std_dev,
            min_score=min_score,
            max_score=max_score,
            pass_rate=pass_rate,
            distribution=distribution,
        )

    # ── Item Analysis ────────────────────────────────────────────────

    async def item_analysis(
        self, template_id: uuid.UUID
    ) -> ItemAnalysisOut:
        """Compute per-item difficulty and discrimination stats."""
        # Load questions
        q_stmt = select(QuestionItem).where(
            QuestionItem.template_id == template_id,
            QuestionItem.is_active.is_(True),
        )
        q_result = await self.db.execute(q_stmt)
        questions = list(q_result.scalars().all())

        items: list[ItemAnalysis] = []

        for question in questions:
            # Get all grades for this question across sessions
            grade_stmt = (
                select(Grade, Response)
                .join(Response, Grade.response_id == Response.id)
                .where(Response.question_id == question.id)
            )
            grade_result = await self.db.execute(grade_stmt)
            rows = grade_result.all()

            response_count = len(rows)
            correct_count = sum(
                1 for g, _ in rows if g.is_correct is True
            )
            scores = [float(g.score) for g, _ in rows]
            max_scores = [float(g.max_score) for g, _ in rows]

            p_value = correct_count / response_count if response_count > 0 else 0.0
            mean_score = round(statistics.mean(scores), 2) if scores else None
            max_score_val = max(max_scores) if max_scores else None

            items.append(
                ItemAnalysis(
                    question_id=question.id,
                    stem_preview=question.stem[:120],
                    question_type=question.question_type,
                    topic=question.topic,
                    response_count=response_count,
                    correct_count=correct_count,
                    p_value=round(p_value, 4),
                    discrimination=(
                        float(question.discrimination)
                        if question.discrimination
                        else None
                    ),
                    mean_score=mean_score,
                    max_score=max_score_val,
                )
            )

        # Sort by p_value ascending (hardest first)
        items.sort(key=lambda x: x.p_value)

        return ItemAnalysisOut(
            template_id=template_id,
            total_items=len(items),
            items=items,
        )

    # ── Topic Mastery (aggregate) ────────────────────────────────────

    async def topic_mastery(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> TopicMasteryOut:
        """Compute topic mastery rates. If user_id given, per-student; else aggregate."""
        # Get questions with topics
        q_stmt = select(QuestionItem).where(
            QuestionItem.template_id == template_id,
            QuestionItem.is_active.is_(True),
            QuestionItem.topic.isnot(None),
        )
        q_result = await self.db.execute(q_stmt)
        questions = list(q_result.scalars().all())

        topic_questions: dict[str, list[uuid.UUID]] = {}
        for q in questions:
            if q.topic:
                topic_questions.setdefault(q.topic, []).append(q.id)

        # Filter sessions
        sess_filter: list[Any] = [
            ExamSession.template_id == template_id,
            ExamSession.status.in_(["submitted", "graded"]),
        ]
        if user_id:
            sess_filter.append(ExamSession.user_id == user_id)

        sess_stmt = select(ExamSession.id).where(*sess_filter)
        sess_result = await self.db.execute(sess_stmt)
        session_ids = [row[0] for row in sess_result.all()]

        if not session_ids:
            return TopicMasteryOut(template_id=template_id, mastery=[])

        # Get grades for these sessions
        grade_stmt = (
            select(Response.question_id, Grade.is_correct)
            .join(Grade, Grade.response_id == Response.id)
            .where(Response.session_id.in_(session_ids))
        )
        grade_result = await self.db.execute(grade_stmt)
        grade_rows = grade_result.all()

        # Map question_id -> list of correct booleans
        q_results: dict[uuid.UUID, list[bool]] = {}
        for qid, is_correct in grade_rows:
            q_results.setdefault(qid, []).append(bool(is_correct))

        mastery_list: list[TopicMastery] = []
        for topic, q_ids in sorted(topic_questions.items()):
            response_count = 0
            correct_count = 0
            for qid in q_ids:
                results = q_results.get(qid, [])
                response_count += len(results)
                correct_count += sum(results)

            mastery_rate = correct_count / response_count if response_count > 0 else 0.0
            mastery_list.append(
                TopicMastery(
                    topic=topic,
                    question_count=len(q_ids),
                    response_count=response_count,
                    correct_count=correct_count,
                    mastery_rate=round(mastery_rate, 4),
                )
            )

        return TopicMasteryOut(template_id=template_id, mastery=mastery_list)

    # ── Performance Over Time ────────────────────────────────────────

    async def performance_over_time(
        self,
        template_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        days: int = 30,
    ) -> PerformanceOverTimeOut:
        """Daily aggregation of session scores."""
        since = datetime.now(UTC) - timedelta(days=days)

        filters: list[Any] = [
            ExamSession.status.in_(["submitted", "graded"]),
            ExamSession.submitted_at >= since,
            ExamSession.percentage.isnot(None),
        ]
        if template_id:
            filters.append(ExamSession.template_id == template_id)
        if user_id:
            filters.append(ExamSession.user_id == user_id)

        stmt = select(
            func.date_trunc("day", ExamSession.submitted_at).label("day"),
            func.count().label("cnt"),
            func.avg(ExamSession.percentage).label("avg_pct"),
        ).where(*filters).group_by("day").order_by("day")

        result = await self.db.execute(stmt)
        rows = result.all()

        points = [
            PerformancePoint(
                date=row.day.date().isoformat() if row.day else "",
                session_count=row.cnt,
                mean_percentage=round(float(row.avg_pct), 2) if row.avg_pct else None,
            )
            for row in rows
        ]

        return PerformanceOverTimeOut(
            template_id=template_id,
            points=points,
        )

    # ── AI Cost Tracking ─────────────────────────────────────────────

    async def ai_costs(
        self,
        template_id: uuid.UUID | None = None,
        days: int | None = None,
    ) -> AICostOut:
        """Aggregate AI costs by task type and provider."""
        filters: list[Any] = []
        period_start: datetime | None = None
        period_end: datetime | None = None

        if template_id:
            filters.append(ModelTrace.template_id == template_id)
        if days:
            period_start = datetime.now(UTC) - timedelta(days=days)
            period_end = datetime.now(UTC)
            filters.append(ModelTrace.created_at >= period_start)

        # By task type
        task_stmt = select(
            ModelTrace.task_type,
            func.count().label("cnt"),
            func.coalesce(
                func.sum(ModelTrace.input_tokens + ModelTrace.output_tokens), 0
            ).label("tokens"),
            func.coalesce(func.sum(ModelTrace.cost_usd), 0).label("cost"),
            func.avg(ModelTrace.latency_ms).label("avg_latency"),
        ).where(*filters).group_by(ModelTrace.task_type)

        task_result = await self.db.execute(task_stmt)
        by_task = [
            AICostByTask(
                task_type=row.task_type,
                call_count=row.cnt,
                total_tokens=int(row.tokens),
                total_cost_usd=round(float(row.cost), 6),
                avg_latency_ms=round(float(row.avg_latency), 1) if row.avg_latency else None,
            )
            for row in task_result.all()
        ]

        # By provider + model
        prov_stmt = select(
            ModelTrace.provider,
            ModelTrace.model,
            func.count().label("cnt"),
            func.coalesce(
                func.sum(ModelTrace.input_tokens + ModelTrace.output_tokens), 0
            ).label("tokens"),
            func.coalesce(func.sum(ModelTrace.cost_usd), 0).label("cost"),
        ).where(*filters).group_by(ModelTrace.provider, ModelTrace.model)

        prov_result = await self.db.execute(prov_stmt)
        by_provider = [
            AICostByProvider(
                provider=row.provider,
                model=row.model,
                call_count=row.cnt,
                total_tokens=int(row.tokens),
                total_cost_usd=round(float(row.cost), 6),
            )
            for row in prov_result.all()
        ]

        total_cost = sum(t.total_cost_usd for t in by_task)
        total_calls = sum(t.call_count for t in by_task)

        return AICostOut(
            period_start=period_start,
            period_end=period_end,
            total_cost_usd=round(total_cost, 6),
            total_calls=total_calls,
            by_task=by_task,
            by_provider=by_provider,
        )

    # ── Dashboard ────────────────────────────────────────────────────

    async def dashboard(
        self,
        template_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> DashboardOut:
        """Aggregated dashboard data."""
        # Session summary
        filters: list[Any] = []
        if template_id:
            filters.append(ExamSession.template_id == template_id)
        if user_id:
            filters.append(ExamSession.user_id == user_id)

        count_stmt = select(
            ExamSession.status,
            func.count().label("cnt"),
        ).where(*filters).group_by(ExamSession.status)

        count_result = await self.db.execute(count_stmt)
        status_counts: dict[str, int] = {}
        for row in count_result.all():
            status_counts[row.status] = row.cnt

        total = sum(status_counts.values())

        # Avg percentage and pass rate for graded
        graded_filters: list[Any] = [*filters, ExamSession.percentage.isnot(None)]
        avg_stmt = select(
            func.avg(ExamSession.percentage),
            func.count(),
        ).where(*graded_filters)
        avg_result = await self.db.execute(avg_stmt)
        avg_row = avg_result.one()
        avg_percentage = round(float(avg_row[0]), 2) if avg_row[0] else None

        pass_filters: list[Any] = [*graded_filters, ExamSession.passed.is_(True)]
        pass_stmt = select(func.count()).where(*pass_filters)
        pass_result = await self.db.execute(pass_stmt)
        pass_count = pass_result.scalar_one()
        graded_count = avg_row[1]
        pass_rate = round(pass_count / graded_count * 100, 2) if graded_count > 0 else None

        session_summary = SessionSummary(
            total_sessions=total,
            in_progress=status_counts.get("in_progress", 0),
            submitted=status_counts.get("submitted", 0),
            graded=status_counts.get("graded", 0),
            avg_percentage=avg_percentage,
            pass_rate=pass_rate,
        )

        # Recent scores (last 30 days)
        perf = await self.performance_over_time(
            template_id=template_id, user_id=user_id, days=30
        )

        # Top difficult items (lowest p_value)
        top_difficult: list[ItemAnalysis] = []
        if template_id:
            item_data = await self.item_analysis(template_id)
            top_difficult = item_data.items[:5]

        # AI costs (last 30 days)
        ai_cost = await self.ai_costs(template_id=template_id, days=30)

        return DashboardOut(
            session_summary=session_summary,
            recent_scores=perf.points,
            top_difficult_items=top_difficult,
            ai_cost_summary=ai_cost if ai_cost.total_calls > 0 else None,
        )
