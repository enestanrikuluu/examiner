import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exams.models import ExamTemplate


class ExamTemplateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, template_id: uuid.UUID) -> ExamTemplate | None:
        result = await self.db.execute(
            select(ExamTemplate).where(ExamTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        *,
        created_by: uuid.UUID | None = None,
        org_id: uuid.UUID | None = None,
        is_published: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExamTemplate], int]:
        query = select(ExamTemplate)
        count_query = select(func.count()).select_from(ExamTemplate)

        if created_by is not None:
            query = query.where(ExamTemplate.created_by == created_by)
            count_query = count_query.where(ExamTemplate.created_by == created_by)
        if org_id is not None:
            query = query.where(ExamTemplate.org_id == org_id)
            count_query = count_query.where(ExamTemplate.org_id == org_id)
        if is_published is not None:
            query = query.where(ExamTemplate.is_published == is_published)
            count_query = count_query.where(ExamTemplate.is_published == is_published)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(ExamTemplate.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def create(self, **kwargs: object) -> ExamTemplate:
        template = ExamTemplate(**kwargs)
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update(
        self, template: ExamTemplate, **kwargs: object
    ) -> ExamTemplate:
        for key, value in kwargs.items():
            if value is not None:
                setattr(template, key, value)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template: ExamTemplate) -> None:
        await self.db.delete(template)
        await self.db.flush()
