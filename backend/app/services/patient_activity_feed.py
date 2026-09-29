from typing import Any

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.patient_timeline import (
    generate_patient_timeline,
)


def generate_patient_activity_feed(
    db: Session,
    patient_id: int,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:

    patient = db.get(Patient, patient_id)

    if patient is None:
        raise ValueError("Patient not found")

    timeline_result = generate_patient_timeline(
        db=db,
        patient_id=patient_id,
    )

    timeline = timeline_result.get(
        "timeline",
        [],
    )

    total_events = len(timeline)

    paginated_events = timeline[
        offset: offset + limit
    ]

    activity_feed: list[dict[str, Any]] = []

    activity_titles = {
        "assessment": "Assessment",
        "health_concern": "Health concern",
        "vital_sign": "Vital signs recorded",
        "lifestyle": "Lifestyle information updated",
        "medication": "Medication recorded",
        "allergy": "Allergy recorded",
        "medical_history": "Medical history recorded",
        "recommendation": "Recommendation",
        "report": "Assessment report",
        "clinician_review": "Clinician review",
    }

    for event in paginated_events:

        event_type = event.get(
            "event_type",
            "unknown",
        )

        title = event.get(
            "title"
        )

        if not title:
            title = activity_titles.get(
                event_type,
                "Patient activity",
            )

        activity_feed.append(
            {
                "activity_type": event_type,
                "activity_id": event.get(
                    "event_id"
                ),
                "assessment_id": event.get(
                    "assessment_id"
                ),
                "occurred_at": event.get(
                    "occurred_at"
                ),
                "title": title,
                "status": event.get(
                    "status"
                ),
                "data": event.get(
                    "data",
                    {},
                ),
            }
        )

    # ---------------------------------------------------------
    # Activity counts
    # ---------------------------------------------------------

    activity_counts: dict[str, int] = {}

    for event in timeline:

        event_type = event.get(
            "event_type",
            "unknown",
        )

        activity_counts[event_type] = (
            activity_counts.get(
                event_type,
                0,
            )
            + 1
        )

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    has_more = (
        offset + limit < total_events
    )

    next_offset = (
        offset + limit
        if has_more
        else None
    )

    return {
        "patient": {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "status": patient.status,
        },
        "total_events": total_events,
        "limit": limit,
        "offset": offset,
        "returned_events": len(
            activity_feed
        ),
        "has_more": has_more,
        "next_offset": next_offset,
        "activity_counts": activity_counts,
        "activities": activity_feed,
    }