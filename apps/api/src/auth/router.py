from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import (
    GoogleCallbackResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from src.auth.service import AuthService
from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import UnauthorizedError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    _user, tokens = await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        locale=body.locale,
    )
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    _user, tokens = await service.login(email=body.email, password=body.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh(body.refresh_token)


@router.post("/logout", status_code=204)
async def logout() -> None:
    # Client-side token deletion; server-side blacklisting can be added via Redis
    return None


@router.get("/google")
async def google_login() -> dict[str, str]:
    if not settings.google_client_id:
        raise ValidationError("Google OAuth is not configured")

    from authlib.integrations.httpx_client import AsyncOAuth2Client

    client = AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
        scope="openid email profile",
    )
    uri, _state = client.create_authorization_url("https://accounts.google.com/o/oauth2/v2/auth")
    return {"authorization_url": uri}


@router.get("/google/callback", response_model=GoogleCallbackResponse)
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> GoogleCallbackResponse:
    if not settings.google_client_id:
        raise ValidationError("Google OAuth is not configured")

    from authlib.integrations.httpx_client import AsyncOAuth2Client

    client = AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )

    await client.fetch_token(
        "https://oauth2.googleapis.com/token",
        code=code,
    )

    resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo")
    if resp.status_code != 200:
        raise UnauthorizedError("Failed to fetch user info from Google")

    userinfo = resp.json()
    google_id = userinfo["sub"]
    email = userinfo["email"]
    full_name = userinfo.get("name", email.split("@")[0])

    service = AuthService(db)
    _user, tokens, is_new = await service.get_or_create_google_user(
        google_id=google_id,
        email=email,
        full_name=full_name,
    )

    return GoogleCallbackResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        is_new_user=is_new,
    )
