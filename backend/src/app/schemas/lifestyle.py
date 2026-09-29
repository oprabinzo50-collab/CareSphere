from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LifestyleCreate(BaseModel):
    smoking_status: str | None = None
    alcohol_use: str | None = None
    physical_activity_level: str | None = None
    exercise_frequency: str | None = None
    diet_pattern: str | None = None
    sleep_duration_hours: float | None = None
    sleep_quality: str | None = None
    stress_level: str | None = None
    additional_notes: str | None = None


class LifestyleUpdate(BaseModel):
    smoking_status: str | None = None
    alcohol_use: str | None = None
    physical_activity_level: str | None = None
    exercise_frequency: str | None = None
    diet_pattern: str | None = None
    sleep_duration_hours: float | None = None
    sleep_quality: str | None = None
    stress_level: str | None = None
    additional_notes: str | None = None


class LifestyleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    smoking_status: str | None
    alcohol_use: str | None
    physical_activity_level: str | None
    exercise_frequency: str | None
    diet_pattern: str | None
    sleep_duration_hours: float | None
    sleep_quality: str | None
    stress_level: str | None
    additional_notes: str | None
    recorded_at: datetime
    recorded_by: int | None