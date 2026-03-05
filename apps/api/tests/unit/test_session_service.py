import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.exams.models import ExamTemplate
from src.questions.models import QuestionItem
from src.sessions.models import ExamSession
from src.sessions.service import SessionService


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_db: AsyncMock) -> SessionService:
    return SessionService(mock_db)


def _make_template(
    is_published: bool = True,
    time_limit_minutes: int | None = None,
    shuffle_questions: bool = False,
) -> ExamTemplate:
    t = ExamTemplate()
    t.id = uuid.uuid4()
    t.title = "Test Exam"
    t.is_published = is_published
    t.time_limit_minutes = time_limit_minutes
    t.shuffle_questions = shuffle_questions
    return t


def _make_question(template_id: uuid.UUID) -> QuestionItem:
    q = QuestionItem()
    q.id = uuid.uuid4()
    q.template_id = template_id
    q.question_type = "mcq"
    q.stem = "Test?"
    return q


def _make_session(
    user_id: uuid.UUID,
    template_id: uuid.UUID,
    status: str = "created",
) -> ExamSession:
    s = ExamSession()
    s.id = uuid.uuid4()
    s.user_id = user_id
    s.template_id = template_id
    s.status = status
    s.expires_at = None
    return s


@pytest.mark.asyncio
async def test_create_session_unpublished_template_raises(
    service: SessionService,
) -> None:
    template = _make_template(is_published=False)
    with (
        patch.object(service.template_repo, "get_by_id", return_value=template),
        pytest.raises(ValidationError, match="unpublished"),
    ):
        await service.create_session(template.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_create_session_template_not_found_raises(
    service: SessionService,
) -> None:
    with (
        patch.object(service.template_repo, "get_by_id", return_value=None),
        pytest.raises(NotFoundError),
    ):
        await service.create_session(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_create_session_no_questions_raises(
    service: SessionService,
) -> None:
    template = _make_template()
    with (
        patch.object(service.template_repo, "get_by_id", return_value=template),
        patch.object(service.question_repo, "list_by_template", return_value=([], 0)),
        pytest.raises(ValidationError, match="no active questions"),
    ):
        await service.create_session(template.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_create_session_success(service: SessionService) -> None:
    template = _make_template()
    q = _make_question(template.id)
    user_id = uuid.uuid4()
    session = _make_session(user_id, template.id)

    with (
        patch.object(service.template_repo, "get_by_id", return_value=template),
        patch.object(service.question_repo, "list_by_template", return_value=([q], 1)),
        patch.object(service.session_repo, "create", return_value=session),
    ):
        result = await service.create_session(template.id, user_id)
        assert result.id == session.id


@pytest.mark.asyncio
async def test_start_session_wrong_status_raises(
    service: SessionService,
) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="in_progress")

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        pytest.raises(ValidationError, match="Cannot start"),
    ):
        await service.start_session(session.id, user_id)


@pytest.mark.asyncio
async def test_start_session_sets_time_limit(
    service: SessionService,
) -> None:
    user_id = uuid.uuid4()
    template = _make_template(time_limit_minutes=60)
    session = _make_session(user_id, template.id, status="created")

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.template_repo, "get_by_id", return_value=template),
        patch.object(service.session_repo, "update", return_value=session) as mock_update,
    ):
        await service.start_session(session.id, user_id)
        call_kwargs = mock_update.call_args
        assert call_kwargs is not None
        assert "expires_at" in call_kwargs.kwargs


@pytest.mark.asyncio
async def test_submit_session_wrong_status_raises(
    service: SessionService,
) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="submitted")

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        pytest.raises(ValidationError, match="Cannot submit"),
    ):
        await service.submit_session(session.id, user_id)


@pytest.mark.asyncio
async def test_submit_session_success(service: SessionService) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="in_progress")

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.session_repo, "update", return_value=session),
    ):
        result = await service.submit_session(session.id, user_id)
        assert result.id == session.id


# --- Resume ---


@pytest.mark.asyncio
async def test_resume_in_progress_session(service: SessionService) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="in_progress")
    session.integrity_log = []

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.response_repo, "list_by_session", return_value=[]),
    ):
        result_session, responses = await service.resume_session(
            session.id, user_id
        )
        assert result_session.id == session.id
        assert responses == []


@pytest.mark.asyncio
async def test_resume_created_session_starts_it(
    service: SessionService,
) -> None:
    user_id = uuid.uuid4()
    template = _make_template(time_limit_minutes=60)
    session = _make_session(user_id, template.id, status="created")
    session.integrity_log = []

    started_session = _make_session(user_id, template.id, status="in_progress")
    started_session.id = session.id
    started_session.expires_at = None
    started_session.integrity_log = []

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.template_repo, "get_by_id", return_value=template),
        patch.object(
            service.session_repo, "update", return_value=started_session
        ),
        patch.object(service.response_repo, "list_by_session", return_value=[]),
    ):
        result_session, _responses = await service.resume_session(
            session.id, user_id
        )
        assert result_session.status == "in_progress"


@pytest.mark.asyncio
async def test_resume_submitted_session_raises(
    service: SessionService,
) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="submitted")

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        pytest.raises(ValidationError, match="Cannot resume"),
    ):
        await service.resume_session(session.id, user_id)


# --- Heartbeat ---


@pytest.mark.asyncio
async def test_heartbeat_returns_session(service: SessionService) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="in_progress")

    with patch.object(service.session_repo, "get_by_id", return_value=session):
        result = await service.heartbeat(session.id, user_id)
        assert result.status == "in_progress"


@pytest.mark.asyncio
async def test_heartbeat_auto_submits_expired(
    service: SessionService,
) -> None:
    from datetime import UTC, datetime, timedelta

    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="in_progress")
    session.expires_at = datetime.now(UTC) - timedelta(minutes=5)

    submitted_session = _make_session(user_id, session.template_id, status="submitted")
    submitted_session.id = session.id

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(
            service.session_repo, "update", return_value=submitted_session
        ),
    ):
        result = await service.heartbeat(session.id, user_id)
        assert result.status == "submitted"


# --- Integrity Logging ---


@pytest.mark.asyncio
async def test_log_integrity_events(service: SessionService) -> None:
    from src.sessions.schemas import IntegrityEvent

    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="in_progress")
    session.integrity_log = []

    events = [
        IntegrityEvent(event_type="tab_switch", details={"count": 1}),
        IntegrityEvent(event_type="focus_loss"),
    ]

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.session_repo, "update", return_value=session) as mock_update,
    ):
        await service.log_integrity_events(session.id, user_id, events)
        call_kwargs = mock_update.call_args
        assert call_kwargs is not None
        log = call_kwargs.kwargs.get("integrity_log", [])
        assert len(log) == 2
        assert log[0]["event_type"] == "tab_switch"
        assert log[1]["event_type"] == "focus_loss"


@pytest.mark.asyncio
async def test_log_integrity_not_in_progress_ignored(
    service: SessionService,
) -> None:
    from src.sessions.schemas import IntegrityEvent

    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4(), status="submitted")

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.session_repo, "update") as mock_update,
    ):
        await service.log_integrity_events(
            session.id,
            user_id,
            [IntegrityEvent(event_type="tab_switch")],
        )
        mock_update.assert_not_called()
