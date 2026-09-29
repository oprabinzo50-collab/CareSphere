from __future__ import annotations


ROLE_ADMINISTRATOR = "administrator"
ROLE_CLINICIAN = "clinician"
ROLE_PATIENT = "patient"

SUPPORTED_ROLES = {
    ROLE_ADMINISTRATOR,
    ROLE_CLINICIAN,
    ROLE_PATIENT,
}

ROLE_ALIASES = {
    "admin": ROLE_ADMINISTRATOR,
    "administrator": ROLE_ADMINISTRATOR,
    "clinician": ROLE_CLINICIAN,
    "doctor": ROLE_CLINICIAN,
    "medical_officer": ROLE_CLINICIAN,
    "nurse": ROLE_CLINICIAN,
    "patient": ROLE_PATIENT,
    "patient_user": ROLE_PATIENT,
}


def normalize_role(role: str | None) -> str:
    value = (role or "").strip().lower()
    return ROLE_ALIASES.get(value, value)


def role_matches(user_role: str | None, allowed_roles: set[str]) -> bool:
    return normalize_role(user_role) in {normalize_role(r) for r in allowed_roles}
