from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.patient_contacts import PatientContact
    from app.models.medical_history import MedicalHistory
    from app.models.allergies import Allergy
    from app.models.medications import Medication
    from app.models.vital_signs import VitalSign
    from app.models.lifestyle import Lifestyle
    from app.models.assessment_sessions import AssessmentSession
    from app.models.clinician_assignments import ClinicianAssignment


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    sex: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    marital_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    occupation: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    preferred_language: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    residence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
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

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    creator: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="patients_created",
    )

    contacts: Mapped[list["PatientContact"]] = orm_relationship(
        "PatientContact",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    medical_history: Mapped[list["MedicalHistory"]] = orm_relationship(
        "MedicalHistory",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    allergies: Mapped[list["Allergy"]] = orm_relationship(
        "Allergy",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    medications: Mapped[list["Medication"]] = orm_relationship(
        "Medication",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    vital_signs: Mapped[list["VitalSign"]] = orm_relationship(
        "VitalSign",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    lifestyle: Mapped[list["Lifestyle"]] = orm_relationship(
        "Lifestyle",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    assessment_sessions: Mapped[list["AssessmentSession"]] = orm_relationship(
        "AssessmentSession",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    clinician_assignments: Mapped[list["ClinicianAssignment"]] = orm_relationship(
        "ClinicianAssignment",
        back_populates="patient",
        cascade="all, delete-orphan",
    )