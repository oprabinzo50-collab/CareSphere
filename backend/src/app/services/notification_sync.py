from typing import Any

from sqlalchemy.orm import Session

from app.services.notification_persistence import (
    synchronize_patient_notifications,
)
from app.services.patient_notifications import (
    generate_patient_notifications,
)


def synchronize_patient_notification_inbox(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    generated = generate_patient_notifications(
        db=db,
        patient_id=patient_id,
    )

    generated_notifications = generated.get(
        "notifications",
        [],
    )

    result = synchronize_patient_notifications(
        db=db,
        patient_id=patient_id,
        generated_notifications=(
            generated_notifications
        ),
    )

    return {
        "patient_id": patient_id,
        "notification_status": generated.get(
            "status",
            "no_notifications",
        ),
        "generated_count": result.get(
            "generated_count",
            0,
        ),
        "created_count": result.get(
            "created_count",
            0,
        ),
        "existing_count": result.get(
            "existing_count",
            0,
        ),
        "resolved_count": result.get(
            "resolved_count",
            0,
        ),
        "created": result.get(
            "created",
            [],
        ),
    }