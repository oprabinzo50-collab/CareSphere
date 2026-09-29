from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    description: str | None
    ip_address: str | None
    user_agent: str | None
    log_metadata: dict | None
    created_at: datetime