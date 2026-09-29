from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.reports import Report
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportUpdate,
)
from app.security.permissions import require_roles
from app.services.report_notification_automation import (
    trigger_report_notifications,
)


router = APIRouter(
    prefix="/assessments",
    tags=["Reports"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{assessment_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    assessment_id: int,
    report_data: ReportCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    now = datetime.now(timezone.utc)

    report = Report(
        assessment_id=assessment_id,
        **report_data.model_dump(),
        generated_at=now,
        created_by=current_user.id,
        updated_at=now,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    trigger_report_notifications(
        db=db,
        report=report,
    )

    return report


@router.get(
    "/{assessment_id}/reports",
    response_model=list[ReportResponse],
)
def list_reports(
    assessment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    statement = (
        select(Report)
        .where(
            Report.assessment_id == assessment_id
        )
        .order_by(Report.id.desc())
    )

    return db.scalars(statement).all()


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
)
def get_report(
    report_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    report = db.get(
        Report,
        report_id,
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return report


@router.put(
    "/reports/{report_id}",
    response_model=ReportResponse,
)
def update_report(
    report_id: int,
    report_data: ReportUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    report = db.get(
        Report,
        report_id,
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    previous_status = str(
        getattr(
            report,
            "status",
            "",
        )
    ).lower()

    update_data = report_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            report,
            field,
            value,
        )

    report.updated_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(report)

    current_status = str(
        getattr(
            report,
            "status",
            "",
        )
    ).lower()

    entered_review_required_state = (
        current_status
        in {
            "draft",
            "pending_review",
            "awaiting_review",
        }
        and previous_status
        not in {
            "draft",
            "pending_review",
            "awaiting_review",
        }
    )

    if entered_review_required_state:
        trigger_report_notifications(
            db=db,
            report=report,
        )

    return report