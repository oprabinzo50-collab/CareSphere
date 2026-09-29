from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    report_type: str
    report_title: str
    report_content: str
    executive_summary: str | None = None
    recommendations_summary: str | None = None
    limitations: str | None = None
    generated_by: str | None = None
    ai_generated: bool = False
    version: int = 1
    status: str = "draft"


class ReportUpdate(BaseModel):
    report_type: str | None = None
    report_title: str | None = None
    report_content: str | None = None
    executive_summary: str | None = None
    recommendations_summary: str | None = None
    limitations: str | None = None
    generated_by: str | None = None
    ai_generated: bool | None = None
    version: int | None = None
    status: str | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    report_type: str
    report_title: str
    report_content: str
    executive_summary: str | None
    recommendations_summary: str | None
    limitations: str | None
    generated_by: str | None
    ai_generated: bool
    version: int
    status: str
    generated_at: datetime
    created_by: int | None
    updated_at: datetime
    clinician_id: int | None = None
    clinician_guidance: str | None = None
    clinician_review_status: str | None = None
    clinician_reviewed_at: datetime | None = None
    released_to_patient: bool = False
    patient_reviewed_at: datetime | None = None
    last_viewed_at: datetime | None = None


class ReviewedReportPatient(BaseModel):
    id: int
    patient_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    sex: str | None = None
    district: str | None = None
    country: str | None = None
    status: str | None = None


class ReviewedReportClinician(BaseModel):
    id: int
    full_name: str
    username: str


class ReviewedReportResponse(BaseModel):
    report: ReportResponse
    patient: ReviewedReportPatient
    clinician: ReviewedReportClinician
    review_status: str
    reviewed_at: datetime
    released_to_patient: bool = False
    patient_reviewed_at: datetime | None = None
    last_viewed_at: datetime | None = None
