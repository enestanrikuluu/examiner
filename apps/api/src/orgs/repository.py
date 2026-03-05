import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import Org, OrgMembership


class OrgRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, org_id: uuid.UUID) -> Org | None:
        result = await self.db.execute(select(Org).where(Org.id == org_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Org | None:
        result = await self.db.execute(select(Org).where(Org.slug == slug))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Org]:
        result = await self.db.execute(
            select(Org)
            .join(OrgMembership, OrgMembership.org_id == Org.id)
            .where(OrgMembership.user_id == user_id)
            .order_by(Org.name)
        )
        return list(result.scalars().all())

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Org], int]:
        count_result = await self.db.execute(select(func.count(Org.id)))
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Org).order_by(Org.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create(self, org: Org) -> Org:
        self.db.add(org)
        await self.db.flush()
        await self.db.refresh(org)
        return org

    async def update(self, org: Org) -> Org:
        await self.db.flush()
        await self.db.refresh(org)
        return org


class MembershipRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: uuid.UUID, org_id: uuid.UUID) -> OrgMembership | None:
        result = await self.db.execute(
            select(OrgMembership).where(
                OrgMembership.user_id == user_id,
                OrgMembership.org_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, org_id: uuid.UUID) -> list[OrgMembership]:
        result = await self.db.execute(select(OrgMembership).where(OrgMembership.org_id == org_id))
        return list(result.scalars().all())

    async def create(self, membership: OrgMembership) -> OrgMembership:
        self.db.add(membership)
        await self.db.flush()
        await self.db.refresh(membership)
        return membership

    async def delete(self, membership: OrgMembership) -> None:
        await self.db.delete(membership)
        await self.db.flush()
