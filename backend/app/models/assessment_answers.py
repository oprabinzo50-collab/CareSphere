from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment_sessions import AssessmentSession
    from app.models.assessment_questions import AssessmentQuestion
    from app.models.health_concerns import HealthConcern
    from app.models.user import User


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    assessment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("assessment_sessions.id"),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("assessment_questions.id"),
        nullable=False,
    )

    health_concern_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("health_concerns.id"),
        nullable=True,
    )

    answer_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    answer_number: Mapped[float | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    answer_boolean: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    answer_json: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    answered_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    assessment: Mapped["AssessmentSession"] = orm_relationship(
        "AssessmentSession",
        back_populates="answers",
    )

    question: Mapped["AssessmentQuestion"] = orm_relationship(
        "AssessmentQuestion",
        back_populates="answers",
    )

    health_concern: Mapped["HealthConcern | None"] = orm_relationship(
        "HealthConcern",
        back_populates="answers",
    )

    answerer: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="answers_recorded",
    )