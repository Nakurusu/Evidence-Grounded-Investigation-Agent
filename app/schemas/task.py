from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from pydantic import ConfigDict
from app.models.enums import TaskStatus

class TaskResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: UUID
    status: TaskStatus
    filename: str
    created_at: datetime
    finished_at: datetime | None
    result: dict | None
    error: str | None