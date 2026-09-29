from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MedicalHistoryCreate(BaseModel):
    condition_name: str
    description: str | None = None
    diagnosed_date: date | None = None
    status: str = "active"
    notes: str | None = None


class MedicalHistoryUpdate(BaseModel):
    condition_name: str | None = None
    description: str | None = None
    diagnosed_date: date | None = None
    status: str | None = None
    notes: str | None = None


class MedicalHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    condition_name: str
    description: str | None
    diagnosed_date: date | None
    status: str
    notes: str | None
    recorded_at: datetime
    recorded_by: int | None