import asyncio
import uuid
import logging

from src.tasks.celery_app import celery_app
from src.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def _execute_calibration(
    template_id: uuid.UUID,
    min_responses: int,
) -> dict:
    from src.adaptive.service import AdaptiveService

    async with async_session_factory() as db:
        try:
            service = AdaptiveService(db)
            result = await service.calibrate(
                template_id=template_id,
                min_responses=min_responses,
            )
            await db.commit()
            return result.model_dump(mode="json")
        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    name="src.tasks.calibration.calibrate",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
)
def calibrate_items(self, template_id: str, min_responses: int = 30) -> dict:
    parsed_id = uuid.UUID(template_id)

    try:
        return asyncio.run(_execute_calibration(parsed_id, min_responses))
    except Exception as exc:
        logger.exception("Calibration failed for template %s", template_id)
        raise self.retry(exc=exc)
