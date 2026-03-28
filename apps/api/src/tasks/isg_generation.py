"""Celery task for ISG exam question generation with per-topic progress tracking."""

import asyncio
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.tasks.celery_app import celery_app
from src.core.config import settings

logger = logging.getLogger(__name__)


def _create_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create a fresh engine + session factory for this event loop."""
    engine = create_async_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _execute_isg_generation(
    task,
    template_id: uuid.UUID,
    request_data: dict,
    user_id: uuid.UUID,
) -> dict:
    from src.ai.schemas import GenerateRequest
    from src.ai.service import AIService
    from src.exams.repository import ExamTemplateRepository
    from src.isg.blueprints import TOPICS_BY_ID
    from src.isg.rubrics import get_rubric, get_rubric_for_topic
    from src.questions.repository import QuestionItemRepository
    from src.questions.schemas import QuestionItemCreate

    session_factory = _create_session_factory()

    async with session_factory() as db:
        try:
            template_repo = ExamTemplateRepository(db)
            question_repo = QuestionItemRepository(db)

            template = await template_repo.get_by_id(template_id)
            if template is None:
                raise ValueError("Template not found")

            isg_settings = template.settings or {}
            distribution = isg_settings.get("isg_topic_distribution", [])
            if not distribution:
                raise ValueError("No topic distribution found")

            question_types = request_data.get("question_types", ["mcq"])
            difficulty = request_data.get("difficulty")
            use_rag = request_data.get("use_rag", True)
            rubric_id = request_data.get("rubric_id")

            # Build initial topic progress
            topic_progress = []
            total_requested = 0
            for entry in distribution:
                qc = entry["question_count"]
                total_requested += qc
                topic_progress.append({
                    "topic_id": entry["topic_id"],
                    "topic_name": entry["topic_name"],
                    "requested_count": qc,
                    "generated_count": 0,
                    "status": "pending",
                    "errors": [],
                })

            # Report initial state
            task.update_state(state="GENERATING", meta={
                "template_id": str(template_id),
                "total_generated": 0,
                "total_requested": total_requested,
                "topic_progress": topic_progress,
                "current_topic": None,
            })

            ai_service = AIService(db)
            total_generated = 0
            trace_ids = []

            for i, topic_entry in enumerate(distribution):
                topic_id = topic_entry["topic_id"]
                topic_name = topic_entry["topic_name"]
                question_count = topic_entry["question_count"]

                if question_count == 0:
                    topic_progress[i]["status"] = "done"
                    continue

                topic_progress[i]["status"] = "generating"
                task.update_state(state="GENERATING", meta={
                    "template_id": str(template_id),
                    "total_generated": total_generated,
                    "total_requested": total_requested,
                    "topic_progress": topic_progress,
                    "current_topic": topic_name,
                })

                topic_obj = TOPICS_BY_ID.get(topic_id)
                generated_for_topic = 0
                topic_errors = []

                for qt_idx, qt in enumerate(question_types):
                    base = question_count // len(question_types)
                    extra = 1 if qt_idx < (question_count % len(question_types)) else 0
                    count_for_type = base + extra

                    if count_for_type == 0:
                        continue

                    rubric_dict = None
                    if qt == "long_form":
                        rubric = None
                        if rubric_id:
                            rubric = get_rubric(rubric_id)
                        if rubric is None:
                            rubric = get_rubric_for_topic(topic_id)
                        if rubric is not None:
                            rubric_dict = rubric.to_dict()

                    gen_request = GenerateRequest(
                        template_id=template_id,
                        question_type=qt,
                        topic=topic_name,
                        subtopic=None,
                        count=count_for_type,
                        difficulty=difficulty,
                        locale="tr-TR",
                        use_rag=use_rag,
                    )

                    try:
                        questions, errors, trace_id = await ai_service.generate_questions(
                            gen_request, user_id
                        )
                        topic_errors.extend(errors)

                        if trace_id is not None:
                            trace_ids.append(str(trace_id))

                        for q in questions:
                            create_data = QuestionItemCreate(
                                question_type=q.question_type,
                                stem=q.stem,
                                options=[{"key": o["key"], "text": o["text"]} for o in q.options]
                                if q.options
                                else None,
                                correct_answer=q.correct_answer,
                                rubric=rubric_dict,
                                explanation=q.explanation,
                                difficulty=q.difficulty,
                                topic=topic_id if topic_obj else topic_name,
                                subtopic=q.subtopic,
                            )
                            await question_repo.create(
                                template_id=template_id,
                                **create_data.model_dump(exclude_unset=True),
                            )
                            generated_for_topic += 1
                    except Exception as exc:
                        logger.exception("Error generating %s questions for topic %s", qt, topic_name)
                        topic_errors.append(str(exc))

                total_generated += generated_for_topic
                topic_progress[i]["generated_count"] = generated_for_topic
                topic_progress[i]["errors"] = topic_errors
                topic_progress[i]["status"] = "done" if generated_for_topic > 0 else "error"

                # Report progress after each topic
                task.update_state(state="GENERATING", meta={
                    "template_id": str(template_id),
                    "total_generated": total_generated,
                    "total_requested": total_requested,
                    "topic_progress": topic_progress,
                    "current_topic": None,
                })

            await db.commit()

            return {
                "template_id": str(template_id),
                "total_generated": total_generated,
                "total_requested": total_requested,
                "topic_progress": topic_progress,
                "trace_ids": trace_ids,
            }
        except Exception:
            await db.rollback()
            raise


@celery_app.task(
    name="src.tasks.isg_generation.generate_isg",
    bind=True,
    max_retries=0,
)
def generate_isg(self, template_id: str, request_data: dict, user_id: str) -> dict:
    parsed_template_id = uuid.UUID(template_id)
    parsed_user_id = uuid.UUID(user_id)

    try:
        return asyncio.run(
            _execute_isg_generation(self, parsed_template_id, request_data, parsed_user_id)
        )
    except Exception as exc:
        logger.exception("ISG generation failed for template %s", template_id)
        raise exc
