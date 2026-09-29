from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    sex: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    preferred_language: str | None = None
    residence: str | None = None
    district: str | None = None
    country: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    preferred_language: str | None = None
    residence: str | None = None
    district: str | None = None
    country: str | None = None
    status: str | None = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_number: str
    first_name: str
    last_name: str
    date_of_birth: date | None
    sex: str | None
    marital_status: str | None
    occupation: str | None
    preferred_language: str | None
    residence: str | None
    district: str | None
    country: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: int | None