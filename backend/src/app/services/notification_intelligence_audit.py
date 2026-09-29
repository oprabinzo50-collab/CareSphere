from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_logs import AuditLog


def record_notification_intelligence_audit(
    db: Session,
    *,
    user_id: int | None,
    patient_id: int,
    action: str,
    description: str,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type="patient",
        entity_id=patient_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        log_metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_notification_intelligence_audit_logs(
    db: Session,
    *,
    patient_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    statement = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == "patient",
            AuditLog.entity_id == patient_id,
            AuditLog.action.in_(
                {
                    "notification_intelligence_search",
                    "notification_intelligence_report",
                }
            ),
        )
        .order_by(
            AuditLog.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


def serialize_notification_intelligence_audit(
    audit_log: AuditLog,
) -> dict[str, Any]:
    return {
        "id": audit_log.id,
        "user_id": audit_log.user_id,
        "action": audit_log.action,
        "entity_type": audit_log.entity_type,
        "entity_id": audit_log.entity_id,
        "description": audit_log.description,
        "ip_address": (
            str(audit_log.ip_address)
            if audit_log.ip_address is not None
            else None
        ),
        "user_agent": audit_log.user_agent,
        "metadata": audit_log.log_metadata,
        "created_at": (
            audit_log.created_at.isoformat()
            if audit_log.created_at
            else None
        ),
    }