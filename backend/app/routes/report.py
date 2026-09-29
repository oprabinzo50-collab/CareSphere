from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.patient_report_access import PatientReportAccess
from app.models.patient import Patient
from app.models.reports import Report
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportUpdate,
    ReviewedReportResponse,
)
from app.security.permissions import require_roles
from app.services.report_notification_automation import (
    trigger_report_notifications,
)
from app.utils.audit import create_audit_log


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


def _report_response_payload(db: Session, report: Report) -> dict:
    """Return report data plus latest clinician review and patient-access metadata."""
    review = db.scalar(
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id == report.assessment_id,
            ClinicianReview.report_id == report.id,
        )
        .order_by(ClinicianReview.id.desc())
    )
    access = db.scalar(
        select(PatientReportAccess)
        .where(PatientReportAccess.report_id == report.id)
    )

    return {
        "id": report.id,
        "assessment_id": report.assessment_id,
        "report_type": report.report_type,
        "report_title": report.report_title,
        "report_content": report.report_content,
        "executive_summary": report.executive_summary,
        "recommendations_summary": report.recommendations_summary,
        "limitations": report.limitations,
        "generated_by": report.generated_by,
        "ai_generated": report.ai_generated,
        "version": report.version,
        "status": report.status,
        "generated_at": report.generated_at,
        "created_by": report.created_by,
        "updated_at": report.updated_at,
        "clinician_id": review.clinician_id if review else None,
        "clinician_guidance": review.clinical_comment if review else None,
        "clinician_review_status": review.review_status if review else None,
        "clinician_reviewed_at": review.reviewed_at if review else None,
        "released_to_patient": bool(access) or str(report.status).lower() in {"approved", "completed"},
        "patient_reviewed_at": access.reviewed_at if access else None,
        "last_viewed_at": access.last_viewed_at if access else None,
    }


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

    return _report_response_payload(db, report)


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

    return [_report_response_payload(db, row) for row in db.scalars(statement).all()]


@router.get(
    "/reports/reviewed",
    response_model=list[ReviewedReportResponse],
)
def list_reviewed_reports(
    limit: int = 50,
    current_user: User = Depends(require_roles("administrator")),
    db: Session = Depends(get_db),
):
    """Return reports that have reached a completed clinician review action.

    The endpoint is administrator-only and does not create a second report
    record. It reads the existing report, latest clinician review, linked
    patient, and patient-access state.
    """
    safe_limit = max(1, min(limit, 200))
    latest_review_id = (
        select(func.max(ClinicianReview.id))
        .where(ClinicianReview.report_id == Report.id)
        .correlate(Report)
        .scalar_subquery()
    )

    statement = (
        select(Report, ClinicianReview, Patient, User)
        .join(AssessmentSession, Report.assessment_id == AssessmentSession.id)
        .join(Patient, AssessmentSession.patient_id == Patient.id)
        .join(ClinicianReview, ClinicianReview.id == latest_review_id)
        .join(User, User.id == ClinicianReview.clinician_id)
        .where(
            ClinicianReview.review_status.in_(
                {"reviewed", "approved", "rejected", "completed"}
            )
        )
        .order_by(
            ClinicianReview.reviewed_at.desc().nullslast(),
            ClinicianReview.updated_at.desc(),
            Report.id.desc(),
        )
        .limit(safe_limit)
    )

    results = []
    for report, review, patient, clinician in db.execute(statement).all():
        access = db.scalar(
            select(PatientReportAccess)
            .where(PatientReportAccess.report_id == report.id)
        )
        reviewed_at = review.reviewed_at or review.updated_at
        report_payload = _report_response_payload(db, report)
        results.append(
            {
                "report": report_payload,
                "patient": {
                    "id": patient.id,
                    "patient_number": patient.patient_number,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": patient.date_of_birth,
                    "sex": patient.sex,
                    "district": patient.district,
                    "country": patient.country,
                    "status": patient.status,
                },
                "clinician": {
                    "id": clinician.id,
                    "full_name": clinician.full_name,
                    "username": clinician.username,
                },
                "review_status": review.review_status,
                "reviewed_at": reviewed_at,
                "released_to_patient": bool(access) or report_payload["released_to_patient"],
                "patient_reviewed_at": access.reviewed_at if access else None,
                "last_viewed_at": access.last_viewed_at if access else None,
            }
        )

    return results


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

    return _report_response_payload(db, report)


@router.delete(
    "/reports/{report_id}",
)
def delete_report(
    report_id: int,
    current_user: User = Depends(require_roles("clinician")),
    db: Session = Depends(get_db),
):
    """Remove a report and its report-specific workflow records.

    Only clinicians can delete reports. The deletion is audited; report,
    clinician-review, and patient-access rows are removed together so a
    deleted report cannot remain visible in the patient portal.
    """
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    latest_review = db.scalar(
        select(ClinicianReview)
        .where(ClinicianReview.report_id == report_id)
        .order_by(ClinicianReview.id.desc())
    )
    access = db.scalar(
        select(PatientReportAccess)
        .where(PatientReportAccess.report_id == report_id)
    )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        entity_type="Report",
        entity_id=report.id,
        description="Clinician deleted a clinical report and its patient-access/review records",
        log_metadata={
            "assessment_id": report.assessment_id,
            "report_status": report.status,
            "review_status": latest_review.review_status if latest_review else None,
            "released_to_patient": bool(access) or str(report.status).lower() in {"approved", "completed"},
        },
    )

    reviews = db.scalars(
        select(ClinicianReview).where(ClinicianReview.report_id == report_id)
    ).all()
    for review in reviews:
        db.delete(review)

    if access is not None:
        db.delete(access)

    db.delete(report)
    db.commit()

    return {"deleted": True, "report_id": report_id}


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

    return _report_response_payload(db, report)

@router.post(
    "/{assessment_id}/reports/{report_id}/release-to-patient",
)
def release_report_to_patient(
    assessment_id: int,
    report_id: int,
    clinical_comment: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("clinician")),
):
    """Approve a report and make it visible in the linked patient's My Health portal."""
    assessment = db.get(AssessmentSession, assessment_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if report.assessment_id != assessment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report does not belong to this assessment",
        )

    report_status = str(report.status).lower()
    if report_status not in {"reviewed", "approved"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review the report before approving and sending it to the patient",
        )

    now = datetime.now(timezone.utc)
    review = db.scalar(
        select(ClinicianReview)
        .where(
            ClinicianReview.assessment_id == assessment_id,
            ClinicianReview.report_id == report_id,
        )
        .order_by(ClinicianReview.id.desc())
    )

    if review is None:
        review = ClinicianReview(
            assessment_id=assessment_id,
            report_id=report_id,
            clinician_id=current_user.id,
            review_status="completed",
            clinical_comment=clinical_comment or "Report approved and released to the patient.",
            modification_notes="Patient-facing report release",
            reviewed_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(review)
    else:
        review.clinician_id = current_user.id
        review.review_status = "completed"
        review.clinical_comment = clinical_comment or review.clinical_comment or "Report approved and released to the patient."
        review.modification_notes = "Patient-facing report release"
        review.reviewed_at = now
        review.updated_at = now

    report.status = "completed"
    report.updated_at = now

    access = db.scalar(
        select(PatientReportAccess)
        .where(PatientReportAccess.report_id == report_id)
    )
    if access is None:
        access = PatientReportAccess(
            patient_id=assessment.patient_id,
            report_id=report_id,
            reviewed_at=None,
            last_viewed_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(access)
    else:
        access.patient_id = assessment.patient_id
        access.updated_at = now

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="release",
        entity_type="Report",
        entity_id=report.id,
        description="Clinician approved and released clinical report to patient portal",
    )

    db.commit()
    db.refresh(review)
    db.refresh(report)
    db.refresh(access)

    return {
        "review": review,
        "report": report,
        "patient_access": {
            "report_id": report.id,
            "patient_id": assessment.patient_id,
            "released_to_patient": True,
            "patient_reviewed_at": access.reviewed_at,
            "last_viewed_at": access.last_viewed_at,
        },
    }
