import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ForbiddenError, NotFoundError
from src.exams.models import ExamTemplate
from src.exams.repository import ExamTemplateRepository
from src.exams.schemas import ExamTemplateCreate, ExamTemplateUpdate


class ExamTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ExamTemplateRepository(db)

    async def get_template(self, template_id: uuid.UUID) -> ExamTemplate:
        template = await self.repo.get_by_id(template_id)
        if template is None:
            raise NotFoundError("Exam template not found")
        return template

    async def list_templates(
        self,
        *,
        user_id: uuid.UUID,
        user_role: str,
        org_id: uuid.UUID | None = None,
        is_published: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExamTemplate], int]:
        if user_role == "admin":
            return await self.repo.list_templates(
                org_id=org_id, is_published=is_published,
                page=page, page_size=page_size,
            )
        elif user_role == "instructor":
            return await self.repo.list_templates(
                created_by=user_id, org_id=org_id,
                is_published=is_published,
                page=page, page_size=page_size,
            )
        else:
            return await self.repo.list_templates(
                is_published=True, org_id=org_id,
                page=page, page_size=page_size,
            )

    async def create_template(
        self, data: ExamTemplateCreate, created_by: uuid.UUID
    ) -> ExamTemplate:
        return await self.repo.create(
            **data.model_dump(exclude_unset=True),
            created_by=created_by,
        )

    async def update_template(
        self,
        template_id: uuid.UUID,
        data: ExamTemplateUpdate,
        user_id: uuid.UUID,
        user_role: str,
    ) -> ExamTemplate:
        template = await self.get_template(template_id)
        if user_role != "admin" and template.created_by != user_id:
            raise ForbiddenError("You can only edit your own templates")
        return await self.repo.update(
            template, **data.model_dump(exclude_unset=True)
        )

    async def delete_template(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str,
    ) -> None:
        template = await self.get_template(template_id)
        if user_role != "admin" and template.created_by != user_id:
            raise ForbiddenError("You can only delete your own templates")
        if template.is_published:
            raise ForbiddenError("Cannot delete a published template")
        await self.repo.delete(template)

    async def publish_template(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str,
    ) -> ExamTemplate:
        template = await self.get_template(template_id)
        if user_role != "admin" and template.created_by != user_id:
            raise ForbiddenError("You can only publish your own templates")
        return await self.repo.update(template, is_published=True)
