import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_instructor
from src.core.database import get_db
from src.core.rate_limit import ai_rate_limit
from src.grading.schemas import GradeOverride
from src.grading.service import GradingService
from src.sessions.schemas import GradeOut, SessionOut
from src.users.models import User

router = APIRouter(prefix="/grading", tags=["grading"])


@router.post("/sessions/{session_id}/grade", response_model=SessionOut, dependencies=[Depends(ai_rate_limit)])
async def grade_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Grade all responses in a session (deterministic + LLM)."""
    service = GradingService(db)
    session = await service.grade_session(session_id, user.id)
    return SessionOut.model_validate(session)


@router.get("/sessions/{session_id}/grades", response_model=list[GradeOut])
async def list_session_grades(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GradeOut]:
    """List all grades for a session."""
    service = GradingService(db)
    grades = await service.list_session_grades(session_id)
    return [GradeOut.model_validate(g) for g in grades]


@router.post("/grades/{grade_id}/regrade", response_model=GradeOut)
async def regrade(
    grade_id: uuid.UUID,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> GradeOut:
    """Re-grade a response using LLM with temperature=0."""
    service = GradingService(db)
    grade = await service.regrade_response(grade_id, user.id)
    return GradeOut.model_validate(grade)


@router.patch("/grades/{grade_id}", response_model=GradeOut)
async def override_grade(
    grade_id: uuid.UUID,
    body: GradeOverride,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> GradeOut:
    """Manually override a grade (instructor only)."""
    service = GradingService(db)
    grade = await service.override_grade(grade_id, body, user.id)
    return GradeOut.model_validate(grade)
