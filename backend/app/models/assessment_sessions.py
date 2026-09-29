from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.health_concerns import HealthConcern
    from app.models.assessment_answers import AssessmentAnswer
    from app.models.recommendations import Recommendation
    from app.models.reports import Report
    from app.models.clinician_reviews import ClinicianReview
    from app.models.user import User
    from app.models.vital_signs import VitalSign


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("patients.id"),
        nullable=False,
    )

    assessment_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="in_progress",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assessed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
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

    patient: Mapped["Patient"] = orm_relationship(
        "Patient",
        back_populates="assessment_sessions",
    )

    assessor: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="assessments_assessed",
    )

    health_concerns: Mapped[list["HealthConcern"]] = orm_relationship(
        "HealthConcern",
        back_populates="assessment",
    )

    answers: Mapped[list["AssessmentAnswer"]] = orm_relationship(
        "AssessmentAnswer",
        back_populates="assessment",
    )

    recommendations: Mapped[list["Recommendation"]] = orm_relationship(
        "Recommendation",
        back_populates="assessment",
    )

    reports: Mapped[list["Report"]] = orm_relationship(
        "Report",
        back_populates="assessment",
    )

    clinician_reviews: Mapped[list["ClinicianReview"]] = orm_relationship(
        "ClinicianReview",
        back_populates="assessment",
    )

    vital_signs: Mapped[list["VitalSign"]] = orm_relationship(
        "VitalSign",
        back_populates="assessment",
    )