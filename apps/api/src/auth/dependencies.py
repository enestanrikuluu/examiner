import uuid
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.core.security import decode_token
from src.users.models import User
from src.users.repository import UserRepository

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise UnauthorizedError("Invalid or expired token") from e

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = uuid.UUID(str(payload["sub"]))
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")

    return user


def require_role(*roles: str) -> Any:
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return current_user

    return role_checker


require_admin = require_role("admin")
require_instructor = require_role("admin", "instructor")
require_student = require_role("admin", "instructor", "student")
