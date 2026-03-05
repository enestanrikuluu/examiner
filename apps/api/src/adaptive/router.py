import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adaptive.schemas import (
    AdaptiveRespond,
    AdaptiveRespondOut,
    AdaptiveSessionCreate,
    AdaptiveSessionOut,
    CalibrationRequest,
    CalibrationResultOut,
    NextQuestionOut,
    NoMoreQuestions,
    ThetaOut,
)
from src.adaptive.service import AdaptiveService
from src.auth.dependencies import get_current_user, require_instructor, require_student
from src.core.database import get_db
from src.users.models import User

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


@router.post("/sessions", response_model=AdaptiveSessionOut, status_code=201)
async def create_adaptive_session(
    body: AdaptiveSessionCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> AdaptiveSessionOut:
    """Create a new adaptive exam session."""
    service = AdaptiveService(db)
    return await service.create_session(body.template_id, user.id)


@router.get(
    "/sessions/{session_id}/next",
    response_model=NextQuestionOut | NoMoreQuestions,
)
async def get_next_question(
    session_id: uuid.UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> NextQuestionOut | NoMoreQuestions:
    """Get the next adaptively selected question."""
    service = AdaptiveService(db)
    return await service.get_next_question(session_id, user.id)


@router.post(
    "/sessions/{session_id}/respond",
    response_model=AdaptiveRespondOut,
)
async def respond(
    session_id: uuid.UUID,
    body: AdaptiveRespond,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> AdaptiveRespondOut:
    """Submit a response and get updated theta estimate."""
    service = AdaptiveService(db)
    return await service.respond(
        session_id=session_id,
        user_id=user.id,
        question_id=body.question_id,
        answer=body.answer,
        time_spent_seconds=body.time_spent_seconds,
    )


@router.get("/sessions/{session_id}/theta", response_model=ThetaOut)
async def get_theta(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ThetaOut:
    """Get theta estimation history for a session."""
    service = AdaptiveService(db)
    return await service.get_theta(session_id, user.id)


@router.post("/calibrate", response_model=CalibrationResultOut)
async def calibrate(
    body: CalibrationRequest,
    _user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> CalibrationResultOut:
    """Calibrate IRT item parameters from response history."""
    service = AdaptiveService(db)
    return await service.calibrate(
        template_id=body.template_id,
        min_responses=body.min_responses,
    )
