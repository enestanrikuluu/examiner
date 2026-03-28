from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine
from src.core.middleware import RequestIdMiddleware
from src.core.storage import ensure_bucket_exists


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    ensure_bucket_exists()
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    from src.adaptive.router import router as adaptive_router
    from src.analytics.router import router as analytics_router
    from src.ai.router import document_router
    from src.ai.router import router as ai_router
    from src.auth.router import router as auth_router
    from src.exams.router import router as exams_router
    from src.grading.router import router as grading_router
    from src.health import router as health_router
    from src.isg.router import router as isg_router
    from src.orgs.router import router as orgs_router
    from src.questions.router import router as questions_router
    from src.sessions.router import config_router as sessions_config_router
    from src.sessions.router import router as sessions_router
    from src.users.router import router as users_router

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(users_router, prefix=settings.api_prefix)
    app.include_router(orgs_router, prefix=settings.api_prefix)
    app.include_router(exams_router, prefix=settings.api_prefix)
    app.include_router(questions_router, prefix=settings.api_prefix)
    app.include_router(sessions_config_router, prefix=settings.api_prefix)
    app.include_router(sessions_router, prefix=settings.api_prefix)
    app.include_router(grading_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(document_router, prefix=settings.api_prefix)
    app.include_router(isg_router, prefix=settings.api_prefix)
    app.include_router(adaptive_router, prefix=settings.api_prefix)
    app.include_router(analytics_router, prefix=settings.api_prefix)

    return app


app = create_app()
