import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.questions.models import QuestionItem


class QuestionItemRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, question_id: uuid.UUID) -> QuestionItem | None:
        result = await self.db.execute(
            select(QuestionItem).where(QuestionItem.id == question_id)
        )
        return result.scalar_one_or_none()

    async def list_by_template(
        self,
        template_id: uuid.UUID,
        *,
        is_active: bool | None = True,
        topic: str | None = None,
        question_type: str | None = None,
    ) -> tuple[list[QuestionItem], int]:
        query = select(QuestionItem).where(
            QuestionItem.template_id == template_id
        )
        count_query = select(func.count()).select_from(QuestionItem).where(
            QuestionItem.template_id == template_id
        )

        if is_active is not None:
            query = query.where(QuestionItem.is_active == is_active)
            count_query = count_query.where(QuestionItem.is_active == is_active)
        if topic is not None:
            query = query.where(QuestionItem.topic == topic)
            count_query = count_query.where(QuestionItem.topic == topic)
        if question_type is not None:
            query = query.where(QuestionItem.question_type == question_type)
            count_query = count_query.where(
                QuestionItem.question_type == question_type
            )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(QuestionItem.sort_order, QuestionItem.created_at)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def create(self, **kwargs: object) -> QuestionItem:
        question = QuestionItem(**kwargs)
        self.db.add(question)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def bulk_create(
        self, template_id: uuid.UUID, items: list[dict[str, object]]
    ) -> list[QuestionItem]:
        questions: list[QuestionItem] = []
        for item_data in items:
            q = QuestionItem(template_id=template_id, **item_data)
            self.db.add(q)
            questions.append(q)
        await self.db.flush()
        for q in questions:
            await self.db.refresh(q)
        return questions

    async def update(
        self, question: QuestionItem, **kwargs: object
    ) -> QuestionItem:
        for key, value in kwargs.items():
            if value is not None:
                setattr(question, key, value)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def delete(self, question: QuestionItem) -> None:
        await self.db.delete(question)
        await self.db.flush()
