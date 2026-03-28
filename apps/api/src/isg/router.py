"""ISG router: blueprints, rubrics, exam creation, and question generation."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_instructor
from src.core.database import get_db
from src.isg.blueprints import ISG_TOPICS, TOPICS_BY_ID, get_blueprint, list_blueprints
from src.isg.rubrics import list_rubrics
from src.isg.schemas import (
    BlueprintListOut,
    BlueprintOut,
    ISGExamCreate,
    ISGExamOut,
    ISGGenerateRequest,
    ISGGenerateTaskOut,
    ISGTaskProgressTopic,
    ISGTaskStatusOut,
    RubricCriterionOut,
    RubricListOut,
    RubricOut,
    SubtopicOut,
    TopicListOut,
    TopicOut,
    TopicWeightOut,
)
from src.isg.service import ISGService
from src.users.models import User

router = APIRouter(prefix="/isg", tags=["isg"])


def _blueprint_to_out(bp: object) -> BlueprintOut:
    from src.isg.blueprints import Blueprint

    assert isinstance(bp, Blueprint)
    return BlueprintOut(
        exam_class=bp.exam_class,
        title=bp.title,
        description=bp.description,
        total_questions=bp.total_questions,
        time_limit_minutes=bp.time_limit_minutes,
        pass_score=bp.pass_score,
        topic_weights=[
            TopicWeightOut(
                topic_id=tw.topic_id,
                topic_name=TOPICS_BY_ID[tw.topic_id].name
                if tw.topic_id in TOPICS_BY_ID
                else tw.topic_id,
                weight=tw.weight,
                question_count=tw.question_count,
            )
            for tw in bp.topic_weights
        ],
        allowed_question_types=list(bp.allowed_question_types),
    )


@router.get("/blueprints", response_model=BlueprintListOut)
async def get_blueprints() -> BlueprintListOut:
    """List all available ISG exam blueprints (A/B/C classes)."""
    bps = list_blueprints()
    return BlueprintListOut(blueprints=[_blueprint_to_out(bp) for bp in bps])


@router.get("/blueprints/{exam_class}", response_model=BlueprintOut)
async def get_blueprint_detail(exam_class: str) -> BlueprintOut:
    """Get a specific ISG blueprint by class (A, B, or C)."""
    from src.core.exceptions import NotFoundError

    bp = get_blueprint(exam_class)
    if bp is None:
        raise NotFoundError(f"Blueprint for class '{exam_class}' not found")
    return _blueprint_to_out(bp)


@router.get("/topics", response_model=TopicListOut)
async def get_topics() -> TopicListOut:
    """List all ISG topics and subtopics."""
    return TopicListOut(
        topics=[
            TopicOut(
                id=t.id,
                name=t.name,
                subtopics=[SubtopicOut(id=s.id, name=s.name) for s in t.subtopics],
            )
            for t in ISG_TOPICS
        ]
    )


@router.get("/rubrics", response_model=RubricListOut)
async def get_rubrics() -> RubricListOut:
    """List all default ISG rubrics for long-form questions."""
    rubrics = list_rubrics()
    return RubricListOut(
        rubrics=[
            RubricOut(
                rubric_id=r.rubric_id,
                name=r.name,
                description=r.description,
                max_score=r.max_score,
                criteria=[
                    RubricCriterionOut(
                        id=c.id,
                        description=c.description,
                        max_points=c.max_points,
                    )
                    for c in r.criteria
                ],
            )
            for r in rubrics
        ]
    )


@router.post("/exams", response_model=ISGExamOut)
async def create_isg_exam(
    data: ISGExamCreate,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ISGExamOut:
    """Create an exam template from an ISG blueprint."""
    service = ISGService(db)
    result = await service.create_exam(data, user_id=user.id)
    await db.commit()
    return result


@router.post("/exams/{template_id}/generate", response_model=ISGGenerateTaskOut)
async def generate_isg_questions(
    template_id: str,
    data: ISGGenerateRequest,
    user: User = Depends(require_instructor),
    db: AsyncSession = Depends(get_db),
) -> ISGGenerateTaskOut:
    """Dispatch ISG question generation as a background task.

    Returns a task_id immediately. Poll GET /isg/tasks/{task_id} for progress.
    """
    import uuid as uuid_mod

    from src.core.exceptions import NotFoundError, ValidationError
    from src.exams.repository import ExamTemplateRepository
    from src.tasks.isg_generation import generate_isg

    parsed_id = uuid_mod.UUID(template_id)
    template_repo = ExamTemplateRepository(db)
    template = await template_repo.get_by_id(parsed_id)

    if template is None:
        raise NotFoundError("Template not found")
    if template.created_by != user.id:
        raise ValidationError("Only the template owner can generate questions")

    isg_settings = template.settings or {}
    distribution = isg_settings.get("isg_topic_distribution", [])
    if not distribution:
        raise ValidationError("Template does not have ISG topic distribution.")

    total_requested = sum(d["question_count"] for d in distribution)

    request_data = {
        "question_types": data.question_types,
        "difficulty": data.difficulty,
        "use_rag": data.use_rag,
        "rubric_id": data.rubric_id,
    }

    task = generate_isg.apply_async(
        args=[str(parsed_id), request_data, str(user.id)],
        queue="generation",
    )

    return ISGGenerateTaskOut(
        task_id=task.id,
        template_id=parsed_id,
        total_topics=len(distribution),
        total_requested=total_requested,
    )


@router.get("/tasks/{task_id}", response_model=ISGTaskStatusOut)
async def get_task_status(
    task_id: str,
    _user: User = Depends(require_instructor),
) -> ISGTaskStatusOut:
    """Poll the status of an ISG generation task."""
    from celery.result import AsyncResult

    from src.tasks.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return ISGTaskStatusOut(task_id=task_id, status="pending")

    if result.state == "STARTED":
        return ISGTaskStatusOut(task_id=task_id, status="started")

    if result.state == "GENERATING":
        meta = result.info or {}
        template_id = meta.get("template_id")
        return ISGTaskStatusOut(
            task_id=task_id,
            status="generating",
            template_id=template_id,
            total_generated=meta.get("total_generated", 0),
            total_requested=meta.get("total_requested", 0),
            topic_progress=[
                ISGTaskProgressTopic(**tp) for tp in meta.get("topic_progress", [])
            ],
            current_topic=meta.get("current_topic"),
        )

    if result.state == "SUCCESS":
        data = result.result or {}
        template_id = data.get("template_id")
        return ISGTaskStatusOut(
            task_id=task_id,
            status="completed",
            template_id=template_id,
            total_generated=data.get("total_generated", 0),
            total_requested=data.get("total_requested", 0),
            topic_progress=[
                ISGTaskProgressTopic(**tp) for tp in data.get("topic_progress", [])
            ],
        )

    if result.state == "FAILURE":
        error_msg = str(result.info) if result.info else "Unknown error"
        return ISGTaskStatusOut(
            task_id=task_id,
            status="failed",
            error=error_msg,
        )

    return ISGTaskStatusOut(task_id=task_id, status=result.state.lower())
