from typing import Any

from pydantic import BaseModel


class AssessmentDetailResponse(BaseModel):
    assessment: dict[str, Any]
    answers: list[dict[str, Any]]
    health_concerns: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    reports: list[dict[str, Any]]
    clinician_reviews: list[dict[str, Any]]
    vital_signs: list[dict[str, Any]]