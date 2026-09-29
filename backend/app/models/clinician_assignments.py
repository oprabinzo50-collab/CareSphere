from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.patient import Patient


class ClinicianAssignment(Base):
    __tablename__ = "clinician_assignments"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )

    clinician_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    assigned_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    care_role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="primary",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
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

    patient: Mapped["Patient"] = orm_relationship(
        "Patient",
        back_populates="clinician_assignments",
    )

    clinician: Mapped["User"] = orm_relationship(
        "User",
        foreign_keys=[clinician_id],
        back_populates="clinician_assignments",
    )

    assigner: Mapped["User | None"] = orm_relationship(
        "User",
        foreign_keys=[assigned_by],
        back_populates="assignments_created",
    )


Index(
    "uq_active_patient_clinician_assignment",
    ClinicianAssignment.patient_id,
    ClinicianAssignment.clinician_id,
    unique=True,
    postgresql_where=text("status = 'active'"),
)

Index(
    "uq_active_primary_clinician_per_patient",
    ClinicianAssignment.patient_id,
    unique=True,
    postgresql_where=text(
        "status = 'active' AND care_role = 'primary'"
    ),
)

Index(
    "ix_clinician_assignments_patient_id",
    ClinicianAssignment.patient_id,
)

Index(
    "ix_clinician_assignments_clinician_id",
    ClinicianAssignment.clinician_id,
)

Index(
    "ix_clinician_assignments_status",
    ClinicianAssignment.status,
)