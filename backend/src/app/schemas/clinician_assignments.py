from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClinicianAssignmentCreate(BaseModel):
    clinician_id: int
    care_role: str = Field(
        default="primary",
        min_length=1,
        max_length=30,
    )


class ClinicianAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    clinician_id: int
    assigned_by: int | None
    care_role: str
    status: str
    assigned_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ClinicianAssignmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    clinician_id: int
    care_role: str
    status: str
    assigned_at: datetime
    ended_at: datetime | None