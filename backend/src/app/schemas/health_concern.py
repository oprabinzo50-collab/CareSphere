from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class HealthConcernCreate(BaseModel):
    concern_title: str
    description: str | None = None
    onset_date: date | None = None
    duration_description: str | None = None
    severity: str | None = None
    frequency: str | None = None
    impact_on_daily_life: str | None = None
    patient_priority: str | None = None
    urgent_flag: bool = False
    patient_reported: bool = True
    notes: str | None = None


class HealthConcernUpdate(BaseModel):
    concern_title: str | None = None
    description: str | None = None
    onset_date: date | None = None
    duration_description: str | None = None
    severity: str | None = None
    frequency: str | None = None
    impact_on_daily_life: str | None = None
    patient_priority: str | None = None
    urgent_flag: bool | None = None
    patient_reported: bool | None = None
    notes: str | None = None


class HealthConcernResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    concern_title: str
    description: str | None
    onset_date: date | None
    duration_description: str | None
    severity: str | None
    frequency: str | None
    impact_on_daily_life: str | None
    patient_priority: str | None
    urgent_flag: bool
    patient_reported: bool
    notes: str | None
    created_at: datetime