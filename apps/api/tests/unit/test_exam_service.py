import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.core.exceptions import ForbiddenError, NotFoundError
from src.exams.models import ExamTemplate
from src.exams.schemas import ExamTemplateCreate, ExamTemplateUpdate
from src.exams.service import ExamTemplateService


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_db: AsyncMock) -> ExamTemplateService:
    return ExamTemplateService(mock_db)


def _make_template(
    created_by: uuid.UUID | None = None,
    is_published: bool = False,
) -> ExamTemplate:
    t = ExamTemplate()
    t.id = uuid.uuid4()
    t.title = "Test Exam"
    t.locale = "tr-TR"
    t.exam_mode = "mock"
    t.is_published = is_published
    t.created_by = created_by or uuid.uuid4()
    t.shuffle_questions = False
    t.shuffle_options = False
    return t


@pytest.mark.asyncio
async def test_get_template_not_found(service: ExamTemplateService) -> None:
    with (
        patch.object(service.repo, "get_by_id", return_value=None),
        pytest.raises(NotFoundError),
    ):
        await service.get_template(uuid.uuid4())


@pytest.mark.asyncio
async def test_get_template_success(service: ExamTemplateService) -> None:
    template = _make_template()
    with patch.object(service.repo, "get_by_id", return_value=template):
        result = await service.get_template(template.id)
        assert result.id == template.id


@pytest.mark.asyncio
async def test_create_template(service: ExamTemplateService) -> None:
    user_id = uuid.uuid4()
    template = _make_template(created_by=user_id)
    data = ExamTemplateCreate(title="New Exam")

    with patch.object(service.repo, "create", return_value=template):
        result = await service.create_template(data, user_id)
        assert result.id == template.id


@pytest.mark.asyncio
async def test_update_template_forbidden_for_other_user(
    service: ExamTemplateService,
) -> None:
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    template = _make_template(created_by=owner_id)
    data = ExamTemplateUpdate(title="Updated")

    with (
        patch.object(service.repo, "get_by_id", return_value=template),
        pytest.raises(ForbiddenError),
    ):
        await service.update_template(
            template.id, data, other_id, "instructor"
        )


@pytest.mark.asyncio
async def test_update_template_allowed_for_admin(
    service: ExamTemplateService,
) -> None:
    owner_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    template = _make_template(created_by=owner_id)
    data = ExamTemplateUpdate(title="Updated")

    with (
        patch.object(service.repo, "get_by_id", return_value=template),
        patch.object(service.repo, "update", return_value=template),
    ):
        result = await service.update_template(
            template.id, data, admin_id, "admin"
        )
        assert result.id == template.id


@pytest.mark.asyncio
async def test_delete_published_template_forbidden(
    service: ExamTemplateService,
) -> None:
    owner_id = uuid.uuid4()
    template = _make_template(created_by=owner_id, is_published=True)

    with (
        patch.object(service.repo, "get_by_id", return_value=template),
        pytest.raises(ForbiddenError, match="published"),
    ):
        await service.delete_template(template.id, owner_id, "instructor")


@pytest.mark.asyncio
async def test_publish_template_success(
    service: ExamTemplateService,
) -> None:
    owner_id = uuid.uuid4()
    template = _make_template(created_by=owner_id)

    with (
        patch.object(service.repo, "get_by_id", return_value=template),
        patch.object(service.repo, "update", return_value=template),
    ):
        result = await service.publish_template(
            template.id, owner_id, "instructor"
        )
        assert result.id == template.id
