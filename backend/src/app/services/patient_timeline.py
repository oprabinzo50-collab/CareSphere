from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.models.allergies import Allergy
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.health_concerns import HealthConcern
from app.models.medical_history import MedicalHistory
from app.models.medications import Medication
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.vital_signs import VitalSign
from app.models.lifestyle import Lifestyle
from app.models.patient import Patient


def serialize_model_columns(obj: Any) -> dict[str, Any]:
    """
    Convert SQLAlchemy model columns into a JSON-safe dictionary.
    """

    data: dict[str, Any] = {}

    mapper = inspect(obj).mapper

    for column in mapper.column_attrs:
        key = column.key
        value = getattr(obj, key)

        if isinstance(value, (datetime, date)):
            value = value.isoformat()

        data[key] = value

    return data


def get_event_timestamp(obj: Any) -> datetime | None:
    """
    Find the most appropriate timestamp for a timeline event.
    """

    timestamp_fields = [
        "occurred_at",
        "recorded_at",
        "started_at",
        "generated_at",
        "reviewed_at",
        "created_at",
        "updated_at",
        "completed_at",
    ]

    for field in timestamp_fields:
        value = getattr(obj, field, None)

        if isinstance(value, datetime):
            return value

    return None


def build_event(
    *,
    event_type: str,
    obj: Any,
    title: str,
    assessment_id: int | None = None,
) -> dict[str, Any]:

    timestamp = get_event_timestamp(obj)

    return {
        "event_type": event_type,
        "event_id": getattr(obj, "id", None),
        "assessment_id": assessment_id,
        "occurred_at": (
            timestamp.isoformat()
            if timestamp is not None
            else None
        ),
        "title": title,
        "status": getattr(obj, "status", None),
        "data": serialize_model_columns(obj),
    }


def generate_patient_timeline(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient not found")

    events: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Medical history
    # ---------------------------------------------------------

    medical_history = list(
        db.scalars(
            select(MedicalHistory)
            .where(MedicalHistory.patient_id == patient_id)
        ).all()
    )

    for item in medical_history:
        title = getattr(
            item,
            "condition_name",
            "Medical history record",
        )

        events.append(
            build_event(
                event_type="medical_history",
                obj=item,
                title=title,
            )
        )

    # ---------------------------------------------------------
    # Allergies
    # ---------------------------------------------------------

    allergies = list(
        db.scalars(
            select(Allergy)
            .where(Allergy.patient_id == patient_id)
        ).all()
    )

    for item in allergies:
        title = (
            getattr(item, "allergen", None)
            or getattr(item, "allergy_name", None)
            or "Allergy record"
        )

        events.append(
            build_event(
                event_type="allergy",
                obj=item,
                title=title,
            )
        )

    # ---------------------------------------------------------
    # Medications
    # ---------------------------------------------------------

    medications = list(
        db.scalars(
            select(Medication)
            .where(Medication.patient_id == patient_id)
        ).all()
    )

    for item in medications:
        title = (
            getattr(item, "medication_name", None)
            or getattr(item, "name", None)
            or "Medication record"
        )

        events.append(
            build_event(
                event_type="medication",
                obj=item,
                title=title,
            )
        )

    # ---------------------------------------------------------
    # Vital signs
    # ---------------------------------------------------------

    vital_signs = list(
        db.scalars(
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id)
        ).all()
    )

    for item in vital_signs:
        events.append(
            build_event(
                event_type="vital_sign",
                obj=item,
                title="Vital signs recorded",
                assessment_id=getattr(
                    item,
                    "assessment_id",
                    None,
                ),
            )
        )

    # ---------------------------------------------------------
    # Lifestyle
    # ---------------------------------------------------------

    lifestyles = list(
        db.scalars(
            select(Lifestyle)
            .where(Lifestyle.patient_id == patient_id)
        ).all()
    )

    for item in lifestyles:
        events.append(
            build_event(
                event_type="lifestyle",
                obj=item,
                title="Lifestyle information recorded",
                assessment_id=getattr(
                    item,
                    "assessment_id",
                    None,
                ),
            )
        )

    # ---------------------------------------------------------
    # Assessments
    # ---------------------------------------------------------

    assessments = list(
        db.scalars(
            select(AssessmentSession)
            .where(
                AssessmentSession.patient_id == patient_id
            )
            .order_by(
                AssessmentSession.started_at.desc()
            )
        ).all()
    )

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    for assessment in assessments:
        events.append(
            build_event(
                event_type="assessment",
                obj=assessment,
                title=(
                    f"Assessment: "
                    f"{assessment.assessment_type}"
                ),
                assessment_id=assessment.id,
            )
        )

    # ---------------------------------------------------------
    # Assessment-linked records
    # ---------------------------------------------------------

    if assessment_ids:

        health_concerns = list(
            db.scalars(
                select(HealthConcern)
                .where(
                    HealthConcern.assessment_id.in_(
                        assessment_ids
                    )
                )
            ).all()
        )

        for item in health_concerns:
            title = (
                getattr(item, "concern_title", None)
                or getattr(item, "title", None)
                or "Health concern"
            )

            events.append(
                build_event(
                    event_type="health_concern",
                    obj=item,
                    title=title,
                    assessment_id=item.assessment_id,
                )
            )

        recommendations = list(
            db.scalars(
                select(Recommendation)
                .where(
                    Recommendation.assessment_id.in_(
                        assessment_ids
                    )
                )
            ).all()
        )

        for item in recommendations:
            title = (
                getattr(item, "title", None)
                or "Recommendation"
            )

            events.append(
                build_event(
                    event_type="recommendation",
                    obj=item,
                    title=title,
                    assessment_id=item.assessment_id,
                )
            )

        reports = list(
            db.scalars(
                select(Report)
                .where(
                    Report.assessment_id.in_(
                        assessment_ids
                    )
                )
            ).all()
        )

        for item in reports:
            title = (
                getattr(item, "report_title", None)
                or "Assessment report"
            )

            events.append(
                build_event(
                    event_type="report",
                    obj=item,
                    title=title,
                    assessment_id=item.assessment_id,
                )
            )

        reviews = list(
            db.scalars(
                select(ClinicianReview)
                .where(
                    ClinicianReview.assessment_id.in_(
                        assessment_ids
                    )
                )
            ).all()
        )

        for item in reviews:
            events.append(
                build_event(
                    event_type="clinician_review",
                    obj=item,
                    title="Clinician review",
                    assessment_id=item.assessment_id,
                )
            )

    # ---------------------------------------------------------
    # Sort newest first
    # ---------------------------------------------------------

    events.sort(
        key=lambda event: event["occurred_at"] or "",
        reverse=True,
    )

    # ---------------------------------------------------------
    # Event counts
    # ---------------------------------------------------------

    counts: dict[str, int] = {}

    for event in events:
        event_type = event["event_type"]
        counts[event_type] = counts.get(event_type, 0) + 1

    return {
        "patient": {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "timeline": events,
        "counts": counts,
        "total_events": len(events),
    }