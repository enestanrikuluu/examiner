import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import AdminUserUpdate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def list_users(self, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
        return await self.repo.list_users(page=page, page_size=page_size)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.locale is not None:
            user.locale = data.locale
        return await self.repo.update(user)

    async def admin_update(self, user_id: uuid.UUID, data: AdminUserUpdate) -> User:
        user = await self.get_by_id(user_id)
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.locale is not None:
            user.locale = data.locale
        return await self.repo.update(user)
