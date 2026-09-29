from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AllergyCreate(BaseModel):
    allergen: str
    reaction: str | None = None
    severity: str | None = None
    notes: str | None = None


class AllergyUpdate(BaseModel):
    allergen: str | None = None
    reaction: str | None = None
    severity: str | None = None
    notes: str | None = None


class AllergyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    allergen: str
    reaction: str | None
    severity: str | None
    notes: str | None
    recorded_at: datetime
    recorded_by: int | None