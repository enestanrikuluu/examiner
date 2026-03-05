import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.orgs.repository import MembershipRepository, OrgRepository
from src.users.models import Org, OrgMembership


class OrgService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = OrgRepository(db)
        self.membership_repo = MembershipRepository(db)

    async def create(self, name: str, slug: str, settings: dict[str, Any] | None = None) -> Org:
        existing = await self.repo.get_by_slug(slug)
        if existing:
            raise ConflictError("An organization with this slug already exists")
        org = Org(name=name, slug=slug, settings=settings or {})
        return await self.repo.create(org)

    async def get_by_id(self, org_id: uuid.UUID) -> Org:
        org = await self.repo.get_by_id(org_id)
        if not org:
            raise NotFoundError("Organization not found")
        return org

    async def list_by_user(self, user_id: uuid.UUID) -> list[Org]:
        return await self.repo.list_by_user(user_id)

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Org], int]:
        return await self.repo.list_all(page=page, page_size=page_size)

    async def update(
        self,
        org_id: uuid.UUID,
        name: str | None = None,
        slug: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Org:
        org = await self.get_by_id(org_id)
        if name is not None:
            org.name = name
        if slug is not None:
            if slug != org.slug:
                existing = await self.repo.get_by_slug(slug)
                if existing:
                    raise ConflictError("Slug already in use")
            org.slug = slug
        if settings is not None:
            org.settings = settings
        return await self.repo.update(org)

    async def add_member(
        self, org_id: uuid.UUID, user_id: uuid.UUID, role: str = "member"
    ) -> OrgMembership:
        await self.get_by_id(org_id)
        existing = await self.membership_repo.get(user_id, org_id)
        if existing:
            raise ConflictError("User is already a member of this organization")
        membership = OrgMembership(user_id=user_id, org_id=org_id, role=role)
        return await self.membership_repo.create(membership)

    async def remove_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        membership = await self.membership_repo.get(user_id, org_id)
        if not membership:
            raise NotFoundError("Membership not found")
        await self.membership_repo.delete(membership)

    async def list_members(self, org_id: uuid.UUID) -> list[OrgMembership]:
        await self.get_by_id(org_id)
        return await self.membership_repo.list_by_org(org_id)
