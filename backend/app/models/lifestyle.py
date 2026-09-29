from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User


class Lifestyle(Base):
    __tablename__ = "lifestyle"

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

    smoking_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    alcohol_use: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    physical_activity_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    exercise_frequency: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    diet_pattern: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    sleep_duration_hours: Mapped[float | None] = mapped_column(
        Numeric(4, 1),
        nullable=True,
    )

    sleep_quality: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    stress_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    additional_notes: Mapped[str | None] = mapped_column(
        Text,
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

    patient: Mapped["Patient"] = orm_relationship(
        "Patient",
        back_populates="lifestyle",
    )

    recorder: Mapped["User | None"] = orm_relationship(
        "User",
        back_populates="lifestyles_recorded",
    )