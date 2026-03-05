import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.sessions.models import ExamSession, Response


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, session_id: uuid.UUID) -> ExamSession | None:
        result = await self.db.execute(
            select(ExamSession).where(ExamSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_with_responses(
        self, session_id: uuid.UUID
    ) -> ExamSession | None:
        result = await self.db.execute(
            select(ExamSession)
            .options(
                selectinload(ExamSession.responses).selectinload(
                    Response.grades
                )
            )
            .where(ExamSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        *,
        user_id: uuid.UUID | None = None,
        template_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExamSession], int]:
        query = select(ExamSession)
        count_query = select(func.count()).select_from(ExamSession)

        if user_id is not None:
            query = query.where(ExamSession.user_id == user_id)
            count_query = count_query.where(ExamSession.user_id == user_id)
        if template_id is not None:
            query = query.where(ExamSession.template_id == template_id)
            count_query = count_query.where(
                ExamSession.template_id == template_id
            )
        if status is not None:
            query = query.where(ExamSession.status == status)
            count_query = count_query.where(ExamSession.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(ExamSession.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def create(self, **kwargs: object) -> ExamSession:
        session = ExamSession(**kwargs)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def update(
        self, session: ExamSession, **kwargs: object
    ) -> ExamSession:
        for key, value in kwargs.items():
            if value is not None:
                setattr(session, key, value)
        await self.db.flush()
        await self.db.refresh(session)
        return session


class ResponseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_session_and_question(
        self, session_id: uuid.UUID, question_id: uuid.UUID
    ) -> Response | None:
        result = await self.db.execute(
            select(Response).where(
                Response.session_id == session_id,
                Response.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_session(
        self, session_id: uuid.UUID
    ) -> list[Response]:
        result = await self.db.execute(
            select(Response)
            .where(Response.session_id == session_id)
            .order_by(Response.answered_at)
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        **kwargs: object,
    ) -> Response:
        existing = await self.get_by_session_and_question(
            session_id, question_id
        )
        if existing is not None:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            response = Response(
                session_id=session_id,
                question_id=question_id,
                **kwargs,
            )
            self.db.add(response)
            await self.db.flush()
            await self.db.refresh(response)
            return response
