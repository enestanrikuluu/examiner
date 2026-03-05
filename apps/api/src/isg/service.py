"""ISG service: creates ISG exams from blueprints and generates questions per topic."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.schemas import GenerateRequest
from src.ai.service import AIService
from src.core.exceptions import NotFoundError, ValidationError
from src.exams.repository import ExamTemplateRepository
from src.isg.blueprints import TOPICS_BY_ID, get_blueprint
from src.isg.rubrics import get_rubric, get_rubric_for_topic
from src.isg.schemas import (
    ISGExamCreate,
    ISGExamOut,
    ISGGenerateRequest,
    ISGGenerateResultOut,
    ISGGenerateTopicResult,
    TopicWeightOut,
)
from src.questions.repository import QuestionItemRepository
from src.questions.schemas import QuestionItemCreate


class ISGService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.template_repo = ExamTemplateRepository(db)
        self.question_repo = QuestionItemRepository(db)

    async def create_exam(
        self,
        data: ISGExamCreate,
        user_id: uuid.UUID,
    ) -> ISGExamOut:
        """Create an exam template pre-configured from an ISG blueprint."""
        exam_class = data.exam_class.upper()
        blueprint = get_blueprint(exam_class)
        if blueprint is None:
            raise NotFoundError(f"Blueprint for class '{exam_class}' not found")

        # Resolve topic distribution (apply overrides if any)
        topic_distribution = self._resolve_distribution(data, blueprint)

        total_questions = sum(tw.question_count for tw in topic_distribution)

        title = data.title or blueprint.title
        description = data.description or blueprint.description
        time_limit = data.time_limit_minutes or blueprint.time_limit_minutes
        pass_score = data.pass_score if data.pass_score is not None else blueprint.pass_score

        # Store ISG metadata in template settings
        settings = {
            "isg_exam_class": exam_class,
            "isg_topic_distribution": [
                {
                    "topic_id": tw.topic_id,
                    "topic_name": tw.topic_name,
                    "weight": tw.weight,
                    "question_count": tw.question_count,
                }
                for tw in topic_distribution
            ],
        }

        template = await self.template_repo.create(
            title=title,
            description=description,
            org_id=data.org_id,
            locale="tr-TR",
            time_limit_minutes=time_limit,
            pass_score=pass_score,
            question_count=total_questions,
            shuffle_questions=data.shuffle_questions,
            shuffle_options=data.shuffle_options,
            exam_mode="mock",
            settings=settings,
            created_by=user_id,
        )

        return ISGExamOut(
            template_id=template.id,
            exam_class=exam_class,
            title=title,
            total_questions=total_questions,
            topic_distribution=topic_distribution,
        )

    async def generate_questions(
        self,
        data: ISGGenerateRequest,
        user_id: uuid.UUID,
    ) -> ISGGenerateResultOut:
        """Generate questions for all topics in an ISG exam template.

        Reads the topic distribution from the template settings and
        generates questions per topic using the AI service.
        """
        template = await self.template_repo.get_by_id(data.template_id)
        if template is None:
            raise NotFoundError("Template not found")

        if template.created_by != user_id:
            raise ValidationError("Only the template owner can generate questions")

        isg_settings = template.settings or {}
        distribution = isg_settings.get("isg_topic_distribution", [])

        if not distribution:
            raise ValidationError(
                "Template does not have ISG topic distribution. "
                "Create the exam using the ISG blueprint first."
            )

        ai_service = AIService(self.db)
        total_generated = 0
        total_requested = 0
        topic_results: list[ISGGenerateTopicResult] = []
        trace_ids: list[uuid.UUID] = []

        for topic_entry in distribution:
            topic_id = topic_entry["topic_id"]
            topic_name = topic_entry["topic_name"]
            question_count = topic_entry["question_count"]
            total_requested += question_count

            if question_count == 0:
                topic_results.append(
                    ISGGenerateTopicResult(
                        topic_id=topic_id,
                        topic_name=topic_name,
                        requested_count=0,
                        generated_count=0,
                    )
                )
                continue

            topic_obj = TOPICS_BY_ID.get(topic_id)

            # Pick question types round-robin
            question_types = data.question_types or ["mcq"]
            topic_errors: list[str] = []
            generated_for_topic = 0

            # Generate in batches per question type
            for qt_idx, qt in enumerate(question_types):
                # Distribute count across types
                base = question_count // len(question_types)
                extra = 1 if qt_idx < (question_count % len(question_types)) else 0
                count_for_type = base + extra

                if count_for_type == 0:
                    continue

                # Determine rubric for long_form
                rubric_dict = None
                if qt == "long_form":
                    rubric = None
                    if data.rubric_id:
                        rubric = get_rubric(data.rubric_id)
                    if rubric is None:
                        rubric = get_rubric_for_topic(topic_id)
                    if rubric is not None:
                        rubric_dict = rubric.to_dict()

                gen_request = GenerateRequest(
                    template_id=data.template_id,
                    question_type=qt,
                    topic=topic_name,
                    subtopic=None,
                    count=count_for_type,
                    difficulty=data.difficulty,
                    locale="tr-TR",
                    use_rag=data.use_rag,
                )

                questions, errors, trace_id = await ai_service.generate_questions(
                    gen_request, user_id
                )
                topic_errors.extend(errors)

                if trace_id is not None:
                    trace_ids.append(trace_id)

                # Save generated questions to the template
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
                    await self.question_repo.create(
                        template_id=data.template_id,
                        **create_data.model_dump(exclude_unset=True),
                    )
                    generated_for_topic += 1

            total_generated += generated_for_topic
            topic_results.append(
                ISGGenerateTopicResult(
                    topic_id=topic_id,
                    topic_name=topic_name,
                    requested_count=question_count,
                    generated_count=generated_for_topic,
                    errors=topic_errors,
                )
            )

        return ISGGenerateResultOut(
            template_id=data.template_id,
            total_generated=total_generated,
            total_requested=total_requested,
            topic_results=topic_results,
            trace_ids=trace_ids,
        )

    @staticmethod
    def _resolve_distribution(
        data: ISGExamCreate,
        blueprint: object,
    ) -> list[TopicWeightOut]:
        """Compute final topic distribution, applying any overrides."""
        from src.isg.blueprints import Blueprint

        assert isinstance(blueprint, Blueprint)

        overrides: dict[str, int] = {}
        if data.topic_overrides:
            overrides = {o.topic_id: o.question_count for o in data.topic_overrides}

        result: list[TopicWeightOut] = []
        for tw in blueprint.topic_weights:
            topic = TOPICS_BY_ID.get(tw.topic_id)
            topic_name = topic.name if topic else tw.topic_id
            question_count = overrides.get(tw.topic_id, tw.question_count)

            result.append(
                TopicWeightOut(
                    topic_id=tw.topic_id,
                    topic_name=topic_name,
                    weight=tw.weight,
                    question_count=question_count,
                )
            )

        return result
