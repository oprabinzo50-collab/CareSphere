from typing import Any

from sqlalchemy.orm import Session

from app.services.notification_sync import (
    synchronize_patient_notification_inbox,
)


def trigger_assessment_completion_notifications(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:
    """
    Synchronize persistent notifications after an
    assessment is completed.
    """

    return synchronize_patient_notification_inbox(
        db=db,
        patient_id=patient_id,
    )