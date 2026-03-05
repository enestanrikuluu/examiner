import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_admin, require_instructor
from src.core.database import get_db
from src.orgs.schemas import (
    MembershipCreate,
    MembershipOut,
    OrgCreate,
    OrgListResponse,
    OrgOut,
    OrgUpdate,
)
from src.orgs.service import OrgService
from src.users.models import User

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.post("", response_model=OrgOut, status_code=201)
async def create_org(
    body: OrgCreate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> OrgOut:
    service = OrgService(db)
    org = await service.create(name=body.name, slug=body.slug, settings=body.settings)
    return OrgOut.model_validate(org)


@router.get("", response_model=OrgListResponse)
async def list_orgs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrgListResponse:
    service = OrgService(db)
    if current_user.role == "admin":
        orgs, total = await service.list_all(page=page, page_size=page_size)
    else:
        orgs = await service.list_by_user(current_user.id)
        total = len(orgs)
    return OrgListResponse(
        items=[OrgOut.model_validate(o) for o in orgs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{org_id}", response_model=OrgOut)
async def get_org(
    org_id: uuid.UUID,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrgOut:
    service = OrgService(db)
    org = await service.get_by_id(org_id)
    return OrgOut.model_validate(org)


@router.patch("/{org_id}", response_model=OrgOut)
async def update_org(
    org_id: uuid.UUID,
    body: OrgUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> OrgOut:
    service = OrgService(db)
    org = await service.update(
        org_id=org_id, name=body.name, slug=body.slug, settings=body.settings
    )
    return OrgOut.model_validate(org)


@router.post("/{org_id}/members", response_model=MembershipOut, status_code=201)
async def add_member(
    org_id: uuid.UUID,
    body: MembershipCreate,
    _instructor: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> MembershipOut:
    service = OrgService(db)
    membership = await service.add_member(org_id=org_id, user_id=body.user_id, role=body.role)
    return MembershipOut.model_validate(membership)


@router.get("/{org_id}/members", response_model=list[MembershipOut])
async def list_members(
    org_id: uuid.UUID,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MembershipOut]:
    service = OrgService(db)
    members = await service.list_members(org_id)
    return [MembershipOut.model_validate(m) for m in members]


@router.delete("/{org_id}/members/{user_id}", status_code=204)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = OrgService(db)
    await service.remove_member(org_id=org_id, user_id=user_id)
