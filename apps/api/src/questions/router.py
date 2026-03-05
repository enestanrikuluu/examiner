import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_instructor
from src.core.database import get_db
from src.questions.schemas import (
    BulkQuestionImport,
    QuestionItemCreate,
    QuestionItemListResponse,
    QuestionItemOut,
    QuestionItemUpdate,
)
from src.questions.service import QuestionItemService
from src.users.models import User

router = APIRouter(prefix="/templates/{template_id}/questions", tags=["questions"])


@router.post("", response_model=QuestionItemOut, status_code=201)
async def create_question(
    template_id: uuid.UUID,
    body: QuestionItemCreate,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> QuestionItemOut:
    service = QuestionItemService(db)
    question = await service.create_question(
        template_id, body, user.id, user.role
    )
    return QuestionItemOut.model_validate(question)


@router.post("/bulk", response_model=list[QuestionItemOut], status_code=201)
async def bulk_import_questions(
    template_id: uuid.UUID,
    body: BulkQuestionImport,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> list[QuestionItemOut]:
    service = QuestionItemService(db)
    questions = await service.bulk_import(
        template_id, body, user.id, user.role
    )
    return [QuestionItemOut.model_validate(q) for q in questions]


@router.get("", response_model=QuestionItemListResponse)
async def list_questions(
    template_id: uuid.UUID,
    is_active: bool | None = True,
    topic: str | None = None,
    question_type: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionItemListResponse:
    service = QuestionItemService(db)
    items, total = await service.list_questions(
        template_id,
        is_active=is_active,
        topic=topic,
        question_type=question_type,
    )
    return QuestionItemListResponse(
        items=[QuestionItemOut.model_validate(q) for q in items],
        total=total,
    )


@router.get("/{question_id}", response_model=QuestionItemOut)
async def get_question(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionItemOut:
    service = QuestionItemService(db)
    question = await service.get_question(question_id)
    return QuestionItemOut.model_validate(question)


@router.patch("/{question_id}", response_model=QuestionItemOut)
async def update_question(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    body: QuestionItemUpdate,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> QuestionItemOut:
    service = QuestionItemService(db)
    question = await service.update_question(
        question_id, body, user.id, user.role
    )
    return QuestionItemOut.model_validate(question)


@router.delete("/{question_id}", status_code=204)
async def delete_question(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = QuestionItemService(db)
    await service.delete_question(question_id, user.id, user.role)
