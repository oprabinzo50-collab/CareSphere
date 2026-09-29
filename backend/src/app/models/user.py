from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.recommendations import Recommendation
    from app.models.reports import Report
    from app.models.clinician_reviews import ClinicianReview
    from app.models.audit_logs import AuditLog
    from app.models.patient import Patient
    from app.models.medical_history import MedicalHistory
    from app.models.allergies import Allergy
    from app.models.medications import Medication
    from app.models.vital_signs import VitalSign
    from app.models.lifestyle import Lifestyle
    from app.models.assessment_sessions import AssessmentSession
    from app.models.assessment_answers import AssessmentAnswer
    from app.models.clinician_assignments import ClinicianAssignment


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    recommendations_created: Mapped[list["Recommendation"]] = orm_relationship(
        "Recommendation",
        back_populates="creator",
    )

    reports_created: Mapped[list["Report"]] = orm_relationship(
        "Report",
        back_populates="creator",
    )

    clinician_reviews: Mapped[list["ClinicianReview"]] = orm_relationship(
        "ClinicianReview",
        back_populates="clinician",
    )

    audit_logs: Mapped[list["AuditLog"]] = orm_relationship(
        "AuditLog",
        back_populates="user",
    )

    patients_created: Mapped[list["Patient"]] = orm_relationship(
        "Patient",
        back_populates="creator",
    )

    medical_history_recorded: Mapped[list["MedicalHistory"]] = orm_relationship(
        "MedicalHistory",
        back_populates="recorder",
    )

    allergies_recorded: Mapped[list["Allergy"]] = orm_relationship(
        "Allergy",
        back_populates="recorder",
    )

    medications_recorded: Mapped[list["Medication"]] = orm_relationship(
        "Medication",
        back_populates="recorder",
    )

    vital_signs_recorded: Mapped[list["VitalSign"]] = orm_relationship(
        "VitalSign",
        back_populates="recorder",
    )

    lifestyles_recorded: Mapped[list["Lifestyle"]] = orm_relationship(
        "Lifestyle",
        back_populates="recorder",
    )

    assessments_assessed: Mapped[list["AssessmentSession"]] = orm_relationship(
        "AssessmentSession",
        back_populates="assessor",
    )

    answers_recorded: Mapped[list["AssessmentAnswer"]] = orm_relationship(
        "AssessmentAnswer",
        back_populates="answerer",
    )

    clinician_assignments: Mapped[list["ClinicianAssignment"]] = orm_relationship(
        "ClinicianAssignment",
        foreign_keys="ClinicianAssignment.clinician_id",
        back_populates="clinician",
    )

    assignments_created: Mapped[list["ClinicianAssignment"]] = orm_relationship(
        "ClinicianAssignment",
        foreign_keys="ClinicianAssignment.assigned_by",
        back_populates="assigner",
    )