import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.grading.models import Grade


class GradeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, grade_id: uuid.UUID) -> Grade | None:
        result = await self.db.execute(
            select(Grade).where(Grade.id == grade_id)
        )
        return result.scalar_one_or_none()

    async def list_by_response(self, response_id: uuid.UUID) -> list[Grade]:
        result = await self.db.execute(
            select(Grade)
            .where(Grade.response_id == response_id)
            .order_by(Grade.graded_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_session(self, session_id: uuid.UUID) -> list[Grade]:
        from src.sessions.models import Response

        result = await self.db.execute(
            select(Grade)
            .join(Response, Grade.response_id == Response.id)
            .where(Response.session_id == session_id)
            .order_by(Grade.graded_at)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: object) -> Grade:
        grade = Grade(**kwargs)
        self.db.add(grade)
        await self.db.flush()
        await self.db.refresh(grade)
        return grade

    async def update(self, grade: Grade, **kwargs: object) -> Grade:
        for key, value in kwargs.items():
            if value is not None:
                setattr(grade, key, value)
        await self.db.flush()
        await self.db.refresh(grade)
        return grade
