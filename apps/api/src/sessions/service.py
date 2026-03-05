import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from src.exams.repository import ExamTemplateRepository
from src.questions.repository import QuestionItemRepository
from src.sessions.models import ExamSession, Response
from src.sessions.repository import ResponseRepository, SessionRepository
from src.sessions.schemas import ResponseSubmit


class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.session_repo = SessionRepository(db)
        self.response_repo = ResponseRepository(db)
        self.template_repo = ExamTemplateRepository(db)
        self.question_repo = QuestionItemRepository(db)

    async def create_session(
        self, template_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamSession:
        template = await self.template_repo.get_by_id(template_id)
        if template is None:
            raise NotFoundError("Exam template not found")
        if not template.is_published:
            raise ValidationError("Cannot start a session for an unpublished template")

        questions, _ = await self.question_repo.list_by_template(
            template_id, is_active=True
        )
        if not questions:
            raise ValidationError("Template has no active questions")

        question_ids = [str(q.id) for q in questions]
        if template.shuffle_questions:
            random.shuffle(question_ids)

        return await self.session_repo.create(
            template_id=template_id,
            user_id=user_id,
            status="created",
            question_order=question_ids,
        )

    async def start_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamSession:
        session = await self._get_user_session(session_id, user_id)
        if session.status != "created":
            raise ValidationError(
                f"Cannot start session in '{session.status}' status"
            )

        now = datetime.now(UTC)
        expires_at: datetime | None = None
        template = await self.template_repo.get_by_id(session.template_id)
        if template is not None and template.time_limit_minutes is not None:
            expires_at = now + timedelta(minutes=template.time_limit_minutes)

        return await self.session_repo.update(
            session,
            status="in_progress",
            started_at=now,
            expires_at=expires_at,
        )

    async def submit_response(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ResponseSubmit,
    ) -> Response:
        session = await self._get_user_session(session_id, user_id)
        if session.status != "in_progress":
            raise ValidationError("Session is not in progress")
        self._check_expired(session)

        return await self.response_repo.upsert(
            session_id=session_id,
            question_id=data.question_id,
            answer=data.answer,
            time_spent_seconds=data.time_spent_seconds,
            is_flagged=data.is_flagged,
        )

    async def submit_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamSession:
        session = await self._get_user_session(session_id, user_id)
        if session.status != "in_progress":
            raise ValidationError(
                f"Cannot submit session in '{session.status}' status"
            )

        return await self.session_repo.update(
            session,
            status="submitted",
            submitted_at=datetime.now(UTC),
        )

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID, user_role: str
    ) -> ExamSession:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError("Session not found")
        if user_role != "admin" and session.user_id != user_id:
            template = await self.template_repo.get_by_id(session.template_id)
            if template is None or (
                user_role == "instructor" and template.created_by != user_id
            ):
                raise ForbiddenError("Access denied")
        return session

    async def get_session_result(
        self, session_id: uuid.UUID, user_id: uuid.UUID, user_role: str
    ) -> ExamSession:
        session = await self.session_repo.get_with_responses(session_id)
        if session is None:
            raise NotFoundError("Session not found")
        if user_role != "admin" and session.user_id != user_id:
            template = await self.template_repo.get_by_id(session.template_id)
            if template is None or (
                user_role == "instructor" and template.created_by != user_id
            ):
                raise ForbiddenError("Access denied")
        return session

    async def list_sessions(
        self,
        *,
        user_id: uuid.UUID,
        user_role: str,
        template_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ExamSession], int]:
        if user_role == "admin":
            return await self.session_repo.list_sessions(
                template_id=template_id, status=status,
                page=page, page_size=page_size,
            )
        elif user_role == "student":
            return await self.session_repo.list_sessions(
                user_id=user_id, template_id=template_id, status=status,
                page=page, page_size=page_size,
            )
        else:
            return await self.session_repo.list_sessions(
                template_id=template_id, status=status,
                page=page, page_size=page_size,
            )

    async def _get_user_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamSession:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError("Session not found")
        if session.user_id != user_id:
            raise ForbiddenError("This is not your session")
        return session

    def _check_expired(self, session: ExamSession) -> None:
        if session.expires_at is not None and datetime.now(UTC) > session.expires_at:
            raise ValidationError("Session has expired")
