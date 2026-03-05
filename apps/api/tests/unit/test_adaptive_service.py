import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.adaptive.schemas import NextQuestionOut, NoMoreQuestions
from src.adaptive.service import AdaptiveService
from src.core.exceptions import NotFoundError, ValidationError
from src.exams.models import ExamTemplate
from src.questions.models import QuestionItem
from src.sessions.models import ExamSession


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_db: AsyncMock) -> AdaptiveService:
    return AdaptiveService(mock_db)


def _make_template(
    is_published: bool = True,
    time_limit_minutes: int | None = 90,
    settings: dict | None = None,
) -> ExamTemplate:
    t = ExamTemplate()
    t.id = uuid.uuid4()
    t.title = "Test Exam"
    t.is_published = is_published
    t.time_limit_minutes = time_limit_minutes
    t.shuffle_questions = False
    t.settings = settings or {}
    return t


def _make_question(
    template_id: uuid.UUID,
    question_type: str = "mcq",
    difficulty: float | None = 0.0,
    discrimination: float | None = 1.0,
) -> QuestionItem:
    q = QuestionItem()
    q.id = uuid.uuid4()
    q.template_id = template_id
    q.question_type = question_type
    q.stem = "Test?"
    q.options = [{"key": "A", "text": "Yes"}, {"key": "B", "text": "No"}]
    q.correct_answer = {"key": "A"}
    q.difficulty = difficulty
    q.discrimination = discrimination
    q.is_active = True
    return q


def _make_session(
    user_id: uuid.UUID,
    template_id: uuid.UUID,
    status: str = "in_progress",
    theta: float = 0.0,
    eligible_ids: list[str] | None = None,
) -> ExamSession:
    s = ExamSession()
    s.id = uuid.uuid4()
    s.user_id = user_id
    s.template_id = template_id
    s.status = status
    s.theta = theta
    s.expires_at = None
    s.session_metadata = {
        "adaptive": True,
        "max_items": 40,
        "min_items": 5,
        "se_threshold": 0.30,
        "eligible_question_ids": eligible_ids or [],
    }
    return s


# --- create_session ---


@pytest.mark.asyncio
async def test_create_session_unpublished_raises(service: AdaptiveService) -> None:
    template = _make_template(is_published=False)
    with (
        patch.object(service.template_repo, "get_by_id", return_value=template),
        pytest.raises(ValidationError, match="unpublished"),
    ):
        await service.create_session(template.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_create_session_not_found_raises(service: AdaptiveService) -> None:
    with (
        patch.object(service.template_repo, "get_by_id", return_value=None),
        pytest.raises(NotFoundError),
    ):
        await service.create_session(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_create_session_no_adaptive_questions_raises(
    service: AdaptiveService,
) -> None:
    template = _make_template()
    # Only long_form questions
    q = _make_question(template.id, question_type="long_form")
    with (
        patch.object(service.template_repo, "get_by_id", return_value=template),
        patch.object(
            service.question_repo, "list_by_template", return_value=([q], 1)
        ),
        pytest.raises(ValidationError, match="suitable for adaptive"),
    ):
        await service.create_session(template.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_create_session_success(service: AdaptiveService) -> None:
    template = _make_template()
    q1 = _make_question(template.id, question_type="mcq")
    q2 = _make_question(template.id, question_type="true_false")
    user_id = uuid.uuid4()

    session = _make_session(user_id, template.id, eligible_ids=[str(q1.id), str(q2.id)])

    with (
        patch.object(service.template_repo, "get_by_id", return_value=template),
        patch.object(
            service.question_repo, "list_by_template", return_value=([q1, q2], 2)
        ),
        patch.object(service.session_repo, "create", return_value=session),
    ):
        result = await service.create_session(template.id, user_id)
        assert result.session_id == session.id
        assert result.items_administered == 0


# --- get_next_question ---


@pytest.mark.asyncio
async def test_next_question_returns_question(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    q = _make_question(template_id)
    session = _make_session(user_id, template_id, eligible_ids=[str(q.id)])

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.theta_repo, "list_by_session", return_value=[]),
        patch.object(
            service.item_param_repo, "get_by_question_ids", return_value=[]
        ),
        patch.object(service.question_repo, "get_by_id", return_value=q),
    ):
        result = await service.get_next_question(session.id, user_id)
        assert isinstance(result, NextQuestionOut)
        assert result.question_id == q.id
        assert result.step == 1


@pytest.mark.asyncio
async def test_next_question_max_items_reached(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    session = _make_session(user_id, template_id)
    session.session_metadata["max_items"] = 2

    # Simulate 2 items already administered
    mock_history = [AsyncMock(question_id=uuid.uuid4()) for _ in range(2)]

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(
            service.theta_repo, "list_by_session", return_value=mock_history
        ),
    ):
        result = await service.get_next_question(session.id, user_id)
        assert isinstance(result, NoMoreQuestions)
        assert result.finish_reason == "max_items_reached"


@pytest.mark.asyncio
async def test_next_question_no_remaining_items(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    q_id = uuid.uuid4()
    session = _make_session(user_id, template_id, eligible_ids=[str(q_id)])
    session.session_metadata["min_items"] = 0

    # The only eligible question was already answered
    mock_history = [AsyncMock(question_id=q_id, information=0.25)]

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(
            service.theta_repo, "list_by_session", return_value=mock_history
        ),
    ):
        result = await service.get_next_question(session.id, user_id)
        assert isinstance(result, NoMoreQuestions)
        assert result.finish_reason == "no_items_remaining"


# --- respond ---


@pytest.mark.asyncio
async def test_respond_correct_answer(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    q = _make_question(template_id, question_type="mcq")
    session = _make_session(
        user_id, template_id, eligible_ids=[str(q.id)]
    )

    mock_response = AsyncMock()
    mock_theta_entry = AsyncMock()

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.question_repo, "get_by_id", return_value=q),
        patch.object(service.theta_repo, "list_by_session", return_value=[]),
        patch.object(
            service.item_param_repo, "get_by_question_id", return_value=None
        ),
        patch.object(
            service.response_repo, "upsert", return_value=mock_response
        ),
        patch.object(
            service.theta_repo, "create", return_value=mock_theta_entry
        ),
        patch.object(
            service.session_repo, "update", return_value=session
        ),
    ):
        result = await service.respond(
            session.id, user_id, q.id, {"key": "A"}
        )
        assert result.is_correct is True
        assert result.step == 1
        assert isinstance(result.theta, float)


@pytest.mark.asyncio
async def test_respond_incorrect_answer(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    q = _make_question(template_id, question_type="mcq")
    session = _make_session(
        user_id, template_id, eligible_ids=[str(q.id)]
    )

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.question_repo, "get_by_id", return_value=q),
        patch.object(service.theta_repo, "list_by_session", return_value=[]),
        patch.object(
            service.item_param_repo, "get_by_question_id", return_value=None
        ),
        patch.object(service.response_repo, "upsert", return_value=AsyncMock()),
        patch.object(service.theta_repo, "create", return_value=AsyncMock()),
        patch.object(service.session_repo, "update", return_value=session),
    ):
        result = await service.respond(
            session.id, user_id, q.id, {"key": "B"}
        )
        assert result.is_correct is False


@pytest.mark.asyncio
async def test_respond_duplicate_question_raises(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    q = _make_question(template_id)
    session = _make_session(user_id, template_id, eligible_ids=[str(q.id)])

    # Question already in history
    mock_h = AsyncMock(question_id=q.id)

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.question_repo, "get_by_id", return_value=q),
        patch.object(
            service.theta_repo, "list_by_session", return_value=[mock_h]
        ),
        pytest.raises(ValidationError, match="already answered"),
    ):
        await service.respond(session.id, user_id, q.id, {"key": "A"})


@pytest.mark.asyncio
async def test_respond_non_deterministic_type_raises(
    service: AdaptiveService,
) -> None:
    user_id = uuid.uuid4()
    template_id = uuid.uuid4()
    q = _make_question(template_id, question_type="long_form")
    session = _make_session(user_id, template_id)

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.question_repo, "get_by_id", return_value=q),
        patch.object(service.theta_repo, "list_by_session", return_value=[]),
        pytest.raises(ValidationError, match="Cannot grade"),
    ):
        await service.respond(
            session.id, user_id, q.id, {"text": "answer"}
        )


# --- get_theta ---


@pytest.mark.asyncio
async def test_get_theta_empty_history(service: AdaptiveService) -> None:
    user_id = uuid.uuid4()
    session = _make_session(user_id, uuid.uuid4())

    with (
        patch.object(service.session_repo, "get_by_id", return_value=session),
        patch.object(service.theta_repo, "list_by_session", return_value=[]),
    ):
        result = await service.get_theta(session.id, user_id)
        assert result.session_id == session.id
        assert result.history == []
        assert result.current_se is None
