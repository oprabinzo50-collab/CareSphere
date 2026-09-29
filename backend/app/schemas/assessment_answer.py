from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AssessmentAnswerCreate(BaseModel):
    question_id: int
    health_concern_id: int | None = None
    answer_text: str | None = None
    answer_number: float | None = None
    answer_boolean: bool | None = None
    answer_json: dict[str, Any] | list[Any] | None = None


class AssessmentAnswerUpdate(BaseModel):
    health_concern_id: int | None = None
    answer_text: str | None = None
    answer_number: float | None = None
    answer_boolean: bool | None = None
    answer_json: dict[str, Any] | list[Any] | None = None


class AssessmentAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    question_id: int
    health_concern_id: int | None
    answer_text: str | None
    answer_number: float | None
    answer_boolean: bool | None
    answer_json: dict[str, Any] | list[Any] | None
    answered_at: datetime
    answered_by: int | None