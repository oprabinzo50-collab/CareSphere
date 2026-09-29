from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit_logs import AuditLog


def create_audit_log(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    log_metadata: dict | None = None,
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        log_metadata=log_metadata,
        created_at=datetime.now(timezone.utc),
    )

    db.add(audit_log)

    return audit_log