from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment_sessions import AssessmentSession
    from app.models.health_concerns import HealthConcern
    from app.models.user import User
    from app.models.clinician_reviews import ClinicianReview


class Recommendation(Base):
    __tablename__ = "recommendations"

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

    health_concern_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("health_concerns.id"),
        nullable=True,
    )

    recommendation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    recommendation_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    priority: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    source_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    clinician_review_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    assessment: Mapped["AssessmentSession"] = orm_relationship(
        "AssessmentSession",
        back_populates="recommendations",
    )

    health_concern: Mapped["HealthConcern | None"] = orm_relationship(
        "HealthConcern",
        back_populates="recommendations",
    )

    creator: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="recommendations_created",
    )

    clinician_reviews: Mapped[list["ClinicianReview"]] = orm_relationship(
        "ClinicianReview",
        back_populates="recommendation",
    )