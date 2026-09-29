from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    report_type: str
    report_title: str
    report_content: str
    executive_summary: str | None = None
    recommendations_summary: str | None = None
    limitations: str | None = None
    generated_by: str | None = None
    ai_generated: bool = False
    version: int = 1
    status: str = "draft"


class ReportUpdate(BaseModel):
    report_type: str | None = None
    report_title: str | None = None
    report_content: str | None = None
    executive_summary: str | None = None
    recommendations_summary: str | None = None
    limitations: str | None = None
    generated_by: str | None = None
    ai_generated: bool | None = None
    version: int | None = None
    status: str | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    report_type: str
    report_title: str
    report_content: str
    executive_summary: str | None
    recommendations_summary: str | None
    limitations: str | None
    generated_by: str | None
    ai_generated: bool
    version: int
    status: str
    generated_at: datetime
    created_by: int | None
    updated_at: datetime