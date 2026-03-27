import asyncio
import uuid
import logging

from src.tasks.celery_app import celery_app
from src.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def _execute_grading(session_id: uuid.UUID, user_id: uuid.UUID | None) -> dict:
    from src.grading.service import GradingService

    async with async_session_factory() as db:
        try:
            service = GradingService(db)
            session = await service.grade_session(session_id, user_id)
            await db.commit()
            return {
                "session_id": str(session.id),
                "status": session.status,
                "total_score": session.total_score,
                "max_score": session.max_score,
                "percentage": session.percentage,
                "passed": session.passed,
            }
        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    name="src.tasks.grading.grade_session",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def grade_session(self, session_id: str, user_id: str | None = None) -> dict:
    parsed_session_id = uuid.UUID(session_id)
    parsed_user_id = uuid.UUID(user_id) if user_id else None

    try:
        return asyncio.run(_execute_grading(parsed_session_id, parsed_user_id))
    except Exception as exc:
        logger.exception("Grading failed for session %s", session_id)
        raise self.retry(exc=exc)
