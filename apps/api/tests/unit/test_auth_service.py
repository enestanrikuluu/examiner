import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.service import AuthService
from src.core.exceptions import ConflictError, UnauthorizedError
from src.users.models import User


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def auth_service(mock_db: AsyncMock) -> AuthService:
    return AuthService(mock_db)


def _make_user(
    email: str = "test@example.com",
    password_hash: str = "$2b$12$fake",
    role: str = "student",
    is_active: bool = True,
) -> User:
    user = User()
    user.id = uuid.uuid4()
    user.email = email
    user.full_name = "Test User"
    user.hashed_password = password_hash
    user.role = role
    user.is_active = is_active
    user.auth_provider = "local"
    return user


@pytest.mark.asyncio
async def test_register_creates_user_and_returns_tokens(
    auth_service: AuthService,
) -> None:
    with patch.object(auth_service.user_repo, "get_by_email", return_value=None):
        with patch.object(
            auth_service.user_repo,
            "create",
            side_effect=lambda u: setattr(u, "id", uuid.uuid4()) or u,
        ):
            _user, tokens = await auth_service.register(
                email="new@example.com",
                password="password123",
                full_name="New User",
            )
            assert tokens.access_token
            assert tokens.refresh_token
            assert tokens.token_type == "bearer"


@pytest.mark.asyncio
async def test_register_raises_conflict_for_existing_email(
    auth_service: AuthService,
) -> None:
    existing_user = _make_user()
    with patch.object(auth_service.user_repo, "get_by_email", return_value=existing_user):
        with pytest.raises(ConflictError):
            await auth_service.register(
                email="test@example.com",
                password="password123",
                full_name="Test",
            )


@pytest.mark.asyncio
async def test_login_with_invalid_email_raises(
    auth_service: AuthService,
) -> None:
    with patch.object(auth_service.user_repo, "get_by_email", return_value=None):
        with pytest.raises(UnauthorizedError):
            await auth_service.login("nonexistent@example.com", "password")


@pytest.mark.asyncio
async def test_login_with_wrong_password_raises(
    auth_service: AuthService,
) -> None:
    user = _make_user()
    with patch.object(auth_service.user_repo, "get_by_email", return_value=user):
        with patch("src.auth.service.verify_password", return_value=False):
            with pytest.raises(UnauthorizedError):
                await auth_service.login("test@example.com", "wrongpassword")


@pytest.mark.asyncio
async def test_login_with_inactive_user_raises(
    auth_service: AuthService,
) -> None:
    user = _make_user(is_active=False)
    with patch.object(auth_service.user_repo, "get_by_email", return_value=user):
        with patch("src.auth.service.verify_password", return_value=True):
            with pytest.raises(UnauthorizedError):
                await auth_service.login("test@example.com", "password")


@pytest.mark.asyncio
async def test_login_success_returns_tokens(
    auth_service: AuthService,
) -> None:
    user = _make_user()
    with patch.object(auth_service.user_repo, "get_by_email", return_value=user):
        with patch("src.auth.service.verify_password", return_value=True):
            _user, tokens = await auth_service.login("test@example.com", "password")
            assert tokens.access_token
            assert tokens.refresh_token


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_raises(
    auth_service: AuthService,
) -> None:
    with pytest.raises(UnauthorizedError):
        await auth_service.refresh("invalid-token")
