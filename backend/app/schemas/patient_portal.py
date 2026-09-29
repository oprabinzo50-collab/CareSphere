from datetime import date

from pydantic import BaseModel, Field


class PatientSelfProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    sex: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    preferred_language: str | None = None
    residence: str | None = None
    district: str | None = None
    country: str | None = None
