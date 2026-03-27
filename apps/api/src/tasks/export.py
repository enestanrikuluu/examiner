import asyncio
import uuid
import logging

from src.tasks.celery_app import celery_app
from src.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def _execute_csv_export(
    template_id: uuid.UUID,
    include_responses: bool,
    include_grades: bool,
) -> dict:
    from src.analytics.exporters.csv import export_sessions_csv

    async with async_session_factory() as db:
        try:
            csv_content = await export_sessions_csv(
                db,
                template_id,
                include_responses=include_responses,
                include_grades=include_grades,
            )
            await db.commit()
            return {"content": csv_content, "format": "csv"}
        except Exception:
            await db.rollback()
            raise


async def _execute_report_export(template_id: uuid.UUID) -> dict:
    from src.analytics.exporters.pdf import generate_report_text

    async with async_session_factory() as db:
        try:
            report = await generate_report_text(db, template_id)
            await db.commit()
            return {"content": report, "format": "text"}
        except Exception:
            await db.rollback()
            raise


@celery_app.task(name="src.tasks.export.csv")
def export_csv(
    template_id: str,
    include_responses: bool = False,
    include_grades: bool = True,
) -> dict:
    parsed_id = uuid.UUID(template_id)
    return asyncio.run(_execute_csv_export(parsed_id, include_responses, include_grades))


@celery_app.task(name="src.tasks.export.report")
def export_report(template_id: str) -> dict:
    parsed_id = uuid.UUID(template_id)
    return asyncio.run(_execute_report_export(parsed_id))
