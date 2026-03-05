from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adaptive.models import ItemParameter, ThetaHistory


class ItemParameterRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_question_id(
        self, question_id: uuid.UUID
    ) -> ItemParameter | None:
        stmt = select(ItemParameter).where(
            ItemParameter.question_id == question_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_question_ids(
        self, question_ids: list[uuid.UUID]
    ) -> list[ItemParameter]:
        if not question_ids:
            return []
        stmt = select(ItemParameter).where(
            ItemParameter.question_id.in_(question_ids)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self, question_id: uuid.UUID, **kwargs: object
    ) -> ItemParameter:
        existing = await self.get_by_question_id(question_id)
        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        param = ItemParameter(question_id=question_id, **kwargs)
        self.db.add(param)
        await self.db.flush()
        await self.db.refresh(param)
        return param


class ThetaHistoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_session(
        self, session_id: uuid.UUID
    ) -> list[ThetaHistory]:
        stmt = (
            select(ThetaHistory)
            .where(ThetaHistory.session_id == session_id)
            .order_by(ThetaHistory.step)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_last(
        self, session_id: uuid.UUID
    ) -> ThetaHistory | None:
        stmt = (
            select(ThetaHistory)
            .where(ThetaHistory.session_id == session_id)
            .order_by(ThetaHistory.step.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: object) -> ThetaHistory:
        entry = ThetaHistory(**kwargs)
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry
