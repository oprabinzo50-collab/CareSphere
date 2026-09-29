from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment_answers import AssessmentAnswer


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    question_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    options: Mapped[dict | list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    answers: Mapped[list["AssessmentAnswer"]] = orm_relationship(
        "AssessmentAnswer",
        back_populates="question",
    )