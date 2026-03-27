import asyncio
import uuid
import logging

from src.tasks.celery_app import celery_app
from src.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def _execute_generation(request_data: dict, user_id: uuid.UUID) -> dict:
    from src.ai.schemas import GenerateRequest
    from src.ai.service import AIService

    request = GenerateRequest(**request_data)

    async with async_session_factory() as db:
        try:
            service = AIService(db)
            questions, errors, trace_id = await service.generate_questions(request, user_id)
            await db.commit()
            return {
                "trace_id": str(trace_id) if trace_id else None,
                "questions": [q.model_dump(mode="json") for q in questions],
                "errors": errors,
                "status": "completed" if questions else "failed",
            }
        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    name="src.tasks.question_generation.generate",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
)
def generate_questions(self, request_data: dict, user_id: str) -> dict:
    parsed_user_id = uuid.UUID(user_id)

    try:
        return asyncio.run(_execute_generation(request_data, parsed_user_id))
    except Exception as exc:
        logger.exception("Question generation failed")
        raise self.retry(exc=exc)
