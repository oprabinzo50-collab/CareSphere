from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.roles import (
    ROLE_ADMINISTRATOR,
    ROLE_CLINICIAN,
    ROLE_PATIENT,
    normalize_role,
)


# Central permission catalogue. Route-level role checks remain intentionally
# simple for now, while this map gives the application one canonical place
# to derive UI capabilities and future fine-grained API authorization.
ALL_PERMISSIONS = {
    "dashboard.view",
    "patients.view",
    "patients.create",
    "patients.update",
    "patients.deactivate",
    "clinical.view",
    "clinical.update",
    "assessments.view",
    "assessments.create",
    "assessments.update",
    "recommendations.view",
    "recommendations.create",
    "reports.view",
    "reports.create",
    "clinician_reviews.view",
    "clinician_reviews.manage",
    "care_team.view",
    "care_team.manage",
    "notifications.view",
    "ai.use",
    "users.view",
    "users.manage",
    "audit_logs.view",
    "system.manage",
    "patient_portal.view",
    "patient.self_view",
    "patient.self_update",
    "patient.self_submit",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_ADMINISTRATOR: set(ALL_PERMISSIONS),
    ROLE_CLINICIAN: {
        "dashboard.view",
        "patients.view",
        "patients.create",
        "patients.update",
        "patients.deactivate",
        "clinical.view",
        "clinical.update",
        "assessments.view",
        "assessments.create",
        "assessments.update",
        "recommendations.view",
        "recommendations.create",
        "reports.view",
        "reports.create",
        "clinician_reviews.view",
        "clinician_reviews.manage",
        "care_team.view",
        "care_team.manage",
        "notifications.view",
        "ai.use",
    },
    ROLE_PATIENT: {
        "patient_portal.view",
        "patient.self_view",
        "patient.self_update",
        "patient.self_submit",
    "patient.self_update",
    "patient.self_submit",
    },
}


def permissions_for_role(role: str | None) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(normalize_role(role), set()))


def require_roles(*allowed_roles: str) -> Callable:
    allowed = {normalize_role(role) for role in allowed_roles}

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if normalize_role(current_user.role) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user

    return role_checker


def require_permission(permission: str) -> Callable:
    def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        allowed = ROLE_PERMISSIONS.get(
            normalize_role(current_user.role),
            set(),
        )
        if permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user

    return permission_checker
