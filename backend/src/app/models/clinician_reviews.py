from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment_sessions import AssessmentSession
    from app.models.recommendations import Recommendation
    from app.models.reports import Report
    from app.models.user import User


class ClinicianReview(Base):
    __tablename__ = "clinician_reviews"

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

    recommendation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("recommendations.id"),
        nullable=True,
    )

    report_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("reports.id"),
        nullable=True,
    )

    clinician_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    review_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    clinical_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    modification_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    assessment: Mapped["AssessmentSession"] = orm_relationship(
        "AssessmentSession",
        back_populates="clinician_reviews",
    )

    recommendation: Mapped["Recommendation | None"] = orm_relationship(
        "Recommendation",
        back_populates="clinician_reviews",
    )

    report: Mapped["Report | None"] = orm_relationship(
        "Report",
        back_populates="clinician_reviews",
    )

    clinician: Mapped["User"] = orm_relationship(
        "User",
        back_populates="clinician_reviews",
    )