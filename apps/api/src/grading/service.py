"""Grading service placeholder. Full grading logic (deterministic + LLM) comes in Phase 4."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.grading.models import Grade
from src.grading.repository import GradeRepository
from src.grading.schemas import GradeOverride


class GradingService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = GradeRepository(db)

    async def get_grade(self, grade_id: uuid.UUID) -> Grade:
        grade = await self.repo.get_by_id(grade_id)
        if grade is None:
            raise NotFoundError("Grade not found")
        return grade

    async def list_session_grades(self, session_id: uuid.UUID) -> list[Grade]:
        return await self.repo.list_by_session(session_id)

    async def override_grade(
        self,
        grade_id: uuid.UUID,
        data: GradeOverride,
        graded_by: uuid.UUID,
    ) -> Grade:
        grade = await self.get_grade(grade_id)
        return await self.repo.update(
            grade,
            score=data.score,
            feedback=data.feedback,
            grading_method="manual",
            graded_by=graded_by,
        )
