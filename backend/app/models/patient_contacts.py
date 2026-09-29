from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base
if TYPE_CHECKING:
    from app.models.patient import Patient

class PatientContact(Base):
    __tablename__ = "patient_contacts"

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

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    next_of_kin: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    next_of_kin_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    emergency_contact: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    emergency_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    relationship: Mapped[str | None] = mapped_column(
        String(100),
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
    back_populates="contacts",
)
    patient: Mapped["Patient"] = orm_relationship(
    "Patient",
    back_populates="contacts",
)