from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VitalSignCreate(BaseModel):
    height: float | None = None
    weight: float | None = None
    bmi: float | None = None
    blood_pressure_systolic: int | None = None
    blood_pressure_diastolic: int | None = None
    pulse: int | None = None
    temperature: float | None = None
    oxygen_saturation: float | None = None
    assessment_id: int | None = None


class VitalSignUpdate(BaseModel):
    height: float | None = None
    weight: float | None = None
    bmi: float | None = None
    blood_pressure_systolic: int | None = None
    blood_pressure_diastolic: int | None = None
    pulse: int | None = None
    temperature: float | None = None
    oxygen_saturation: float | None = None
    assessment_id: int | None = None


class VitalSignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    height: float | None
    weight: float | None
    bmi: float | None
    blood_pressure_systolic: int | None
    blood_pressure_diastolic: int | None
    pulse: int | None
    temperature: float | None
    oxygen_saturation: float | None
    recorded_at: datetime
    recorded_by: int | None
    assessment_id: int | None