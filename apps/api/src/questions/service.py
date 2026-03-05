import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ForbiddenError, NotFoundError
from src.exams.repository import ExamTemplateRepository
from src.questions.models import QuestionItem
from src.questions.repository import QuestionItemRepository
from src.questions.schemas import (
    BulkQuestionImport,
    QuestionItemCreate,
    QuestionItemUpdate,
)


class QuestionItemService:
    def __init__(self, db: AsyncSession) -> None:
        self.question_repo = QuestionItemRepository(db)
        self.template_repo = ExamTemplateRepository(db)

    async def _check_template_access(
        self, template_id: uuid.UUID, user_id: uuid.UUID, user_role: str
    ) -> None:
        template = await self.template_repo.get_by_id(template_id)
        if template is None:
            raise NotFoundError("Exam template not found")
        if user_role != "admin" and template.created_by != user_id:
            raise ForbiddenError("You can only manage questions in your own templates")

    async def get_question(self, question_id: uuid.UUID) -> QuestionItem:
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            raise NotFoundError("Question not found")
        return question

    async def list_questions(
        self,
        template_id: uuid.UUID,
        *,
        is_active: bool | None = True,
        topic: str | None = None,
        question_type: str | None = None,
    ) -> tuple[list[QuestionItem], int]:
        return await self.question_repo.list_by_template(
            template_id,
            is_active=is_active,
            topic=topic,
            question_type=question_type,
        )

    async def create_question(
        self,
        template_id: uuid.UUID,
        data: QuestionItemCreate,
        user_id: uuid.UUID,
        user_role: str,
    ) -> QuestionItem:
        await self._check_template_access(template_id, user_id, user_role)
        return await self.question_repo.create(
            template_id=template_id,
            **data.model_dump(exclude_unset=True),
        )

    async def bulk_import(
        self,
        template_id: uuid.UUID,
        data: BulkQuestionImport,
        user_id: uuid.UUID,
        user_role: str,
    ) -> list[QuestionItem]:
        await self._check_template_access(template_id, user_id, user_role)
        items = [q.model_dump(exclude_unset=True) for q in data.questions]
        return await self.question_repo.bulk_create(template_id, items)

    async def update_question(
        self,
        question_id: uuid.UUID,
        data: QuestionItemUpdate,
        user_id: uuid.UUID,
        user_role: str,
    ) -> QuestionItem:
        question = await self.get_question(question_id)
        await self._check_template_access(
            question.template_id, user_id, user_role
        )
        return await self.question_repo.update(
            question, **data.model_dump(exclude_unset=True)
        )

    async def delete_question(
        self,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str,
    ) -> None:
        question = await self.get_question(question_id)
        await self._check_template_access(
            question.template_id, user_id, user_role
        )
        await self.question_repo.delete(question)
