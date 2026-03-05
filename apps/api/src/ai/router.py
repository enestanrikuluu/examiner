import uuid

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.document_service import DocumentService
from src.ai.schemas import (
    AcceptQuestionsRequest,
    DocumentOut,
    GenerateRequest,
    GenerateResultOut,
    ModelTraceListResponse,
    ModelTraceOut,
    PromptVersionOut,
)
from src.ai.service import AIService
from src.auth.dependencies import get_current_user, require_instructor
from src.core.database import get_db
from src.core.exceptions import ValidationError
from src.users.models import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate", response_model=GenerateResultOut)
async def generate_questions(
    body: GenerateRequest,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> GenerateResultOut:
    """Generate questions using AI (synchronous for now, Celery task in production)."""
    service = AIService(db)
    questions, errors, trace_id = await service.generate_questions(
        body, user.id
    )
    status = "completed" if questions else ("failed" if errors else "completed")

    return GenerateResultOut(
        task_id=str(trace_id) if trace_id else "unknown",
        status=status,
        questions=questions,
        errors=errors,
        trace_id=trace_id,
    )


@router.post("/generate/{trace_id}/accept", response_model=list[dict[str, str]])
async def accept_generated_questions(
    trace_id: uuid.UUID,
    body: AcceptQuestionsRequest,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, str]]:
    """Accept selected generated questions and add them to the template.

    NOTE: In the current synchronous flow, questions are returned directly
    from /generate. This endpoint is a placeholder for the async Celery flow
    where results are stored and accepted later.
    """
    return [{"status": "accepted", "trace_id": str(trace_id)}]


@router.get("/traces", response_model=ModelTraceListResponse)
async def list_traces(
    template_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ModelTraceListResponse:
    from sqlalchemy import func, select

    from src.ai.models import ModelTrace

    query = select(ModelTrace)
    count_query = select(func.count()).select_from(ModelTrace)

    if template_id:
        query = query.where(ModelTrace.template_id == template_id)
        count_query = count_query.where(ModelTrace.template_id == template_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(ModelTrace.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return ModelTraceListResponse(
        items=[ModelTraceOut.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/prompts", response_model=list[PromptVersionOut])
async def list_prompts(
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> list[PromptVersionOut]:
    from src.ai.prompts.registry import PromptRegistry

    registry = PromptRegistry(db)
    prompts = await registry.list_prompts()
    return [PromptVersionOut.model_validate(p) for p in prompts]


# --- Document endpoints ---

document_router = APIRouter(tags=["documents"])


@document_router.post(
    "/templates/{template_id}/documents",
    response_model=DocumentOut,
    status_code=201,
)
async def upload_document(
    template_id: uuid.UUID,
    file: UploadFile,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    if not file.filename:
        raise ValidationError("Filename is required")

    file_bytes = await file.read()
    service = DocumentService(db)
    doc = await service.upload_document(
        template_id=template_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes,
        user_id=user.id,
    )

    # Process document synchronously for now (Celery in production)
    doc = await service.process_document(doc.id)

    return DocumentOut.model_validate(doc)


@document_router.get(
    "/templates/{template_id}/documents",
    response_model=list[DocumentOut],
)
async def list_documents(
    template_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentOut]:
    service = DocumentService(db)
    docs = await service.list_documents(template_id)
    return [DocumentOut.model_validate(d) for d in docs]


@document_router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = DocumentService(db)
    await service.delete_document(document_id)
