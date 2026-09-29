from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationCreate(BaseModel):
    health_concern_id: int | None = None
    recommendation_type: str
    title: str
    recommendation_text: str
    rationale: str | None = None
    priority: str | None = None
    source_type: str | None = None
    ai_generated: bool = False
    clinician_review_required: bool = True
    status: str = "draft"


class RecommendationUpdate(BaseModel):
    health_concern_id: int | None = None
    recommendation_type: str | None = None
    title: str | None = None
    recommendation_text: str | None = None
    rationale: str | None = None
    priority: str | None = None
    source_type: str | None = None
    ai_generated: bool | None = None
    clinician_review_required: bool | None = None
    status: str | None = None


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    health_concern_id: int | None
    recommendation_type: str
    title: str
    recommendation_text: str
    rationale: str | None
    priority: str | None
    source_type: str | None
    ai_generated: bool
    clinician_review_required: bool
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: int | None