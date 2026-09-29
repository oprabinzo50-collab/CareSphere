from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment_sessions import AssessmentSession
    from app.models.assessment_answers import AssessmentAnswer
    from app.models.recommendations import Recommendation


class HealthConcern(Base):
    __tablename__ = "health_concerns"

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

    concern_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    onset_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    duration_description: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    severity: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    frequency: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    impact_on_daily_life: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    patient_priority: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    urgent_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    patient_reported: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    assessment: Mapped["AssessmentSession"] = orm_relationship(
        "AssessmentSession",
        back_populates="health_concerns",
    )

    answers: Mapped[list["AssessmentAnswer"]] = orm_relationship(
        "AssessmentAnswer",
        back_populates="health_concern",
    )

    recommendations: Mapped[list["Recommendation"]] = orm_relationship(
        "Recommendation",
        back_populates="health_concern",
    )