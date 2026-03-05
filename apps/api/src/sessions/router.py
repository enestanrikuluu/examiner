import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_student
from src.core.database import get_db
from src.sessions.schemas import (
    BatchResponseSubmit,
    GradeOut,
    ResponseOut,
    ResponseSubmit,
    SessionCreate,
    SessionListResponse,
    SessionOut,
    SessionResultOut,
)
from src.sessions.service import SessionService
from src.users.models import User

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    body: SessionCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    service = SessionService(db)
    session = await service.create_session(body.template_id, user.id)
    return SessionOut.model_validate(session)


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    template_id: uuid.UUID | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    service = SessionService(db)
    items, total = await service.list_sessions(
        user_id=user.id,
        user_role=user.role,
        template_id=template_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return SessionListResponse(
        items=[SessionOut.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    service = SessionService(db)
    session = await service.get_session(session_id, user.id, user.role)
    return SessionOut.model_validate(session)


@router.post("/{session_id}/start", response_model=SessionOut)
async def start_session(
    session_id: uuid.UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    service = SessionService(db)
    session = await service.start_session(session_id, user.id)
    return SessionOut.model_validate(session)


@router.post("/{session_id}/responses", response_model=ResponseOut)
async def submit_response(
    session_id: uuid.UUID,
    body: ResponseSubmit,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> ResponseOut:
    service = SessionService(db)
    response = await service.submit_response(session_id, user.id, body)
    return ResponseOut.model_validate(response)


@router.post(
    "/{session_id}/responses/batch",
    response_model=list[ResponseOut],
)
async def batch_submit_responses(
    session_id: uuid.UUID,
    body: BatchResponseSubmit,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> list[ResponseOut]:
    service = SessionService(db)
    results = []
    for resp_data in body.responses:
        response = await service.submit_response(
            session_id, user.id, resp_data
        )
        results.append(ResponseOut.model_validate(response))
    return results


@router.post("/{session_id}/submit", response_model=SessionOut)
async def submit_session(
    session_id: uuid.UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    service = SessionService(db)
    session = await service.submit_session(session_id, user.id)
    return SessionOut.model_validate(session)


@router.get("/{session_id}/result", response_model=SessionResultOut)
async def get_session_result(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionResultOut:
    service = SessionService(db)
    session = await service.get_session_result(session_id, user.id, user.role)
    responses = [ResponseOut.model_validate(r) for r in session.responses]
    grades: list[GradeOut] = []
    for r in session.responses:
        for g in r.grades:
            grades.append(GradeOut.model_validate(g))
    return SessionResultOut(
        session=SessionOut.model_validate(session),
        responses=responses,
        grades=grades,
    )
