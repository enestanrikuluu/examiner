from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ItemParameter(Base):
    """Calibrated IRT parameters for a question item.

    Stores the latest calibrated a (discrimination) and b (difficulty)
    parameters, along with calibration metadata.
    """

    __tablename__ = "item_parameters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    a: Mapped[float] = mapped_column(
        Numeric(6, 4), nullable=False, default=1.0
    )
    b: Mapped[float] = mapped_column(
        Numeric(6, 3), nullable=False, default=0.0
    )
    se_a: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    se_b: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    response_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    calibration_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    calibration_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    calibrated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ThetaHistory(Base):
    """History of theta estimates during an adaptive session.

    Each row represents a theta update after a response is submitted.
    """

    __tablename__ = "theta_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_items.id"),
        nullable=False,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    theta: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    se: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    information: Mapped[float | None] = mapped_column(
        Numeric(8, 4), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
