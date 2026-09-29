from typing import Any

from pydantic import BaseModel


class PatientProfileResponse(BaseModel):
    patient: dict[str, Any]
    contacts: list[dict[str, Any]]
    medical_history: list[dict[str, Any]]
    allergies: list[dict[str, Any]]
    medications: list[dict[str, Any]]
    lifestyle: list[dict[str, Any]]
    vital_signs: list[dict[str, Any]]
    assessments: list[dict[str, Any]]