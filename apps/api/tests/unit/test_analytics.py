"""Tests for analytics service (unit-level with mocked DB queries)."""

import statistics
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.analytics.schemas import (
    ScoreBucket,
)
from src.analytics.service import AnalyticsService


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_db: AsyncMock) -> AnalyticsService:
    return AnalyticsService(mock_db)


def _make_session(
    template_id: uuid.UUID,
    percentage: float | None = None,
    passed: bool | None = None,
    status: str = "graded",
) -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.template_id = template_id
    s.user_id = uuid.uuid4()
    s.status = status
    s.percentage = percentage
    s.passed = passed
    s.total_score = percentage
    s.max_score = 100.0
    s.theta = None
    s.started_at = datetime.now(UTC) - timedelta(hours=1)
    s.submitted_at = datetime.now(UTC)
    return s


# --- Score Distribution ---


class TestScoreDistribution:
    @pytest.mark.asyncio
    async def test_empty_sessions(self, service: AnalyticsService) -> None:
        """No sessions should return zeroed distribution."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.score_distribution(uuid.uuid4())
        assert result.total_sessions == 0
        assert result.graded_sessions == 0
        assert result.mean_score is None
        assert result.distribution == []

    @pytest.mark.asyncio
    async def test_with_graded_sessions(self, service: AnalyticsService) -> None:
        """Graded sessions should produce valid stats."""
        template_id = uuid.uuid4()
        sessions = [
            _make_session(template_id, percentage=80.0, passed=True),
            _make_session(template_id, percentage=60.0, passed=True),
            _make_session(template_id, percentage=40.0, passed=False),
            _make_session(template_id, percentage=90.0, passed=True),
            _make_session(template_id, percentage=50.0, passed=False),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sessions
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.score_distribution(template_id)
        assert result.total_sessions == 5
        assert result.graded_sessions == 5
        assert result.mean_score == round(statistics.mean([80, 60, 40, 90, 50]), 2)
        assert result.median_score == round(statistics.median([80, 60, 40, 90, 50]), 2)
        assert result.pass_rate == 60.0  # 3 out of 5
        assert len(result.distribution) == 10  # default 10 buckets

    @pytest.mark.asyncio
    async def test_single_session_zero_stddev(self, service: AnalyticsService) -> None:
        """Single session should have stddev = 0."""
        template_id = uuid.uuid4()
        sessions = [_make_session(template_id, percentage=75.0, passed=True)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sessions
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.score_distribution(template_id)
        assert result.std_dev == 0.0

    @pytest.mark.asyncio
    async def test_bucket_count(self, service: AnalyticsService) -> None:
        """Custom bucket count should be respected."""
        template_id = uuid.uuid4()
        sessions = [
            _make_session(template_id, percentage=float(i * 10), passed=i >= 7)
            for i in range(1, 11)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sessions
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.score_distribution(template_id, bucket_count=5)
        assert len(result.distribution) == 5


# --- Score Bucket Validation ---


class TestScoreBucket:
    def test_bucket_model(self) -> None:
        bucket = ScoreBucket(range_start=0.0, range_end=10.0, count=5)
        assert bucket.range_start == 0.0
        assert bucket.range_end == 10.0
        assert bucket.count == 5


# --- Item Analysis (integration patterns) ---


class TestItemAnalysis:
    @pytest.mark.asyncio
    async def test_empty_template(self, service: AnalyticsService) -> None:
        """No questions should return empty item list."""
        # Mock: first call for questions, second for each grade query
        mock_q_result = MagicMock()
        mock_q_result.scalars.return_value.all.return_value = []
        service.db.execute = AsyncMock(return_value=mock_q_result)

        result = await service.item_analysis(uuid.uuid4())
        assert result.total_items == 0
        assert result.items == []


# --- Topic Mastery ---


class TestTopicMastery:
    @pytest.mark.asyncio
    async def test_no_sessions(self, service: AnalyticsService) -> None:
        """No sessions should return empty mastery."""
        mock_q_result = MagicMock()
        mock_q_result.scalars.return_value.all.return_value = []
        mock_sess_result = MagicMock()
        mock_sess_result.all.return_value = []

        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_q_result
            return mock_sess_result

        service.db.execute = mock_execute

        result = await service.topic_mastery(uuid.uuid4())
        assert result.mastery == []


# --- AI Costs ---


class TestAICosts:
    @pytest.mark.asyncio
    async def test_no_traces(self, service: AnalyticsService) -> None:
        """No traces should return zero costs."""
        mock_result = MagicMock()
        mock_result.all.return_value = []

        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.ai_costs()
        assert result.total_cost_usd == 0.0
        assert result.total_calls == 0
        assert result.by_task == []
        assert result.by_provider == []


# --- Performance Over Time ---


class TestPerformanceOverTime:
    @pytest.mark.asyncio
    async def test_no_data(self, service: AnalyticsService) -> None:
        """No submitted sessions should return empty points."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        service.db.execute = AsyncMock(return_value=mock_result)

        result = await service.performance_over_time()
        assert result.points == []


# --- Dashboard ---


class TestDashboard:
    @pytest.mark.asyncio
    async def test_empty_dashboard(self, service: AnalyticsService) -> None:
        """Empty state should return zeroed dashboard."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_scalar = MagicMock()
        mock_scalar.one.return_value = (None, 0)
        mock_scalar_one = MagicMock()
        mock_scalar_one.scalar_one.return_value = 0

        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            # Different responses for different queries
            if call_count == 1:
                return mock_result  # status counts
            if call_count == 2:
                return mock_scalar  # avg percentage
            if call_count == 3:
                return mock_scalar_one  # pass count
            return mock_result

        service.db.execute = mock_execute

        result = await service.dashboard()
        assert result.session_summary.total_sessions == 0
