from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClinicianReviewCreate(BaseModel):
    recommendation_id: int | None = None
    report_id: int | None = None
    clinician_id: int
    review_status: str = "pending"
    clinical_comment: str | None = None
    modification_notes: str | None = None


class ClinicianReviewUpdate(BaseModel):
    review_status: str | None = None
    clinical_comment: str | None = None
    modification_notes: str | None = None


class ClinicianReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    recommendation_id: int | None
    report_id: int | None
    clinician_id: int
    review_status: str
    clinical_comment: str | None
    modification_notes: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime