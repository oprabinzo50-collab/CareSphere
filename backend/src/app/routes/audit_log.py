from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.audit_logs import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.security.permissions import require_roles

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def list_audit_logs(
    user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("administrator")
    ),
):
    statement = select(AuditLog).order_by(
        AuditLog.created_at.desc()
    )

    if user_id is not None:
        statement = statement.where(
            AuditLog.user_id == user_id
        )

    if action is not None:
        statement = statement.where(
            AuditLog.action == action
        )

    if entity_type is not None:
        statement = statement.where(
            AuditLog.entity_type == entity_type
        )

    statement = statement.limit(limit)

    return list(db.scalars(statement).all())


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("administrator")
    ),
):
    audit_log = db.get(AuditLog, audit_log_id)

    if audit_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return audit_log