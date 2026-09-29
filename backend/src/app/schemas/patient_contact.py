from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PatientContactCreate(BaseModel):
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    next_of_kin: str | None = None
    next_of_kin_phone: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    relationship: str | None = None


class PatientContactUpdate(BaseModel):
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    next_of_kin: str | None = None
    next_of_kin_phone: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    relationship: str | None = None


class PatientContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    phone: str | None
    email: str | None
    address: str | None
    next_of_kin: str | None
    next_of_kin_phone: str | None
    emergency_contact: str | None
    emergency_phone: str | None
    relationship: str | None
    created_at: datetime
    updated_at: datetime