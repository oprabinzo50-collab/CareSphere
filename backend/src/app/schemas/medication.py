from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MedicationCreate(BaseModel):
    medication_name: str
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "active"
    prescribed_by: str | None = None
    notes: str | None = None


class MedicationUpdate(BaseModel):
    medication_name: str | None = None
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    prescribed_by: str | None = None
    notes: str | None = None


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    medication_name: str
    dose: str | None
    frequency: str | None
    route: str | None
    start_date: date | None
    end_date: date | None
    status: str
    prescribed_by: str | None
    notes: str | None
    recorded_at: datetime
    recorded_by: int | None