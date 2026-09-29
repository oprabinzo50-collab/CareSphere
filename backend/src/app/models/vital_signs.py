from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.assessment_sessions import AssessmentSession
    from app.models.user import User


class VitalSign(Base):
    __tablename__ = "vital_signs"

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

    height: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    weight: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    bmi: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    blood_pressure_systolic: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    blood_pressure_diastolic: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    pulse: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    temperature: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )

    oxygen_saturation: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    recorded_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    assessment_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("assessment_sessions.id"),
        nullable=True,
    )

    patient: Mapped["Patient"] = orm_relationship(
        "Patient",
        back_populates="vital_signs",
    )

    assessment: Mapped["AssessmentSession | None"] = orm_relationship(
        "AssessmentSession",
        back_populates="vital_signs",
    )

    recorder: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="vital_signs_recorded",
    )