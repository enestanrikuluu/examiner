import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OrgCreate(BaseModel):
    name: str
    slug: str
    settings: dict[str, Any] | None = None


class OrgUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    settings: dict[str, Any] | None = None


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    settings: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipCreate(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class MembershipOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    org_id: uuid.UUID
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class OrgListResponse(BaseModel):
    items: list[OrgOut]
    total: int
    page: int
    page_size: int
