import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_instructor
from src.core.database import get_db
from src.exams.schemas import (
    ExamTemplateCreate,
    ExamTemplateListResponse,
    ExamTemplateOut,
    ExamTemplateUpdate,
)
from src.exams.service import ExamTemplateService
from src.users.models import User

router = APIRouter(prefix="/templates", tags=["exam-templates"])


@router.post("", response_model=ExamTemplateOut, status_code=201)
async def create_template(
    body: ExamTemplateCreate,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ExamTemplateOut:
    service = ExamTemplateService(db)
    template = await service.create_template(body, user.id)
    return ExamTemplateOut.model_validate(template)


@router.get("", response_model=ExamTemplateListResponse)
async def list_templates(
    org_id: uuid.UUID | None = None,
    is_published: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamTemplateListResponse:
    service = ExamTemplateService(db)
    items, total = await service.list_templates(
        user_id=user.id,
        user_role=user.role,
        org_id=org_id,
        is_published=is_published,
        page=page,
        page_size=page_size,
    )
    return ExamTemplateListResponse(
        items=[ExamTemplateOut.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=ExamTemplateOut)
async def get_template(
    template_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamTemplateOut:
    service = ExamTemplateService(db)
    template = await service.get_template(template_id)
    return ExamTemplateOut.model_validate(template)


@router.patch("/{template_id}", response_model=ExamTemplateOut)
async def update_template(
    template_id: uuid.UUID,
    body: ExamTemplateUpdate,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ExamTemplateOut:
    service = ExamTemplateService(db)
    template = await service.update_template(
        template_id, body, user.id, user.role
    )
    return ExamTemplateOut.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ExamTemplateService(db)
    await service.delete_template(template_id, user.id, user.role)


@router.post("/{template_id}/publish", response_model=ExamTemplateOut)
async def publish_template(
    template_id: uuid.UUID,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ExamTemplateOut:
    service = ExamTemplateService(db)
    template = await service.publish_template(template_id, user.id, user.role)
    return ExamTemplateOut.model_validate(template)
