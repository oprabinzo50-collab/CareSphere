from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.assessment_sessions import AssessmentSession
    from app.models.user import User
    from app.models.clinician_reviews import ClinicianReview


class Report(Base):
    __tablename__ = "reports"

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

    report_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    report_title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    report_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    executive_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendations_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    limitations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    generated_by: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    ai_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    assessment: Mapped["AssessmentSession"] = orm_relationship(
        "AssessmentSession",
        back_populates="reports",
    )

    creator: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="reports_created",
    )

    clinician_reviews: Mapped[list["ClinicianReview"]] = orm_relationship(
        "ClinicianReview",
        back_populates="report",
    )