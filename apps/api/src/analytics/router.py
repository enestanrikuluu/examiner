import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.exporters.csv import export_sessions_csv
from src.analytics.exporters.pdf import generate_report_text
from src.analytics.schemas import (
    AICostOut,
    DashboardOut,
    ExportRequest,
    ItemAnalysisOut,
    PerformanceOverTimeOut,
    ScoreDistributionOut,
    TopicMasteryOut,
)
from src.analytics.service import AnalyticsService
from src.auth.dependencies import get_current_user, require_instructor
from src.core.database import get_db
from src.users.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    template_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardOut:
    """Get aggregated dashboard analytics."""
    svc = AnalyticsService(db)
    uid = user.id if user.role == "student" else None
    return await svc.dashboard(template_id=template_id, user_id=uid)


@router.get("/scores/{template_id}", response_model=ScoreDistributionOut)
async def get_score_distribution(
    template_id: uuid.UUID,
    buckets: int = Query(10, ge=5, le=20),
    _user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ScoreDistributionOut:
    """Get score distribution for a template."""
    svc = AnalyticsService(db)
    return await svc.score_distribution(template_id, bucket_count=buckets)


@router.get("/items/{template_id}", response_model=ItemAnalysisOut)
async def get_item_analysis(
    template_id: uuid.UUID,
    _user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ItemAnalysisOut:
    """Get per-item difficulty and discrimination stats."""
    svc = AnalyticsService(db)
    return await svc.item_analysis(template_id)


@router.get("/mastery/{template_id}", response_model=TopicMasteryOut)
async def get_topic_mastery(
    template_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TopicMasteryOut:
    """Get topic mastery rates. Students can only see their own."""
    svc = AnalyticsService(db)
    uid = user.id if user.role == "student" else user_id
    return await svc.topic_mastery(template_id, user_id=uid)


@router.get("/performance", response_model=PerformanceOverTimeOut)
async def get_performance_over_time(
    template_id: uuid.UUID | None = None,
    days: int = Query(30, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PerformanceOverTimeOut:
    """Get daily performance trends."""
    svc = AnalyticsService(db)
    uid = user.id if user.role == "student" else None
    return await svc.performance_over_time(
        template_id=template_id, user_id=uid, days=days
    )


@router.get("/ai-costs", response_model=AICostOut)
async def get_ai_costs(
    template_id: uuid.UUID | None = None,
    days: int | None = Query(None, ge=1, le=365),
    _user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> AICostOut:
    """Get AI usage cost breakdown."""
    svc = AnalyticsService(db)
    return await svc.ai_costs(template_id=template_id, days=days)


@router.post("/export/csv")
async def export_csv(
    body: ExportRequest,
    _user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export session data as CSV download."""
    csv_content = await export_sessions_csv(
        db,
        body.template_id,
        include_responses=body.include_responses,
        include_grades=body.include_grades,
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=export_{body.template_id}.csv"
        },
    )


@router.post("/export/pdf")
async def export_pdf(
    body: ExportRequest,
    _user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export analytics report as text (PDF placeholder)."""
    report = await generate_report_text(db, body.template_id)
    return StreamingResponse(
        iter([report]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=report_{body.template_id}.txt"
        },
    )
