"""AI service orchestrating question generation with RAG and verification."""

from __future__ import annotations

import json
import uuid

import jinja2
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.models import ModelTrace
from src.ai.prompts.generator import (
    PROMPT_ID_QUESTION_GENERATION,
    QUESTION_GENERATION_SYSTEM,
    QUESTION_GENERATION_USER,
)
from src.ai.prompts.registry import PromptRegistry
from src.ai.providers.base import AIProvider, AIResponse
from src.ai.providers.groq_provider import GroqProvider
from src.ai.rag.retriever import Retriever
from src.ai.schemas import GeneratedQuestion, GenerateRequest
from src.ai.verification.language_checker import check_language
from src.ai.verification.leak_detector import detect_answer_leak
from src.ai.verification.schema_validator import validate_generated_questions


class AIService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.prompt_registry = PromptRegistry(db)
        self.retriever = Retriever(db)

    def _get_provider(self, provider_name: str = "groq") -> AIProvider:
        if provider_name == "anthropic":
            from src.ai.providers.anthropic_provider import AnthropicProvider

            return AnthropicProvider()
        return GroqProvider()

    async def generate_questions(
        self,
        request: GenerateRequest,
        user_id: uuid.UUID,
    ) -> tuple[list[GeneratedQuestion], list[str], uuid.UUID | None]:
        """Generate questions using AI with optional RAG context.

        Returns:
            Tuple of (generated questions, error messages, model trace ID)
        """
        # 1. Get RAG context if enabled
        context = ""
        if request.use_rag:
            context = await self.retriever.retrieve(
                request.template_id,
                f"{request.topic} {request.subtopic or ''}",
            )

        # 2. Build prompt from registry or defaults
        system_prompt = QUESTION_GENERATION_SYSTEM
        user_template = QUESTION_GENERATION_USER

        db_prompt = await self.prompt_registry.get_active_prompt(
            PROMPT_ID_QUESTION_GENERATION
        )
        prompt_version: int | None = None
        if db_prompt:
            user_template = db_prompt.template_text
            if db_prompt.system_prompt:
                system_prompt = db_prompt.system_prompt
            prompt_version = db_prompt.version

        # 3. Render Jinja2 template
        env = jinja2.Environment(autoescape=False)
        tmpl = env.from_string(user_template)
        user_prompt = tmpl.render(
            count=request.count,
            topic=request.topic,
            subtopic=request.subtopic,
            question_type=request.question_type,
            locale=request.locale,
            difficulty=request.difficulty,
            context=context,
        )

        # 4. Call AI provider
        provider = self._get_provider("anthropic")
        trace_id: uuid.UUID | None = None
        ai_response: AIResponse | None = None
        error_msg: str | None = None

        try:
            ai_response = await provider.generate_with_timing(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_mode=True,
                temperature=0.7,
                max_tokens=4096,
            )
        except Exception as e:
            error_msg = str(e)

        # 5. Log model trace
        trace = ModelTrace(
            provider=provider.provider_name,
            model=provider.default_model,
            task_type="generation",
            prompt_id=PROMPT_ID_QUESTION_GENERATION,
            prompt_version=prompt_version,
            input_tokens=ai_response.input_tokens if ai_response else None,
            output_tokens=ai_response.output_tokens if ai_response else None,
            latency_ms=ai_response.latency_ms if ai_response else None,
            status="success" if ai_response else "error",
            error_message=error_msg,
            template_id=request.template_id,
            user_id=user_id,
        )
        self.db.add(trace)
        await self.db.flush()
        await self.db.refresh(trace)
        trace_id = trace.id

        if ai_response is None:
            return [], [error_msg or "AI generation failed"], trace_id

        # 6. Parse JSON response
        try:
            data = json.loads(ai_response.content)
            raw_questions = data.get("questions", [])
        except json.JSONDecodeError as e:
            return [], [f"Failed to parse AI response as JSON: {e}"], trace_id

        if not isinstance(raw_questions, list):
            return [], ["AI response 'questions' field is not a list"], trace_id

        # 7. Validate with Pydantic schemas
        valid_questions, validation_errors = validate_generated_questions(
            raw_questions, expected_type=request.question_type
        )

        # 8. Run verification pipeline on valid questions
        generated: list[GeneratedQuestion] = []
        for q in valid_questions:
            warnings: list[str] = []

            # Leak detection
            leaks = detect_answer_leak(
                q.stem, q.correct_answer, [o.model_dump() for o in q.options] if q.options else None
            )
            warnings.extend(leaks)

            # Language check
            if not check_language(q.stem, request.locale):
                warnings.append(f"Question may not be in {request.locale}")

            generated.append(
                GeneratedQuestion(
                    stem=q.stem,
                    question_type=q.question_type,
                    options=[o.model_dump() for o in q.options] if q.options else None,
                    correct_answer=q.correct_answer,
                    explanation=q.explanation,
                    topic=q.topic,
                    subtopic=q.subtopic,
                    difficulty=q.difficulty,
                    warnings=warnings,
                )
            )

        return generated, validation_errors, trace_id
