from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.allergies import Allergy
from app.models.assessment_sessions import AssessmentSession
from app.models.clinician_reviews import ClinicianReview
from app.models.lifestyle import Lifestyle
from app.models.medical_history import MedicalHistory
from app.models.medications import Medication
from app.models.patient import Patient
from app.models.patient_contacts import PatientContact
from app.models.patient_user_links import PatientUserLink
from app.models.patient_report_access import PatientReportAccess
from app.models.recommendations import Recommendation
from app.models.reports import Report
from app.models.user import User
from app.models.vital_signs import VitalSign
from app.schemas.allergy import AllergyCreate, AllergyResponse
from app.schemas.lifestyle import LifestyleCreate, LifestyleResponse
from app.schemas.medical_history import MedicalHistoryCreate, MedicalHistoryResponse
from app.schemas.medication import MedicationCreate, MedicationResponse
from app.schemas.patient import PatientResponse
from app.schemas.patient_portal import PatientSelfProfileUpdate
from app.schemas.patient_contact import PatientContactCreate, PatientContactResponse, PatientContactUpdate
from app.schemas.vital_sign import VitalSignCreate, VitalSignResponse
from app.security.permissions import require_roles
from app.utils.audit import create_audit_log


router = APIRouter(prefix="/patient/me", tags=["Patient Portal"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_linked_patient(current_user: User, db: Session) -> Patient:
    link = db.scalar(
        select(PatientUserLink).where(PatientUserLink.user_id == current_user.id)
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No patient record is linked to this account",
        )

    patient = db.get(Patient, link.patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked patient record was not found",
        )
    return patient


@router.put("/profile", response_model=PatientResponse)
def update_my_profile(
    payload: PatientSelfProfileUpdate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    patient.updated_at = datetime.now(timezone.utc)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="update",
        entity_type="Patient",
        entity_id=patient.id,
        description="Patient self-service profile updated",
    )
    db.commit()
    db.refresh(patient)
    return patient


@router.post("/contacts", response_model=PatientContactResponse, status_code=status.HTTP_201_CREATED)
def add_my_contact(
    payload: PatientContactCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    now = datetime.now(timezone.utc)
    record = PatientContact(patient_id=patient.id, **payload.model_dump(), created_at=now, updated_at=now)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/contacts/{contact_id}", response_model=PatientContactResponse)
def update_my_contact(
    contact_id: int,
    payload: PatientContactUpdate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    record = db.get(PatientContact, contact_id)
    if record is None or record.patient_id != patient.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


@router.post("/medical-history", response_model=MedicalHistoryResponse, status_code=status.HTTP_201_CREATED)
def add_my_medical_history(
    payload: MedicalHistoryCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    record = MedicalHistory(
        patient_id=patient.id,
        **payload.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/allergies", response_model=AllergyResponse, status_code=status.HTTP_201_CREATED)
def add_my_allergy(
    payload: AllergyCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    record = Allergy(
        patient_id=patient.id,
        **payload.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/medications", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def add_my_medication(
    payload: MedicationCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    record = Medication(
        patient_id=patient.id,
        **payload.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/lifestyle", response_model=LifestyleResponse, status_code=status.HTTP_201_CREATED)
def add_my_lifestyle(
    payload: LifestyleCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    record = Lifestyle(
        patient_id=patient.id,
        **payload.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/vital-signs", response_model=VitalSignResponse, status_code=status.HTTP_201_CREATED)
def add_my_vital_signs(
    payload: VitalSignCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    if payload.assessment_id is not None:
        assessment = db.get(AssessmentSession, payload.assessment_id)
        if assessment is None or assessment.patient_id != patient.id:
            raise HTTPException(status_code=400, detail="Assessment does not belong to your patient record")
    record = VitalSign(
        patient_id=patient.id,
        **payload.model_dump(),
        recorded_at=datetime.now(timezone.utc),
        recorded_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/reports/{report_id}/reviewed")
def mark_my_report_reviewed(
    report_id: int,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    assessment = db.get(AssessmentSession, report.assessment_id)
    if assessment is None or assessment.patient_id != patient.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This report is not part of your patient record")

    if str(report.status).lower() not in {"approved", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This report is not yet released for patient access")

    now = datetime.now(timezone.utc)
    access = db.scalar(select(PatientReportAccess).where(PatientReportAccess.report_id == report_id))
    if access is None:
        access = PatientReportAccess(
            patient_id=patient.id,
            report_id=report_id,
            reviewed_at=now,
            last_viewed_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(access)
    else:
        access.patient_id = patient.id
        access.reviewed_at = access.reviewed_at or now
        access.last_viewed_at = now
        access.updated_at = now

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="review",
        entity_type="Report",
        entity_id=report.id,
        description="Patient marked released clinical report as reviewed",
    )
    db.commit()
    db.refresh(access)
    return {"report_id": report.id, "reviewed_at": access.reviewed_at}


@router.get("/care-summary")
def get_my_care_summary(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_linked_patient(current_user, db)

    approved_review_exists = exists(
        select(ClinicianReview.id).where(
            ClinicianReview.recommendation_id == Recommendation.id,
            ClinicianReview.review_status.in_(["approved", "completed"]),
        )
    )

    recommendation_rows = db.scalars(
        select(Recommendation)
        .join(AssessmentSession, Recommendation.assessment_id == AssessmentSession.id)
        .where(
            AssessmentSession.patient_id == patient.id,
            or_(Recommendation.status == "approved", approved_review_exists),
        )
        .order_by(Recommendation.id.desc())
    ).all()

    report_rows = db.scalars(
        select(Report)
        .join(AssessmentSession, Report.assessment_id == AssessmentSession.id)
        .where(
            AssessmentSession.patient_id == patient.id,
            Report.status.in_(["approved", "completed"]),
        )
        .order_by(Report.id.desc())
    ).all()

    report_ids = [row.id for row in report_rows]
    review_map = {}
    if report_ids:
        reviews = db.scalars(
            select(ClinicianReview)
            .where(ClinicianReview.report_id.in_(report_ids))
            .order_by(ClinicianReview.id.desc())
        ).all()
        for review in reviews:
            review_map.setdefault(review.report_id, review)

    access_map = {}
    if report_ids:
        accesses = db.scalars(
            select(PatientReportAccess)
            .where(
                PatientReportAccess.patient_id == patient.id,
                PatientReportAccess.report_id.in_(report_ids),
            )
        ).all()
        access_map = {item.report_id: item for item in accesses}

    return {
        "recommendations": jsonable_encoder([
            {
                "id": row.id,
                "title": row.title,
                "recommendation_text": row.recommendation_text,
                "priority": row.priority,
                "source_type": row.source_type,
                "ai_generated": row.ai_generated,
                "status": row.status,
                "updated_at": row.updated_at,
            }
            for row in recommendation_rows
        ]),
        "reports": jsonable_encoder([
            {
                "id": row.id,
                "assessment_id": row.assessment_id,
                "report_type": row.report_type,
                "report_title": row.report_title,
                "report_content": row.report_content,
                "executive_summary": row.executive_summary,
                "recommendations_summary": row.recommendations_summary,
                "limitations": row.limitations,
                "generated_by": row.generated_by,
                "ai_generated": row.ai_generated,
                "version": row.version,
                "status": row.status,
                "generated_at": row.generated_at,
                "clinician_id": review_map[row.id].clinician_id if row.id in review_map else None,
                "clinician_guidance": review_map[row.id].clinical_comment if row.id in review_map else None,
                "clinician_review_status": review_map[row.id].review_status if row.id in review_map else None,
                "patient_reviewed_at": access_map[row.id].reviewed_at if row.id in access_map else None,
            }
            for row in report_rows
        ]),
    }
