import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import TokenResponse
from src.core.exceptions import ConflictError, UnauthorizedError
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.users.models import User
from src.users.repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        locale: str = "tr-TR",
    ) -> tuple[User, TokenResponse]:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("A user with this email already exists")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            locale=locale,
            role="student",
            auth_provider="local",
        )
        user = await self.user_repo.create(user)
        tokens = self._create_tokens(user)
        return user, tokens

    async def login(self, email: str, password: str) -> tuple[User, TokenResponse]:
        user = await self.user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        tokens = self._create_tokens(user)
        return user, tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise UnauthorizedError("Invalid refresh token") from e

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = uuid.UUID(str(payload["sub"]))
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or deactivated")

        return self._create_tokens(user)

    async def get_or_create_google_user(
        self,
        google_id: str,
        email: str,
        full_name: str,
    ) -> tuple[User, TokenResponse, bool]:
        user = await self.user_repo.get_by_google_id(google_id)
        is_new = False

        if not user:
            user = await self.user_repo.get_by_email(email)
            if user:
                user.google_id = google_id
                user.auth_provider = "google"
                user = await self.user_repo.update(user)
            else:
                user = User(
                    email=email,
                    full_name=full_name,
                    google_id=google_id,
                    auth_provider="google",
                    role="student",
                    locale="tr-TR",
                )
                user = await self.user_repo.create(user)
                is_new = True

        tokens = self._create_tokens(user)
        return user, tokens, is_new

    @staticmethod
    def _create_tokens(user: User) -> TokenResponse:
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
