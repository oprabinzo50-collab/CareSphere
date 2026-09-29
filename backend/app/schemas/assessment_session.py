from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssessmentSessionCreate(BaseModel):
    assessment_type: str
    status: str = "in_progress"
    summary: str | None = None
    notes: str | None = None


class AssessmentSessionUpdate(BaseModel):
    assessment_type: str | None = None
    status: str | None = None
    summary: str | None = None
    notes: str | None = None


class AssessmentSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    assessment_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    assessed_by: int | None
    summary: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime