from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AssessmentQuestionCreate(BaseModel):
    question_code: str
    question_text: str
    category: str | None = None
    question_type: str
    options: dict[str, Any] | list[Any] | None = None
    is_required: bool = False
    display_order: int = 0
    active: bool = True


class AssessmentQuestionUpdate(BaseModel):
    question_text: str | None = None
    category: str | None = None
    question_type: str | None = None
    options: dict[str, Any] | list[Any] | None = None
    is_required: bool | None = None
    display_order: int | None = None
    active: bool | None = None


class AssessmentQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_code: str
    question_text: str
    category: str | None
    question_type: str
    options: dict[str, Any] | list[Any] | None
    is_required: bool
    display_order: int
    active: bool
    created_at: datetime
    updated_at: datetime